from fastapi import FastAPI, HTTPException, status, File, UploadFile, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import csv
from io import StringIO

import models
import schemas
from schemas import EventCreate, EventUpdate, AttendeeCreate, AttendeeResponse, EventResponse, Token
from database import SessionLocal, engine
from auth import (
    get_current_active_user,
    authenticate_user,
    create_access_token,
    oauth2_scheme,
    fake_hash_password
)
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility function to update all event statuses if end_time has passed
def update_all_events_status(db: Session):
    now = datetime.utcnow()
    events_to_update = db.query(models.Event).filter(models.Event.end_time < now, models.Event.status != "completed").all()
    for event in events_to_update:
        event.status = "completed"
    if events_to_update:
        db.commit()

# Token endpoint for user login
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    from auth import fake_users_db
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Create an event
@app.post("/events/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    valid_statuses = {"scheduled", "ongoing", "completed", "canceled"}
    if event.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid event status")

    new_event = models.Event(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# Update an event
@app.put("/events/{event_id}/", response_model=EventResponse)
def update_event(event_id: int, event: EventUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    db_event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    for key, value in event.dict(exclude_unset=True).items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event

# List all events with filters
@app.get("/events/", response_model=list[EventResponse])
def list_events(status: str = None, location: str = None, date: str = None, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    # Update event statuses before fetching
    update_all_events_status(db)
    
    query = db.query(models.Event)
    if status:
        query = query.filter(models.Event.status == status)
    if location:
        query = query.filter(models.Event.location == location)
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(models.Event.start_time >= date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    return query.all()

# Register an attendee
@app.post("/attendees/", response_model=AttendeeResponse, status_code=status.HTTP_201_CREATED)
def register_attendee(attendee: AttendeeCreate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    # Update event statuses in case the event has ended
    update_all_events_status(db)
    
    event = db.query(models.Event).filter(models.Event.event_id == attendee.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    total_attendees = db.query(models.Attendee).filter(models.Attendee.event_id == attendee.event_id).count()
    if total_attendees >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Event is full")

    new_attendee = models.Attendee(**attendee.dict())
    db.add(new_attendee)
    db.commit()
    db.refresh(new_attendee)
    return new_attendee

# List attendees for an event
@app.get("/events/{event_id}/attendees/", response_model=list[AttendeeResponse])
def list_attendees(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    attendees = db.query(models.Attendee).filter(models.Attendee.event_id == event_id).all()
    return attendees

# Check-in an attendee
@app.put("/attendees/{attendee_id}/checkin/")
def checkin_attendee(attendee_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    attendee = db.query(models.Attendee).filter(models.Attendee.attendee_id == attendee_id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    if attendee.check_in_status:
        raise HTTPException(status_code=400, detail="Attendee already checked in")    
    attendee.check_in_status = True
    db.commit()
    return {"message": "Check-in successful"}

# Bulk check-in via CSV upload
@app.post("/events/{event_id}/bulk-checkin/")
async def bulk_checkin(event_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    contents = await file.read()
    file_data = StringIO(contents.decode("utf-8"))
    reader = csv.reader(file_data)
    next(reader)  # Skip header

    checkin_count = 0
    for row in reader:
        try:
            attendee_id = int(row[0])  # Assume CSV contains attendee_id in the first column
        except (IndexError, ValueError):
            continue

        attendee = db.query(models.Attendee).filter(
            models.Attendee.attendee_id == attendee_id,
            models.Attendee.event_id == event_id
        ).first()
        if attendee:
            attendee.check_in_status = True
            checkin_count += 1

    db.commit()
    return {"message": f"{checkin_count} attendees checked in"}

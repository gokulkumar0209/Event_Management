import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

import models
from database import Base, engine, SessionLocal
from main import app

client = TestClient(app)

# Helper function to obtain an access token
def get_token():
    response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token

@pytest.fixture(autouse=True)
def setup_db():
    # Recreate the database for testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Create a test event that is active
    test_event = models.Event(
        name="Test Event",
        description="Test Description",
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow() + timedelta(hours=1),
        location="Test Location",
        max_attendees=2,
        status="scheduled"
    )
    db.add(test_event)
    db.commit()
    db.refresh(test_event)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

# Test registration limit
def test_registration_limit():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    db = SessionLocal()
    event = db.query(models.Event).first()
    db.close()
    
    response = client.post("/attendees/", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "phone_number": "1234567890",
        "event_id": event.event_id
    }, headers=headers)
    assert response.status_code == 201
    
    response = client.post("/attendees/", json={
        "first_name": "Bob",
        "last_name": "Brown",
        "email": "bob@example.com",
        "phone_number": "0987654321",
        "event_id": event.event_id
    }, headers=headers)
    assert response.status_code == 201
    
    response = client.post("/attendees/", json={
        "first_name": "Charlie",
        "last_name": "Davis",
        "email": "charlie@example.com",
        "phone_number": "1112223333",
        "event_id": event.event_id
    }, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Event is full"

# Test attendee check-in
def test_checkin_attendee():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    db = SessionLocal()
    event = db.query(models.Event).first()
    db.close()
    
    response = client.post("/attendees/", json={
        "first_name": "Dana",
        "last_name": "Evans",
        "email": "dana@example.com",
        "phone_number": "4445556666",
        "event_id": event.event_id
    }, headers=headers)
    assert response.status_code == 201
    attendee_id = response.json()["attendee_id"]
    
    response = client.put(f"/attendees/{attendee_id}/checkin/", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Check-in successful"

# Additional tests

def test_invalid_registration():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/attendees/", json={}, headers=headers)
    assert response.status_code == 422  # Unprocessable Entity due to missing fields

def test_unauthorized_access():
    response = client.post("/attendees/", json={
        "first_name": "Unauthorized",
        "last_name": "User",
        "email": "unauth@example.com",
        "phone_number": "0001112222",
        "event_id": 1
    })
    assert response.status_code == 401  # Unauthorized

def test_duplicate_checkin():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    db = SessionLocal()
    event = db.query(models.Event).first()
    db.close()
    
    response = client.post("/attendees/", json={
        "first_name": "Frank",
        "last_name": "Miller",
        "email": "frank@example.com",
        "phone_number": "5556667777",
        "event_id": event.event_id
    }, headers=headers)
    assert response.status_code == 201
    attendee_id = response.json()["attendee_id"]
    
    response = client.put(f"/attendees/{attendee_id}/checkin/", headers=headers)
    assert response.status_code == 200
    
    response = client.put(f"/attendees/{attendee_id}/checkin/", headers=headers)
    assert response.status_code == 400  # Should fail as already checked in

def test_checkin_nonexistent_attendee():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.put("/attendees/999/checkin/", headers=headers)
    assert response.status_code == 404  # Non-existent attendee

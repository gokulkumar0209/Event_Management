from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

# Enum for Event Status
class EventStatus(str, Enum):
    scheduled = "scheduled"
    ongoing = "ongoing"
    completed = "completed"
    canceled = "canceled"

# Schema for Creating an Event
class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: str
    max_attendees: int
    status: Optional[EventStatus] = EventStatus.scheduled

# Schema for Updating an Event
class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None
    status: Optional[EventStatus] = None

# Schema for Response - Event
class EventResponse(BaseModel):
    event_id: int
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: str
    max_attendees: int
    status: EventStatus

    class Config:
        orm_mode = True

# Schema for Creating an Attendee
class AttendeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    event_id: int

# Schema for Response - Attendee
class AttendeeResponse(AttendeeCreate):
    attendee_id: int
    check_in_status: bool

    class Config:
        orm_mode = True

# Schemas for JWT Authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from database import Base

class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    max_attendees = Column(Integer, nullable=False)
    status = Column(Enum("scheduled", "ongoing", "completed", "canceled", name="event_status"), default="scheduled")
    
    attendees = relationship("Attendee", back_populates="event")

class Attendee(Base):
    __tablename__ = "attendees"
    
    attendee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey("events.event_id"))
    check_in_status = Column(Boolean, default=False)
    
    event = relationship("Event", back_populates="attendees")

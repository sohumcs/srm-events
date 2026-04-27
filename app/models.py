from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(300))
    capacity = Column(Integer, default=100)
    facilities = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    events = relationship("Event", back_populates="venue")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    date = Column(String(50), nullable=False)
    time = Column(String(50))
    venue_id = Column(Integer, ForeignKey("venues.id"))
    capacity = Column(Integer, default=100)
    registered_count = Column(Integer, default=0)
    organizer = Column(String(200))
    status = Column(String(50), default="upcoming")
    created_at = Column(DateTime, default=datetime.utcnow)
    venue = relationship("Venue", back_populates="events")
    registrations = relationship("Registration", back_populates="event")

    __table_args__ = (
        Index("ix_event_category_status", "category", "status"),
        Index("ix_event_date", "date"),
    )

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    student_name = Column(String(200), nullable=False)
    student_email = Column(String(200), nullable=False, index=True)
    student_reg_no = Column(String(50))
    department = Column(String(100))
    year = Column(Integer)
    registered_at = Column(DateTime, default=datetime.utcnow)
    event = relationship("Event", back_populates="registrations")

    __table_args__ = (
        Index("ix_registration_event_email", "event_id", "student_email"),
    )

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

class VenueCreate(BaseModel):
    name: str
    location: str
    capacity: int
    facilities: Optional[str] = ""

    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Venue name cannot be empty")
        return v.strip()

class VenueOut(VenueCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: str
    date: str
    time: Optional[str] = ""
    venue_id: Optional[int] = None
    capacity: int
    organizer: Optional[str] = ""
    status: Optional[str] = "upcoming"

    @validator("title")
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Event title cannot be empty")
        if len(v) > 300:
            raise ValueError("Title too long")
        return v.strip()

    @validator("capacity")
    def capacity_positive(cls, v):
        if v <= 0:
            raise ValueError("Capacity must be positive")
        if v > 50000:
            raise ValueError("Capacity unrealistically large")
        return v

    @validator("category")
    def valid_category(cls, v):
        valid = ["Technical", "Cultural", "Sports", "Workshop", "Seminar", "Other"]
        if v not in valid:
            raise ValueError(f"Category must be one of: {valid}")
        return v

class EventOut(EventCreate):
    id: int
    registered_count: int
    created_at: datetime
    class Config:
        from_attributes = True

class RegistrationCreate(BaseModel):
    event_id: int
    student_name: str
    student_email: str
    student_reg_no: Optional[str] = ""
    department: Optional[str] = ""
    year: Optional[int] = None

    @validator("student_name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Student name cannot be empty")
        return v.strip()

    @validator("student_email")
    def valid_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @validator("student_reg_no")
    def valid_reg_no(cls, v):
        if v and not re.match(r'^[A-Za-z0-9]+$', v):
            raise ValueError("Registration number must be alphanumeric")
        return v

class RegistrationOut(RegistrationCreate):
    id: int
    registered_at: datetime
    class Config:
        from_attributes = True

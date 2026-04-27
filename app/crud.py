from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from datetime import datetime

def get_events(db: Session, skip=0, limit=100, category=None):
    q = db.query(models.Event)
    if category:
        q = q.filter(models.Event.category == category)
    return q.offset(skip).limit(limit).all()

def get_event(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.id == event_id).first()

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_event(db: Session, event_id: int, event: schemas.EventCreate):
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    for key, value in event.dict().items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int):
    db_event = get_event(db, event_id)
    if not db_event:
        return False
    db.delete(db_event)
    db.commit()
    return True

def get_venues(db: Session):
    return db.query(models.Venue).all()

def create_venue(db: Session, venue: schemas.VenueCreate):
    db_venue = models.Venue(**venue.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue

def get_registrations(db: Session):
    return db.query(models.Registration).all()

def get_registrations_by_event(db: Session, event_id: int):
    return db.query(models.Registration).filter(models.Registration.event_id == event_id).all()

def check_duplicate_registration(db: Session, event_id: int, email: str):
    return db.query(models.Registration).filter(
        models.Registration.event_id == event_id,
        models.Registration.student_email == email.lower()
    ).first() is not None

def create_registration(db: Session, reg: schemas.RegistrationCreate):
    db_reg = models.Registration(**reg.dict())
    db.add(db_reg)
    # Increment event registered_count
    event = get_event(db, reg.event_id)
    if event:
        event.registered_count += 1
    db.commit()
    db.refresh(db_reg)
    return db_reg

def get_dashboard_stats(db: Session):
    total_events = db.query(func.count(models.Event.id)).scalar()
    total_registrations = db.query(func.count(models.Registration.id)).scalar()
    total_venues = db.query(func.count(models.Venue.id)).scalar()
    upcoming = db.query(func.count(models.Event.id)).filter(models.Event.status == "upcoming").scalar()

    by_category = db.query(
        models.Event.category,
        func.count(models.Event.id).label("count")
    ).group_by(models.Event.category).all()

    top_events = db.query(
        models.Event.title,
        models.Event.registered_count,
        models.Event.capacity
    ).order_by(models.Event.registered_count.desc()).limit(5).all()

    return {
        "total_events": total_events,
        "total_registrations": total_registrations,
        "total_venues": total_venues,
        "upcoming_events": upcoming,
        "events_by_category": [{"category": r[0], "count": r[1]} for r in by_category],
        "top_events": [{"title": r[0], "registered": r[1], "capacity": r[2]} for r in top_events]
    }

def seed_sample_data(db: Session):
    venues = [
        models.Venue(name="Tech Park Auditorium", location="Main Campus Block A", capacity=500, facilities="Projector, AC, WiFi, Stage"),
        models.Venue(name="Open Air Theatre", location="Central Lawn", capacity=2000, facilities="Sound System, Lighting, Stage"),
        models.Venue(name="Seminar Hall 101", location="Academic Block", capacity=150, facilities="Smartboard, AC, WiFi"),
        models.Venue(name="Sports Complex", location="Sports Block", capacity=1000, facilities="Courts, Changing Rooms, Scoreboard"),
    ]
    db.add_all(venues)
    db.commit()

    events = [
        models.Event(title="SRM Hackathon 2025", description="24-hour coding marathon for all tech enthusiasts. Build innovative solutions!", category="Technical", date="2025-03-15", time="09:00 AM", venue_id=1, capacity=300, registered_count=245, organizer="CSE Department", status="upcoming"),
        models.Event(title="Aaruush Tech Fest", description="Annual national-level technical symposium with workshops and competitions.", category="Technical", date="2025-04-10", time="10:00 AM", venue_id=2, capacity=1500, registered_count=1100, organizer="Student Council", status="upcoming"),
        models.Event(title="Culturals Night 2025", description="Showcase your talent in dance, music, drama and more!", category="Cultural", date="2025-03-28", time="06:00 PM", venue_id=2, capacity=2000, registered_count=1800, organizer="Cultural Committee", status="upcoming"),
        models.Event(title="Cloud Computing Workshop", description="Hands-on AWS/Azure workshop for final year students.", category="Workshop", date="2025-03-20", time="10:00 AM", venue_id=3, capacity=100, registered_count=98, organizer="CSE Dept", status="upcoming"),
        models.Event(title="Inter-Department Cricket", description="Annual cricket tournament between all departments.", category="Sports", date="2025-04-05", time="08:00 AM", venue_id=4, capacity=500, registered_count=320, organizer="Sports Committee", status="upcoming"),
        models.Event(title="AI/ML Seminar", description="Industry experts talk on latest trends in Artificial Intelligence.", category="Seminar", date="2025-03-25", time="02:00 PM", venue_id=3, capacity=150, registered_count=140, organizer="AI Club", status="upcoming"),
        models.Event(title="Robotics Workshop", description="Build and program robots using Arduino and Raspberry Pi.", category="Workshop", date="2025-03-22", time="09:30 AM", venue_id=1, capacity=60, registered_count=60, organizer="Robotics Club", status="upcoming"),
        models.Event(title="Kalotsav Cultural Fest", description="Celebrate art, culture and heritage of India.", category="Cultural", date="2025-04-20", time="04:00 PM", venue_id=2, capacity=3000, registered_count=2100, organizer="Cultural Committee", status="upcoming"),
    ]
    db.add_all(events)
    db.commit()

    registrations = [
        models.Registration(event_id=1, student_name="Rahul Sharma", student_email="rahul@srmist.edu.in", student_reg_no="RA2111003010001", department="CSE", year=3),
        models.Registration(event_id=1, student_name="Priya Singh", student_email="priya@srmist.edu.in", student_reg_no="RA2111003010002", department="ECE", year=2),
        models.Registration(event_id=2, student_name="Arjun Kumar", student_email="arjun@srmist.edu.in", student_reg_no="RA2111003010003", department="MECH", year=4),
        models.Registration(event_id=3, student_name="Divya Nair", student_email="divya@srmist.edu.in", student_reg_no="RA2111003010004", department="IT", year=2),
        models.Registration(event_id=4, student_name="Vikram Patel", student_email="vikram@srmist.edu.in", student_reg_no="RA2111003010005", department="CSE", year=3),
    ]
    db.add_all(registrations)
    db.commit()

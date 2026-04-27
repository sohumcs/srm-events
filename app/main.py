from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import os
from datetime import datetime

from app.database import SessionLocal, engine, Base
from app import models, schemas, crud
from app.metrics import metrics_store

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SRM Event Management System",
    description="Cloud-native college event management platform for SRM Institute of Technology",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request timing middleware for monitoring
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    metrics_store.record_request(request.url.path, response.status_code, duration)
    return response

# Seed data on startup
@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        if db.query(models.Event).count() == 0:
            crud.seed_sample_data(db)
    finally:
        db.close()

# ─── ROOT ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=FileResponse)
def root():
    return FileResponse(os.path.join(static_path, "index.html"))

# ─── HEALTH ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "service": "srm-events"}

# ─── EVENTS ──────────────────────────────────────────────────────────────────
@app.get("/api/events", response_model=List[schemas.EventOut])
def list_events(skip: int = 0, limit: int = 100, category: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_events(db, skip=skip, limit=limit, category=category)

@app.get("/api/events/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.post("/api/events", response_model=schemas.EventOut, status_code=201)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, event)

@app.put("/api/events/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, event: schemas.EventCreate, db: Session = Depends(get_db)):
    updated = crud.update_event(db, event_id, event)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    if not crud.delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

# ─── REGISTRATIONS ───────────────────────────────────────────────────────────
@app.get("/api/registrations", response_model=List[schemas.RegistrationOut])
def list_registrations(db: Session = Depends(get_db)):
    return crud.get_registrations(db)

@app.post("/api/registrations", response_model=schemas.RegistrationOut, status_code=201)
def register(reg: schemas.RegistrationCreate, db: Session = Depends(get_db)):
    # Check event exists and has capacity
    event = crud.get_event(db, reg.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.registered_count >= event.capacity:
        raise HTTPException(status_code=400, detail="Event is at full capacity")
    # Check duplicate
    if crud.check_duplicate_registration(db, reg.event_id, reg.student_email):
        raise HTTPException(status_code=400, detail="Student already registered for this event")
    return crud.create_registration(db, reg)

@app.get("/api/registrations/event/{event_id}", response_model=List[schemas.RegistrationOut])
def get_event_registrations(event_id: int, db: Session = Depends(get_db)):
    return crud.get_registrations_by_event(db, event_id)

# ─── VENUES ──────────────────────────────────────────────────────────────────
@app.get("/api/venues", response_model=List[schemas.VenueOut])
def list_venues(db: Session = Depends(get_db)):
    return crud.get_venues(db)

@app.post("/api/venues", response_model=schemas.VenueOut, status_code=201)
def create_venue(venue: schemas.VenueCreate, db: Session = Depends(get_db)):
    return crud.create_venue(db, venue)

# ─── MONITORING & METRICS ────────────────────────────────────────────────────
@app.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)):
    stats = crud.get_dashboard_stats(db)
    return {
        "system": metrics_store.get_summary(),
        "database": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/metrics/requests")
def get_request_metrics():
    return metrics_store.get_request_history()

@app.get("/api/metrics/performance")
def get_performance():
    return metrics_store.get_performance_data()

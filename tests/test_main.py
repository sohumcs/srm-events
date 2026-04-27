"""
SRM Event Management System - Test Suite
PBL-3: Testing & Validation
Covers: Functional tests, validation tests, performance tests, security tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

from app.main import app, get_db
from app.database import Base

# ─── TEST DATABASE SETUP ──────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_srm_events.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# 1. HEALTH & SMOKE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestHealthAndSmoke:
    def test_health_endpoint_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_returns_correct_structure(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_docs_accessible(self):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_schema(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        assert "paths" in r.json()


# ═══════════════════════════════════════════════════════════════════════════
# 2. VENUE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestVenues:
    def test_create_venue_success(self):
        r = client.post("/api/venues", json={
            "name": "Test Auditorium", "location": "Block A",
            "capacity": 500, "facilities": "AC, Projector"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test Auditorium"
        assert data["capacity"] == 500
        assert "id" in data

    def test_list_venues(self):
        r = client.get("/api/venues")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_venue_missing_name_fails(self):
        r = client.post("/api/venues", json={"location": "Block B", "capacity": 100})
        assert r.status_code == 422  # Validation error

    def test_venue_stores_facilities(self):
        r = client.post("/api/venues", json={
            "name": "Seminar Hall", "location": "Acad Block",
            "capacity": 150, "facilities": "WiFi, Smart Board"
        })
        assert r.status_code == 201
        assert "WiFi" in r.json()["facilities"]


# ═══════════════════════════════════════════════════════════════════════════
# 3. EVENT CRUD TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEventCRUD:
    def setup_method(self):
        """Create a test event before each test"""
        r = client.post("/api/events", json={
            "title": "Test Hackathon",
            "description": "A test hackathon event",
            "category": "Technical",
            "date": "2025-06-15",
            "time": "09:00",
            "capacity": 100,
            "organizer": "CSE Dept",
            "status": "upcoming"
        })
        self.event_id = r.json()["id"]

    def test_create_event_returns_201(self):
        r = client.post("/api/events", json={
            "title": "New Workshop",
            "category": "Workshop",
            "date": "2025-07-01",
            "capacity": 50
        })
        assert r.status_code == 201

    def test_get_event_by_id(self):
        r = client.get(f"/api/events/{self.event_id}")
        assert r.status_code == 200
        assert r.json()["id"] == self.event_id
        assert r.json()["title"] == "Test Hackathon"

    def test_get_nonexistent_event_returns_404(self):
        r = client.get("/api/events/99999")
        assert r.status_code == 404

    def test_list_events(self):
        r = client.get("/api/events")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_filter_events_by_category(self):
        r = client.get("/api/events?category=Technical")
        assert r.status_code == 200
        for ev in r.json():
            assert ev["category"] == "Technical"

    def test_update_event(self):
        r = client.put(f"/api/events/{self.event_id}", json={
            "title": "Updated Hackathon",
            "category": "Technical",
            "date": "2025-06-15",
            "capacity": 200,
            "status": "upcoming"
        })
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Hackathon"
        assert r.json()["capacity"] == 200

    def test_delete_event(self):
        r = client.delete(f"/api/events/{self.event_id}")
        assert r.status_code == 200
        # Verify it's gone
        r2 = client.get(f"/api/events/{self.event_id}")
        assert r2.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# 4. VALIDATION & SECURITY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestValidationAndSecurity:
    def test_empty_title_rejected(self):
        r = client.post("/api/events", json={
            "title": "   ", "category": "Technical",
            "date": "2025-06-01", "capacity": 100
        })
        assert r.status_code == 422

    def test_negative_capacity_rejected(self):
        r = client.post("/api/events", json={
            "title": "Valid Title", "category": "Technical",
            "date": "2025-06-01", "capacity": -10
        })
        assert r.status_code == 422

    def test_invalid_category_rejected(self):
        r = client.post("/api/events", json={
            "title": "Valid Title", "category": "INVALID_CATEGORY",
            "date": "2025-06-01", "capacity": 100
        })
        assert r.status_code == 422

    def test_sql_injection_in_title_is_safe(self):
        """SQL injection attempt should either be stored safely or rejected"""
        payload = "'; DROP TABLE events; --"
        r = client.post("/api/events", json={
            "title": payload, "category": "Technical",
            "date": "2025-06-01", "capacity": 100
        })
        # Either accepted safely (parameterized query) or rejected by validation
        # Either way, the server should NOT crash
        assert r.status_code in [201, 422]
        # Verify events table still works
        r2 = client.get("/api/events")
        assert r2.status_code == 200

    def test_invalid_email_in_registration_rejected(self):
        ev = client.post("/api/events", json={
            "title": "Email Test Event", "category": "Technical",
            "date": "2025-06-01", "capacity": 100
        }).json()
        r = client.post("/api/registrations", json={
            "event_id": ev["id"],
            "student_name": "Test Student",
            "student_email": "not-an-email",
        })
        assert r.status_code == 422

    def test_xss_in_description_stored_safely(self):
        """XSS payload should be stored as plain text, not executed"""
        r = client.post("/api/events", json={
            "title": "XSS Test", "category": "Technical",
            "date": "2025-06-01", "capacity": 100,
            "description": "<script>alert('xss')</script>"
        })
        assert r.status_code == 201
        # Content stored as text, not rendered as HTML in API response
        assert r.json()["description"] == "<script>alert('xss')</script>"

    def test_capacity_overflow_rejected(self):
        r = client.post("/api/events", json={
            "title": "Big Event", "category": "Technical",
            "date": "2025-06-01", "capacity": 99999999
        })
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# 5. REGISTRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestRegistrations:
    def setup_method(self):
        r = client.post("/api/events", json={
            "title": "Reg Test Event", "category": "Technical",
            "date": "2025-06-15", "capacity": 5
        })
        self.event_id = r.json()["id"]

    def test_registration_success(self):
        r = client.post("/api/registrations", json={
            "event_id": self.event_id,
            "student_name": "Test Student",
            "student_email": "test@srmist.edu.in",
            "student_reg_no": "RA2111003010001",
            "department": "CSE", "year": 3
        })
        assert r.status_code == 201
        assert r.json()["student_name"] == "Test Student"

    def test_duplicate_registration_rejected(self):
        email = "dup@srmist.edu.in"
        reg_data = {
            "event_id": self.event_id,
            "student_name": "Dup Student",
            "student_email": email
        }
        r1 = client.post("/api/registrations", json=reg_data)
        assert r1.status_code == 201
        r2 = client.post("/api/registrations", json=reg_data)
        assert r2.status_code == 400
        assert "already registered" in r2.json()["detail"]

    def test_register_for_nonexistent_event(self):
        r = client.post("/api/registrations", json={
            "event_id": 99999,
            "student_name": "Ghost Student",
            "student_email": "ghost@srmist.edu.in"
        })
        assert r.status_code == 404

    def test_capacity_enforcement(self):
        """Event with capacity 5 should reject 6th registration"""
        for i in range(5):
            client.post("/api/registrations", json={
                "event_id": self.event_id,
                "student_name": f"Student {i}",
                "student_email": f"s{i}cap@srmist.edu.in"
            })
        r = client.post("/api/registrations", json={
            "event_id": self.event_id,
            "student_name": "Overflow Student",
            "student_email": "overflow@srmist.edu.in"
        })
        assert r.status_code == 400
        assert "capacity" in r.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# 6. PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPerformance:
    def test_event_list_under_500ms(self):
        start = time.time()
        r = client.get("/api/events")
        elapsed = (time.time() - start) * 1000
        assert r.status_code == 200
        assert elapsed < 500, f"Response took {elapsed:.0f}ms, expected < 500ms"

    def test_health_check_under_100ms(self):
        start = time.time()
        client.get("/health")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"Health check took {elapsed:.0f}ms"

    def test_metrics_endpoint_accessible(self):
        r = client.get("/api/metrics")
        assert r.status_code == 200
        assert "database" in r.json()
        assert "system" in r.json()

    def test_create_10_events_performance(self):
        """Bulk insert performance test"""
        start = time.time()
        for i in range(10):
            client.post("/api/events", json={
                "title": f"Perf Test Event {i}",
                "category": "Technical",
                "date": "2025-09-01",
                "capacity": 50
            })
        elapsed = time.time() - start
        assert elapsed < 5.0, f"10 inserts took {elapsed:.2f}s"

    def test_concurrent_reads(self):
        """Simulate multiple read requests"""
        times = []
        for _ in range(20):
            start = time.time()
            r = client.get("/api/events")
            times.append((time.time() - start) * 1000)
            assert r.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 200, f"Avg response {avg:.1f}ms, expected < 200ms"


# ═══════════════════════════════════════════════════════════════════════════
# 7. MONITORING & METRICS TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMonitoring:
    def test_metrics_endpoint(self):
        r = client.get("/api/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "system" in data
        assert "database" in data
        assert "timestamp" in data

    def test_metrics_request_history(self):
        r = client.get("/api/metrics/requests")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_performance_metrics(self):
        r = client.get("/api/metrics/performance")
        assert r.status_code == 200
        data = r.json()
        assert "response_time_distribution" in data

    def test_system_metrics_structure(self):
        r = client.get("/api/metrics")
        sys = r.json()["system"]
        required = ["total_requests", "error_count", "avg_response_ms", "uptime_seconds"]
        for key in required:
            assert key in sys, f"Missing metric: {key}"

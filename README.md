# SRM Event Management System
### Cloud Product and Platform Engineering — 21IPE315P

A cloud-native, production-grade event management platform for SRM Institute of Science and Technology, Kattankulathur.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    SRM Events Platform                    │
├─────────────────┬───────────────────┬───────────────────┤
│   Frontend      │   Backend API     │   Data Layer      │
│   HTML/CSS/JS   │   FastAPI (REST)  │   SQLite/Postgres │
│   Chart.js      │   Pydantic        │   SQLAlchemy ORM  │
│   Fetch API     │   Middleware      │   DB Indexes      │
└─────────────────┴───────────────────┴───────────────────┘
        │                   │                  │
┌───────▼───────────────────▼──────────────────▼──────────┐
│              Cloud Deployment (Render.com)                │
│   CI/CD: GitHub Actions → Build → Test → Deploy          │
│   Monitoring: /api/metrics (live dashboards)             │
└──────────────────────────────────────────────────────────┘
```

## Features

### PBL-1: Product Design & Architecture
- ✅ Real-world problem: Campus event management at SRM
- ✅ Cloud-native REST API architecture
- ✅ User stories: Students register, admins manage events
- ✅ Security: Input validation, SQL injection prevention

### PBL-2: Implementation
- ✅ Full CRUD for Events, Venues, Registrations
- ✅ SQLite database with optimized indexes
- ✅ Pydantic validation (security layer)
- ✅ Docker-ready, CI/CD with GitHub Actions

### PBL-3: Testing, Optimization & Deployment
- ✅ **30+ pytest tests** covering functional, validation, performance, security
- ✅ **Live monitoring dashboard** with real metrics (Chart.js)
- ✅ **Performance tests** with response time assertions
- ✅ **Render.com deployment** — real cloud URL
- ✅ **Risk mitigation**: SQL injection safe, capacity enforcement, duplicate prevention

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn app.main:app --reload

# 3. Open browser
open http://localhost:8000

# 4. Run tests
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /api/events | List all events |
| POST | /api/events | Create event |
| PUT | /api/events/{id} | Update event |
| DELETE | /api/events/{id} | Delete event |
| GET | /api/registrations | List registrations |
| POST | /api/registrations | Register student |
| GET | /api/venues | List venues |
| POST | /api/venues | Add venue |
| GET | /api/metrics | System metrics |

## Security Features
- Pydantic input validation on all endpoints
- Parameterized SQL queries (SQLAlchemy ORM — no raw SQL)
- Email format validation with regex
- Capacity enforcement
- Duplicate registration prevention

## Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: SQLite (WAL mode + indexed queries)
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Testing**: pytest, httpx (TestClient)
- **CI/CD**: GitHub Actions
- **Cloud**: Render.com (free tier)

---
*SRM Institute of Science and Technology, Kattankulathur*

# Job Tracker Django

> A production-grade **Django** job application tracking system — demonstrating the complete Django ecosystem from ORM to WebSockets.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14-red)](https://www.django-rest-framework.org)
[![Celery](https://img.shields.io/badge/Celery-5.3-brightgreen)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7.x-red)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What Is This?

**Job Tracker** is a full-featured REST API that lets users manage their entire job search pipeline — from the first application to the final offer.

Built to showcase **every major area of Django** that matters in a professional engineering role.

---

## Features

| Feature | Technology |
|---------|-----------|
| Custom User Model (email login) | `AbstractUser` |
| JWT Authentication (login/register/refresh/logout) | `djangorestframework-simplejwt` |
| REST API with filtering, search, pagination | `Django REST Framework` |
| Application pipeline (Applied → Offer) | `DRF ViewSets + Routers` |
| Nested serializers (contacts, interviews) | `DRF Serializers` |
| Status-change auto email + notification | `Django Signals` |
| Interview reminders & weekly emails | `Celery + Celery Beat` |
| Real-time push notifications | `Django Channels + WebSockets` |
| Dashboard stats with caching | `Redis Cache` |
| Production admin panel | `Django Admin (customized)` |
| Auto API docs | `drf-spectacular (Swagger + ReDoc)` |
| Full test suite | `Django TestCase + APIClient` |
| Containerized | `Docker + docker-compose` |

---

## Project Structure

```
job-tracker-django/
│
├── config/                          # Django project config
│   ├── settings/
│   │   ├── base.py                  # Shared settings
│   │   ├── development.py           # Dev overrides
│   │   └── production.py            # Prod overrides
│   ├── urls.py                      # Root URL config
│   ├── celery.py                    # Celery app + Beat schedule
│   ├── asgi.py                      # ASGI (Channels/WebSocket)
│   └── wsgi.py
│
├── apps/
│   ├── accounts/                    # Auth & user management
│   │   ├── models.py                # CustomUser (AbstractUser)
│   │   ├── serializers.py           # Register, Profile, ChangePassword
│   │   ├── views.py                 # Register, Login, Profile, Logout
│   │   ├── urls.py
│   │   ├── admin.py                 # Custom UserAdmin
│   │   ├── signals.py               # Post-save: send welcome email
│   │   └── tests.py
│   │
│   ├── jobs/                        # Core job tracking
│   │   ├── models.py                # Company, Application, Contact, InterviewRound
│   │   ├── serializers.py           # List/Detail/Dashboard serializers
│   │   ├── views.py                 # ViewSets + dashboard + status update
│   │   ├── filters.py               # DjangoFilterBackend filters
│   │   ├── urls.py                  # DRF Router
│   │   ├── admin.py                 # Colored status, inline models, bulk actions
│   │   ├── signals.py               # pre_save/post_save: status change handler
│   │   └── tests.py
│   │
│   ├── notifications/               # In-app notification system
│   │   ├── models.py                # Notification model
│   │   ├── consumers.py             # WebSocket consumer (Channels)
│   │   ├── routing.py               # WebSocket URL routing
│   │   ├── utils.py                 # create_notification() helper
│   │   ├── views.py                 # List, mark-read, clear
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   └── tasks/                       # Celery async tasks
│       ├── email_tasks.py           # Welcome, status-change, reminders, weekly summary
│       └── tests.py
│
├── templates/
│   └── emails/                      # Plain-text email templates
│       ├── welcome.txt
│       ├── status_change.txt
│       └── interview_reminder.txt
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── docker-compose.yml               # Full stack: web + db + redis + celery + beat
├── Dockerfile
├── manage.py
├── pytest.ini
└── .env.example
```

---

## Data Models

```
CustomUser
  └── email (login), full_name, avatar, role, target_role, target_salary

Company
  └── name, website, industry, size, notes  →  FK: user

Application
  └── job_title, status, work_mode, salary_min/max, applied_date, notes  →  FK: user, company
      ├── Contact (name, role, email, linkedin)
      └── InterviewRound (type, scheduled_at, outcome, feedback)

Notification
  └── title, message, type, is_read  →  FK: user
```

---

## API Endpoints

### Auth
```
POST   /api/v1/auth/register/           Register + get tokens
POST   /api/v1/auth/login/              Login (email + password)
POST   /api/v1/auth/token/refresh/      Refresh access token
POST   /api/v1/auth/logout/             Blacklist refresh token
GET    /api/v1/auth/profile/            View profile
PUT    /api/v1/auth/profile/            Update profile
POST   /api/v1/auth/change-password/    Change password
```

### Applications
```
GET    /api/v1/applications/                  List (paginated, filterable, searchable)
POST   /api/v1/applications/                  Create
GET    /api/v1/applications/{id}/             Detail (with contacts + interviews)
PUT    /api/v1/applications/{id}/             Full update
PATCH  /api/v1/applications/{id}/             Partial update
DELETE /api/v1/applications/{id}/             Delete
GET    /api/v1/applications/dashboard/        Stats + pipeline summary (cached)
PATCH  /api/v1/applications/{id}/update_status/  Quick status change
```

### Companies
```
GET    /api/v1/companies/         List companies
POST   /api/v1/companies/         Create
GET    /api/v1/companies/{id}/    Detail + application count
PUT    /api/v1/companies/{id}/    Update
DELETE /api/v1/companies/{id}/    Delete
```

### Interviews
```
GET    /api/v1/interviews/            List all rounds
POST   /api/v1/interviews/            Schedule interview
GET    /api/v1/interviews/{id}/       Detail
PATCH  /api/v1/interviews/{id}/       Update outcome/feedback
GET    /api/v1/interviews/upcoming/   Interviews in next 7 days
```

### Contacts
```
GET    /api/v1/contacts/         List
POST   /api/v1/contacts/         Create
PATCH  /api/v1/contacts/{id}/    Update
DELETE /api/v1/contacts/{id}/    Delete
```

### Notifications
```
GET    /api/v1/notifications/          List notifications
PATCH  /api/v1/notifications/{id}/     Mark as read
DELETE /api/v1/notifications/clear/    Delete all read notifications

WS     ws://localhost:8000/ws/notifications/   Real-time push
```

### API Docs
```
GET    /api/schema/swagger-ui/    Swagger UI (interactive)
GET    /api/schema/redoc/         ReDoc
GET    /api/schema/               Raw OpenAPI schema
```

---

## How to Run

### Option A — Docker (Recommended, easiest)

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# 1. Clone the repo
git clone https://github.com/ramabharti8/job-tracker-django.git
cd job-tracker-django

# 2. Create your .env file
cp .env.example .env
```

Open `.env` and set at minimum:
```
SECRET_KEY=any-random-long-string-here
DEBUG=True
DATABASE_URL=postgres://postgres:postgres@db:5432/jobtracker
REDIS_URL=redis://redis:6379/0
```

```bash
# 3. Start everything
docker-compose up --build

# 4. In a second terminal — run migrations and create superuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

**That's it.** Services running:

| Service | URL |
|---------|-----|
| Django API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/schema/swagger-ui/ |
| Django Admin | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

### Option B — Run Locally (without Docker)

**Requires:** Python 3.11+, PostgreSQL, Redis

#### Step 1 — Clone and set up virtual environment

```bash
git clone https://github.com/ramabharti8/job-tracker-django.git
cd job-tracker-django

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

#### Step 2 — Install dependencies

```bash
pip install -r requirements/development.txt
```

#### Step 3 — Set up environment variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-secret-key-any-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://postgres:yourpassword@localhost:5432/jobtracker
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### Step 4 — Create PostgreSQL database

```bash
# Open psql
psql -U postgres

# Inside psql
CREATE DATABASE jobtracker;
\q
```

#### Step 5 — Run migrations

```bash
python manage.py migrate
```

#### Step 6 — Create a superuser (for admin panel)

```bash
python manage.py createsuperuser
# Enter email, password when prompted
```

#### Step 7 — Start Redis

```bash
# Windows (with Redis installed)
redis-server

# Mac (with Homebrew)
brew services start redis
```

#### Step 8 — Start Celery worker (new terminal)

```bash
# Activate venv first
venv\Scripts\activate       # Windows

celery -A config worker -l info
```

#### Step 9 — Start Celery Beat scheduler (new terminal)

```bash
venv\Scripts\activate

celery -A config beat -l info
```

#### Step 10 — Start Django server (new terminal)

```bash
venv\Scripts\activate

python manage.py runserver
```

**Open:** http://localhost:8000/api/schema/swagger-ui/

---

## Testing the API (Quick Start)

### 1. Register a user
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rama@example.com",
    "full_name": "Rama Bharti",
    "password": "MyPass123!",
    "password2": "MyPass123!"
  }'
```
Response gives you `access` and `refresh` tokens. Copy the `access` token.

### 2. Create a company
```bash
curl -X POST http://localhost:8000/api/v1/companies/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Google", "industry": "Technology", "size": "enterprise"}'
```

### 3. Add a job application
```bash
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company": 1,
    "job_title": "Backend Engineer",
    "job_url": "https://careers.google.com/jobs/123",
    "work_mode": "hybrid",
    "salary_min": 120000,
    "salary_max": 160000,
    "excitement_level": 5
  }'
```

### 4. View dashboard stats
```bash
curl http://localhost:8000/api/v1/applications/dashboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Update application status
```bash
curl -X PATCH http://localhost:8000/api/v1/applications/1/update_status/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "screening"}'
```
> This triggers a Django Signal → sends status-change email + creates a notification

### 6. Open Swagger UI
Visit: **http://localhost:8000/api/schema/swagger-ui/**  
Click **Authorize** → enter `Bearer YOUR_ACCESS_TOKEN` → test all endpoints interactively.

---

## Running Tests

```bash
# Run all tests
python manage.py test

# Run a specific app
python manage.py test apps.jobs
python manage.py test apps.accounts
python manage.py test apps.notifications
python manage.py test apps.tasks

# With pytest
pytest

# With coverage report
pip install coverage
coverage run manage.py test
coverage report
coverage html        # Opens detailed HTML report in htmlcov/
```

---

## Django Concepts Demonstrated

| Concept | File |
|---------|------|
| Custom User Model | `apps/accounts/models.py` |
| Abstract Base Model | `TimeStampedModel` in `apps/jobs/models.py` |
| ForeignKey, choices, properties | `apps/jobs/models.py` |
| Django ORM — annotate, Count, filter | `apps/jobs/views.py` |
| Model Signals (pre_save + post_save) | `apps/jobs/signals.py` |
| DRF Serializers (nested, read_only, validate) | `apps/jobs/serializers.py` |
| DRF ModelViewSet + custom actions | `apps/jobs/views.py` |
| DRF Routers | `apps/jobs/urls.py` |
| DRF Permissions (IsAuthenticated) | All views |
| DRF Filtering + Search + Ordering | `apps/jobs/filters.py` |
| DRF Pagination | `config/settings/base.py` |
| JWT Auth | `apps/accounts/views.py` |
| Celery shared_task + retry | `apps/tasks/email_tasks.py` |
| Celery Beat (crontab schedule) | `config/celery.py` |
| Django Channels WebSocket | `apps/notifications/consumers.py` |
| Redis Caching + invalidation | `apps/jobs/views.py` dashboard |
| Custom Admin (colored columns, inlines) | `apps/jobs/admin.py` |
| Split settings (base/dev/prod) | `config/settings/` |
| Email backend | `config/settings/base.py` |
| Docker multi-service | `docker-compose.yml` |

---

## Admin Panel

URL: **http://localhost:8000/admin/**

Login with your superuser credentials.

| Section | Features |
|---------|----------|
| **Users** | Manage users, roles, avatars, preferences |
| **Applications** | Color-coded status column, bulk reject/withdraw, inline contacts + interviews |
| **Companies** | Annotated with application count |
| **Interview Rounds** | Color-coded outcome (green/red/orange) |
| **Notifications** | View all user notifications |
| **Celery Beat** | Manage periodic task schedules (from Django admin) |

---

## Tech Stack

```
Backend          : Django 4.2 · Django REST Framework 3.14
Auth             : djangorestframework-simplejwt (JWT)
Async Tasks      : Celery 5.3 + Celery Beat
Real-Time        : Django Channels 4.x + WebSockets
Cache / Broker   : Redis 7
Database         : PostgreSQL 15
API Docs         : drf-spectacular (Swagger UI + ReDoc)
Email            : Django Email + SMTP
Testing          : Django TestCase · DRF APIClient · pytest-django
Deployment       : Docker · docker-compose · Gunicorn · WhiteNoise
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built by [Rama Bharti](https://github.com/ramabharti8) · Headstarter AI Fellowship · Production Django Project*

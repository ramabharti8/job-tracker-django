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

**Job Tracker** is a full-featured web application that lets users manage their entire job search pipeline — from the first application to the final offer — in one place.

It is deliberately built to showcase **every major area of Django** that matters in a professional engineering role:

- Custom user authentication
- Relational data modeling
- REST API design with Django REST Framework
- Async task processing with Celery + Redis
- Real-time updates via Django Channels (WebSockets)
- Redis caching for performance
- Signal-driven automation
- Production-grade admin panel
- Comprehensive test suite

---

## Features

### Core Application
- **Pipeline Management** — Track applications across 6 stages: `Applied → Screening → Phone Interview → Technical Interview → Offer → Rejected`
- **Application Dashboard** — Live stats: total applied, response rate, interview conversion, avg. days-to-offer
- **Company & Contact Manager** — Store recruiter contacts, company notes, and salary benchmarks per company
- **Document Vault** — Attach resume versions and cover letters to each application
- **Interview Scheduler** — Log interview rounds with date, type (phone/video/onsite), and feedback notes

### Technical Features
- **JWT Authentication** — Secure login with access + refresh token rotation
- **Role-Based Access** — `User` and `Admin` roles with DRF permission classes
- **Async Email Reminders** — Celery Beat sends interview reminder emails 24h before scheduled time
- **Status Change Signals** — Django signal auto-triggers email + in-app notification on status change
- **Real-Time Notifications** — Django Channels WebSocket pushes live status updates to the browser
- **Redis Caching** — Dashboard stats cached with auto-invalidation on data change
- **Custom Admin** — Full `list_display`, `list_filter`, bulk actions, and inline editing in Django admin
- **API Documentation** — Auto-generated Swagger/OpenAPI docs via `drf-spectacular`
- **Pagination & Filtering** — DRF pagination, search, and ordering on all list endpoints
- **Full Test Suite** — Model tests, API tests with `APIClient`, Celery task tests, signal tests

---

## Tech Stack

```
Backend          : Django 4.2 · Django REST Framework 3.14
Auth             : djangorestframework-simplejwt
Async Tasks      : Celery 5.3 · Celery Beat (periodic tasks)
Real-Time        : Django Channels 4.x · WebSockets
Cache / Broker   : Redis 7
Database         : PostgreSQL 15
Admin            : Django Admin (customized)
API Docs         : drf-spectacular (Swagger UI + ReDoc)
Email            : Django Email Backend (SMTP / SendGrid)
Testing          : Django TestCase · DRF APIClient · pytest-django
Deployment       : Docker · Docker Compose · Gunicorn · Nginx
```

---

## Project Structure

```
job-tracker-django/
├── config/                    # Django project settings
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Dev overrides
│   │   └── production.py      # Prod overrides
│   ├── urls.py
│   ├── asgi.py                # ASGI config (Channels)
│   └── celery.py              # Celery app config
│
├── apps/
│   ├── accounts/              # Custom user model & auth
│   │   ├── models.py          # CustomUser (AbstractUser)
│   │   ├── serializers.py     # Register, Login, Profile
│   │   ├── views.py           # Auth endpoints
│   │   ├── signals.py         # Post-save user signals
│   │   └── tests.py
│   │
│   ├── jobs/                  # Core job tracking
│   │   ├── models.py          # Application, Company, Contact, Interview
│   │   ├── serializers.py     # Nested serializers
│   │   ├── views.py           # ViewSets
│   │   ├── filters.py         # DjangoFilterBackend filters
│   │   ├── signals.py         # Status-change notifications
│   │   ├── admin.py           # Custom admin config
│   │   └── tests.py
│   │
│   ├── notifications/         # In-app notification system
│   │   ├── models.py          # Notification model
│   │   ├── consumers.py       # WebSocket consumer (Channels)
│   │   ├── routing.py         # WebSocket URL routing
│   │   └── tests.py
│   │
│   └── tasks/                 # Celery async tasks
│       ├── email_tasks.py     # Interview reminders, status emails
│       ├── report_tasks.py    # Weekly summary email
│       └── tests.py
│
├── templates/                 # Email HTML templates
├── docker-compose.yml         # Full stack: Django + Postgres + Redis + Celery
├── Dockerfile
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
└── README.md
```

---

## Data Models

### `CustomUser`
```python
# Extends AbstractUser
email           # Login field (unique)
full_name
avatar
date_joined
is_active
role            # 'user' | 'admin'
```

### `Company`
```python
name            # Unique company name
website
industry
size            # startup / mid / enterprise
notes
created_at
```

### `Application`
```python
user            # FK → CustomUser
company         # FK → Company
job_title
job_url
status          # Applied / Screening / Phone / Technical / Offer / Rejected
salary_min
salary_max
location
work_mode       # remote / hybrid / onsite
applied_date
last_updated
notes
```

### `Contact`
```python
application     # FK → Application
name
role            # Recruiter / Hiring Manager / etc.
email
linkedin_url
notes
```

### `InterviewRound`
```python
application     # FK → Application
round_number
interview_type  # phone / video / onsite / technical
scheduled_at
duration_mins
interviewer
feedback
outcome         # pending / passed / failed
```

### `Notification`
```python
user            # FK → CustomUser
title
message
is_read
created_at
```

---

## API Endpoints

### Auth
```
POST   /api/v1/auth/register/          Register new user
POST   /api/v1/auth/login/             Obtain JWT tokens
POST   /api/v1/auth/token/refresh/     Refresh access token
GET    /api/v1/auth/profile/           Get current user profile
PUT    /api/v1/auth/profile/           Update profile
```

### Applications
```
GET    /api/v1/applications/           List all applications (paginated, filterable)
POST   /api/v1/applications/           Create new application
GET    /api/v1/applications/{id}/      Retrieve application detail
PUT    /api/v1/applications/{id}/      Update application
PATCH  /api/v1/applications/{id}/      Partial update (e.g. status change)
DELETE /api/v1/applications/{id}/      Delete application
GET    /api/v1/applications/dashboard/ Aggregated stats & pipeline summary
```

### Companies
```
GET    /api/v1/companies/              List companies
POST   /api/v1/companies/             Create company
GET    /api/v1/companies/{id}/        Company detail + linked applications
```

### Interviews
```
GET    /api/v1/interviews/             List all interview rounds
POST   /api/v1/interviews/            Schedule interview
PATCH  /api/v1/interviews/{id}/       Update outcome / feedback
GET    /api/v1/interviews/upcoming/   Interviews in next 7 days
```

### Notifications
```
GET    /api/v1/notifications/          List notifications
PATCH  /api/v1/notifications/{id}/     Mark as read
DELETE /api/v1/notifications/clear/    Clear all read notifications

WS     ws://localhost:8000/ws/notifications/   Real-time push
```

### API Docs
```
GET    /api/schema/swagger-ui/         Swagger UI
GET    /api/schema/redoc/              ReDoc
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/ramabharti8/job-tracker-django.git
cd job-tracker-django
```

### 2. Run with Docker (recommended)
```bash
cp .env.example .env
# Fill in your values in .env
docker-compose up --build
```

This starts:
- Django dev server on `http://localhost:8000`
- PostgreSQL on port `5432`
- Redis on port `6379`
- Celery worker
- Celery Beat (scheduler)

### 3. Or run locally

```bash
# Create and activate virtualenv
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Set up environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Redis (must be running separately)
redis-server

# Start Celery worker (separate terminal)
celery -A config worker -l info

# Start Celery Beat (separate terminal)
celery -A config beat -l info

# Run Django
python manage.py runserver
```

---

## Environment Variables

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:password@localhost:5432/jobtracker

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Job Tracker <noreply@jobtracker.com>

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test apps.jobs

# With pytest-django
pytest

# With coverage
coverage run manage.py test
coverage report
coverage html    # open htmlcov/index.html
```

---

## Django Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Custom User Model | `apps/accounts/models.py` |
| Abstract Base Models | `apps/core/models.py` |
| ForeignKey / ManyToMany | `apps/jobs/models.py` |
| Model `__str__`, `Meta`, `ordering` | All models |
| Django ORM — annotate, aggregate | `apps/jobs/views.py` dashboard |
| Model Signals | `apps/jobs/signals.py` |
| Custom Manager | `apps/jobs/managers.py` |
| DRF Serializers (nested) | `apps/jobs/serializers.py` |
| DRF ViewSets + Routers | `apps/jobs/views.py` |
| DRF Permissions | `apps/accounts/permissions.py` |
| DRF Filtering + Search | `apps/jobs/filters.py` |
| DRF Pagination | `config/settings/base.py` |
| JWT Auth | `djangorestframework-simplejwt` |
| Celery Tasks | `apps/tasks/email_tasks.py` |
| Celery Beat (periodic) | `config/celery.py` |
| Django Channels (WebSocket) | `apps/notifications/consumers.py` |
| Redis Cache | `apps/jobs/views.py` dashboard |
| Custom Admin | `apps/jobs/admin.py` |
| Admin Inline | `apps/jobs/admin.py` |
| Email Templates | `templates/emails/` |
| Environment-split Settings | `config/settings/` |
| Docker + Compose | `Dockerfile`, `docker-compose.yml` |
| Test Suite | `tests.py` in every app |

---

## Admin Panel

Access at `http://localhost:8000/admin/`

Customized features:
- **Applications** — filterable by status, company, date range; bulk status-change action
- **Companies** — inline contacts, annotated with application count
- **Interviews** — color-coded outcome column
- **Users** — full profile management, last login tracking

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built by [Rama Bharti](https://github.com/ramabharti8) · Headstarter AI Fellowship · Production Django Project*

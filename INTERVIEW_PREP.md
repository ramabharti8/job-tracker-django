# Job Tracker Django — Complete Interview Prep Book

> Every question an interviewer can ask about this project — answered as an experienced Django developer.

---

## TABLE OF CONTENTS

1. [Project Overview Questions](#1-project-overview)
2. [Django Core](#2-django-core)
3. [Custom User Model](#3-custom-user-model)
4. [Models & ORM](#4-models--orm)
5. [Django REST Framework](#5-django-rest-framework)
6. [Authentication & JWT](#6-authentication--jwt)
7. [Signals](#7-django-signals)
8. [Celery & Async Tasks](#8-celery--async-tasks)
9. [Django Channels & WebSockets](#9-django-channels--websockets)
10. [Redis & Caching](#10-redis--caching)
11. [Admin Panel](#11-django-admin)
12. [Testing](#12-testing)
13. [Settings & Configuration](#13-settings--configuration)
14. [Docker & Deployment](#14-docker--deployment)
15. [Security](#15-security)
16. [Performance & Scalability](#16-performance--scalability)
17. [Database & Migrations](#17-database--migrations)
18. [Tricky / Advanced Questions](#18-tricky--advanced-questions)

---

## 1. PROJECT OVERVIEW

---

**Q: Tell me about this project.**

A: Job Tracker is a production-grade REST API built with Django 4.2 that helps users manage their entire job search pipeline — from the first application all the way to an offer. Users can track applications across companies, log interview rounds with feedback, manage recruiter contacts, and get automated email reminders before scheduled interviews.

I built it specifically to demonstrate the full Django ecosystem — not just models and views, but also signals, async tasks with Celery, real-time WebSocket notifications with Django Channels, Redis caching, custom admin, JWT authentication, and a full test suite. Everything is containerized with Docker.

---

**Q: Why did you choose this project idea?**

A: I wanted a project that was real-world and relatable — everyone understands job hunting. But more importantly, it gave me a natural reason to use every major Django feature:
- Applications changing status → perfect use case for signals
- Interview reminders → perfect for Celery Beat scheduled tasks
- Live status updates → perfect for WebSockets
- Dashboard stats that don't change every second → perfect for Redis caching
- Complex relationships (user → application → interview rounds → contacts) → showcases Django ORM

---

**Q: Walk me through the data flow when a user updates an application status.**

A: Great question. Here's the full chain:

1. Client sends `PATCH /api/v1/applications/1/update_status/` with `{"status": "screening"}` and a Bearer token
2. JWT middleware authenticates the request and attaches the user to `request.user`
3. DRF's `IsAuthenticated` permission class validates the user
4. `ApplicationViewSet.update_status()` action runs — fetches the application (ownership verified by queryset filtering on `user=request.user`), validates the new status
5. `application.save()` triggers the `pre_save` signal which captures the old status, then `post_save` fires
6. The `post_save` signal calls `send_status_change_email.delay()` — a Celery task that runs asynchronously in the background
7. The signal also calls `create_notification()` which saves a `Notification` record and pushes it via Django Channels to the user's WebSocket connection
8. Redis cache for the dashboard is invalidated (`cache.delete(f"dashboard_{user.id}")`)
9. The API returns the updated application data immediately — the user doesn't wait for the email

---

**Q: What was the hardest part of building this project?**

A: The trickiest part was getting the signal + Celery + Channels chain to work reliably together. The challenge was:
- Signals are synchronous and run inside the database transaction
- If the Celery task tries to read the application before the transaction commits, it gets stale data
- The solution is to use `transaction.on_commit()` to delay the Celery task dispatch until after the DB transaction commits

Also, Django Channels required switching from WSGI to ASGI, which needed careful configuration in `asgi.py` with `ProtocolTypeRouter`.

---

## 2. DJANGO CORE

---

**Q: What is Django's MVT architecture?**

A: MVT stands for Model-View-Template.
- **Model** — defines the data structure and handles database interaction via the ORM
- **View** — contains the business logic, processes requests, returns responses
- **Template** — handles presentation (HTML rendering)

In this project, since it's a REST API, we don't use templates for responses — instead DRF Serializers act as the presentation layer, converting model instances to JSON.

---

**Q: What is the Django request-response lifecycle?**

A: When a request comes in:
1. `WSGI/ASGI` server receives the HTTP request
2. Django's URL dispatcher (`urls.py`) matches the URL pattern
3. Middleware stack processes the request (security, sessions, auth, CORS, etc.)
4. The matched view function/class is called
5. The view interacts with models/database
6. The view returns a `HttpResponse` (or DRF `Response`)
7. Middleware processes the response (in reverse order)
8. Response is sent back to the client

In this project I have middleware for: security, WhiteNoise (static files), CORS, CSRF, authentication, and messages.

---

**Q: What is middleware and what middleware do you use?**

A: Middleware is a hook into Django's request/response processing. Each middleware can modify the request before it hits the view, or modify the response before it goes back to the client.

In this project:
- `SecurityMiddleware` — sets security headers (HTTPS redirect, XSS protection)
- `WhiteNoiseMiddleware` — serves static files efficiently without a separate web server
- `CorsMiddleware` — handles Cross-Origin Resource Sharing headers
- `SessionMiddleware` — enables session support
- `AuthenticationMiddleware` — attaches `request.user` to every request
- `CsrfViewMiddleware` — protects against CSRF attacks

---

**Q: What is `settings.py` splitting and why did you do it?**

A: Instead of one `settings.py`, I split it into three files under `config/settings/`:
- `base.py` — common settings shared everywhere (installed apps, DRF config, JWT, Redis, etc.)
- `development.py` — imports base and adds dev-specific overrides (DEBUG=True, console email backend)
- `production.py` — imports base and adds prod hardening (HTTPS, HSTS, compressed static files)

The benefit is you never accidentally run production settings locally or push debug settings to prod. You select the environment with `DJANGO_SETTINGS_MODULE=config.settings.development`.

---

**Q: What is `django-environ` and why use it?**

A: `django-environ` reads environment variables from a `.env` file and provides type casting. Instead of:
```python
import os
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```
You write:
```python
env = environ.Env(DEBUG=(bool, False))
DEBUG = env('DEBUG')
```
It handles booleans, integers, lists, database URLs, and more automatically. It also keeps secrets out of the codebase — `.env` is in `.gitignore`.

---

## 3. CUSTOM USER MODEL

---

**Q: Why did you create a custom User model instead of using Django's default?**

A: Django's default `User` model uses `username` as the login field. I wanted `email` as the login field because:
1. Emails are unique and users remember them
2. No username collision issues
3. More professional for a job-tracking app

Django's official documentation strongly recommends creating a custom user model at the start of every project because it's very difficult to swap it out later once you have migrations. So I extended `AbstractUser`, set `username = None`, and set `USERNAME_FIELD = "email"`.

---

**Q: What's the difference between `AbstractUser` and `AbstractBaseUser`?**

A:
- `AbstractUser` — gives you all of Django's built-in user fields (first_name, last_name, is_staff, is_active, groups, permissions) plus authentication. You just add extra fields. Much less code.
- `AbstractBaseUser` — gives you only the password hashing and authentication. You define everything else yourself. Use when you need total control over the user model structure.

I used `AbstractUser` because I needed standard Django admin, permissions, and groups — no reason to reinvent them. I just added fields like `full_name`, `avatar`, `role`, `target_role`, and `target_salary`.

---

**Q: How did you set email as the login field?**

A:
```python
class CustomUser(AbstractUser):
    username = None                    # Remove username field
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"           # Use email for login
    REQUIRED_FIELDS = []               # No required fields for createsuperuser prompt
```

And in `settings.py`:
```python
AUTH_USER_MODEL = "accounts.CustomUser"
```

This must be set before the first migration. If you set it after, you'll have to reset your entire database.

---

**Q: What is the `display_name` property in your user model?**

A:
```python
@property
def display_name(self):
    return self.full_name or self.email.split("@")[0]
```

It's a Python `@property` — not stored in the database, computed on access. If the user has a full name, use it; otherwise fall back to the part of their email before the `@`. This is used in email templates to personalize messages.

---

## 4. MODELS & ORM

---

**Q: Explain your model structure and relationships.**

A: I have four main models in the `jobs` app:

- **Company** — belongs to a user (`ForeignKey → CustomUser`). Stores company info.
- **Application** — belongs to a user and a company (`ForeignKey → CustomUser`, `ForeignKey → Company`). This is the core model — tracks job title, status, salary range, work mode, etc.
- **Contact** — belongs to an application (`ForeignKey → Application`). Stores recruiter/hiring manager contact info.
- **InterviewRound** — belongs to an application (`ForeignKey → Application`). Tracks each interview round with type, scheduled time, and outcome.
- **Notification** — belongs to a user (`ForeignKey → CustomUser`). Stores in-app notifications.

---

**Q: What is `TimeStampedModel` and why did you use it?**

A:
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

It's an abstract base model. `abstract = True` means Django doesn't create a database table for it. All models that inherit from it get `created_at` and `updated_at` fields automatically.

`auto_now_add=True` sets the time once when the record is created. `auto_now=True` updates the time every time the record is saved. This is a common pattern to avoid repeating these two fields in every model.

---

**Q: What is `TextChoices` and how did you use it?**

A: `TextChoices` is Django's way to define enumerated choices for a CharField:

```python
class Status(models.TextChoices):
    APPLIED = "applied", "Applied"
    SCREENING = "screening", "Screening"
    OFFER = "offer", "Offer Received"
    REJECTED = "rejected", "Rejected"

status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
```

Benefits:
- `Application.Status.APPLIED` gives you `"applied"` — no magic strings
- `.choices` gives you the list of tuples Django needs for the field
- `get_status_display()` gives you the human-readable label ("Offer Received")
- IDE autocomplete works
- Easy to add new statuses without hunting for string literals

---

**Q: What is `select_related` and when did you use it?**

A: `select_related` performs a SQL JOIN to fetch related objects in a single query instead of separate queries per object (the N+1 problem).

In this project:
```python
Application.objects.filter(user=request.user).select_related("company")
```

Without `select_related`, if you have 20 applications and access `app.company.name` for each one, Django makes 21 queries (1 for applications + 20 for companies). With `select_related`, it's 1 query with a JOIN.

Use it for `ForeignKey` and `OneToOneField` relationships. For `ManyToManyField` use `prefetch_related` instead.

---

**Q: What is `annotate` and how did you use it?**

A: `annotate` adds a computed field to each object in a queryset using SQL aggregation — it runs in the database, not Python.

```python
Company.objects.filter(user=request.user).annotate(
    application_count=Count("applications")
)
```

This adds an `application_count` attribute to each `Company` object containing the count of related applications. It's done in a single SQL query. If you did it in Python, you'd need one query per company.

---

**Q: What is `unique_together` and where did you use it?**

A:
```python
class Meta:
    unique_together = ("name", "user")
```

This creates a database-level constraint that the combination of `name` and `user` must be unique. So the same user can't add "Google" twice, but two different users can both have "Google" as a company. It's enforced at the database level, not just in Python.

---

**Q: What is `on_delete=models.CASCADE` and what are the alternatives?**

A: `on_delete` defines what happens to child records when the parent is deleted:

- `CASCADE` — delete all related objects (delete user → delete all their applications)
- `PROTECT` — prevent deletion if related objects exist (raises `ProtectedError`)
- `SET_NULL` — set the FK to NULL (requires `null=True`)
- `SET_DEFAULT` — set to the field's default value
- `DO_NOTHING` — do nothing (can break database integrity)
- `RESTRICT` — like PROTECT but allows deletion if related objects will also be deleted via CASCADE

In this project I use `CASCADE` everywhere because it makes sense — deleting a user should delete all their data, and deleting an application should delete its contacts and interviews.

---

**Q: Explain the `days_since_applied` property.**

A:
```python
@property
def days_since_applied(self):
    return (timezone.now().date() - self.applied_date).days
```

This is a Python property (not a database field) that computes how many days have passed since the application was submitted. `timezone.now()` is timezone-aware (uses UTC as configured), `.date()` strips the time, and subtracting two dates gives a `timedelta` whose `.days` gives the integer.

In the serializer, I declare it as `serializers.IntegerField(read_only=True)` so DRF knows to include it in the response.

---

## 5. DJANGO REST FRAMEWORK

---

**Q: What is a ViewSet and how is it different from a regular View?**

A: A `ViewSet` combines all CRUD operations into one class. Instead of writing separate views for list, create, retrieve, update, delete — you write one `ModelViewSet` and DRF generates all the URL patterns via a Router.

```python
class ApplicationViewSet(viewsets.ModelViewSet):
    # Automatically gives you:
    # GET    /applications/        → list()
    # POST   /applications/        → create()
    # GET    /applications/{id}/   → retrieve()
    # PUT    /applications/{id}/   → update()
    # PATCH  /applications/{id}/   → partial_update()
    # DELETE /applications/{id}/   → destroy()
```

Plus I added custom actions:
```python
@action(detail=False, methods=["get"])
def dashboard(self, request):
    ...

@action(detail=True, methods=["patch"])
def update_status(self, request, pk=None):
    ...
```

`detail=False` means the URL is `/applications/dashboard/`. `detail=True` means `/applications/{id}/update_status/`.

---

**Q: What is the difference between a Serializer and ModelSerializer?**

A:
- `Serializer` — you define every field manually, full control
- `ModelSerializer` — automatically generates fields from the model, much less code

```python
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")
```

`"__all__"` includes every model field. `read_only_fields` prevents those fields from being set by the client. I also add computed fields like `application_count = serializers.IntegerField(read_only=True)` for annotated values.

---

**Q: Why do you have two serializers for Application — List and Detail?**

A: For performance. The list endpoint returns many applications and only needs summary data. The detail endpoint returns one application and can afford to include nested contacts and interviews.

```python
class ApplicationListSerializer(serializers.ModelSerializer):
    # Lightweight — no nested data
    company_name = serializers.CharField(source="company.name", read_only=True)
    interview_count = serializers.IntegerField(read_only=True)

class ApplicationDetailSerializer(serializers.ModelSerializer):
    # Full — includes nested contacts and interviews
    contacts = ContactSerializer(many=True, read_only=True)
    interviews = InterviewRoundSerializer(many=True, read_only=True)
```

In the ViewSet:
```python
def get_serializer_class(self):
    if self.action == "list":
        return ApplicationListSerializer
    return ApplicationDetailSerializer
```

This way a list of 100 applications doesn't serialize all their nested contacts and interviews.

---

**Q: What is `perform_create` and why override it?**

A: `perform_create` is called by DRF's `CreateModelMixin` after serializer validation, just before saving. I override it to automatically set the `user` field to the logged-in user:

```python
def perform_create(self, serializer):
    serializer.save(user=self.request.user)
```

This prevents users from creating applications for other users by passing a `user` ID in the request body. The user field is set server-side from the authenticated request, not from user input.

---

**Q: How does queryset filtering prevent users from seeing each other's data?**

A:
```python
def get_queryset(self):
    return Application.objects.filter(user=self.request.user)
```

By filtering on `user=request.user` in `get_queryset`, every operation — list, retrieve, update, delete — is automatically scoped to the logged-in user. If user A tries to access `/applications/5/` and application 5 belongs to user B, the queryset won't contain it and DRF returns 404. This is called object-level permission through queryset scoping.

---

**Q: What is `DjangoFilterBackend` and how did you use it?**

A: `DjangoFilterBackend` integrates `django-filter` with DRF to allow URL query parameter filtering:

```python
# filters.py
class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Application.Status.choices)
    applied_after = django_filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    company_name = django_filters.CharFilter(field_name="company__name", lookup_expr="icontains")
```

Now users can do:
```
GET /api/v1/applications/?status=applied&status=screening
GET /api/v1/applications/?applied_after=2024-01-01&company_name=google
```

`MultipleChoiceFilter` allows filtering by multiple statuses at once. `lookup_expr="icontains"` makes text search case-insensitive. `"gte"` means "greater than or equal to".

---

**Q: What is pagination and how is it configured?**

A:
```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
```

This automatically paginates all list endpoints. The response looks like:
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/applications/?page=2",
  "previous": null,
  "results": [...]
}
```

The client requests pages with `?page=2`. Page size is 20 by default. Without pagination, a user with 500 applications would get all 500 in one response — slow and memory-intensive.

---

**Q: What is `source` in a serializer field?**

A:
```python
company_name = serializers.CharField(source="company.name", read_only=True)
```

`source` tells the serializer where to get the value from. `"company.name"` traverses the `company` ForeignKey relationship and gets the `name` field. This lets you expose a flat field name (`company_name`) in the API response while the actual data comes from a related model.

---

## 6. AUTHENTICATION & JWT

---

**Q: What is JWT and how does it work?**

A: JWT (JSON Web Token) is a stateless authentication mechanism. A token contains three base64-encoded parts separated by dots:

1. **Header** — algorithm used (e.g., HS256)
2. **Payload** — data (user ID, expiry time)
3. **Signature** — HMAC of header+payload with the secret key

When a user logs in, the server creates a token signed with `SECRET_KEY`. On subsequent requests, the client sends the token in the `Authorization: Bearer <token>` header. The server verifies the signature — no database lookup needed.

**Access token** — short-lived (60 mins in this project). Used for API calls.
**Refresh token** — long-lived (7 days). Used only to get a new access token.

---

**Q: Why use JWT over Django's session-based auth?**

A: Session auth stores session data server-side (in DB or cache) and sends a session cookie to the browser. JWT is stateless — all auth info is in the token itself.

Advantages of JWT for a REST API:
- Stateless — server doesn't store sessions, scales horizontally easily
- Works across domains (no cookie issues)
- Perfect for mobile clients and SPAs
- Can be used by any client (mobile app, React, Postman)

Disadvantage: Can't invalidate a token before it expires (unless you maintain a blacklist — which `simplejwt` supports with `BLACKLIST_AFTER_ROTATION`).

---

**Q: What is token rotation and why did you enable it?**

A:
```python
SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

When a refresh token is used to get a new access token, Django issues a brand new refresh token and blacklists the old one. This means:
- If a refresh token is stolen, it can only be used once before it's invalidated
- Old refresh tokens cannot be reused
- Requires `djangorestframework-simplejwt`'s blacklist app to be installed

---

**Q: How does your logout work?**

A:
```python
class LogoutView(APIView):
    def post(self, request):
        token = RefreshToken(request.data["refresh"])
        token.blacklist()
```

The client sends their refresh token. We add it to the blacklist table in the database. The refresh token can never be used again. The access token will still work until it expires (60 mins) — for true immediate logout in high-security apps you'd keep an access token blacklist too, but that defeats the stateless benefit.

---

## 7. DJANGO SIGNALS

---

**Q: What are Django signals and what problem do they solve?**

A: Signals let decoupled applications notify each other when certain actions happen. They implement the Observer pattern.

Instead of:
```python
# Messy — mixing concerns in the view
def update_status(request, pk):
    app.status = new_status
    app.save()
    send_email(app)           # email logic in view
    create_notification(app)  # notification logic in view
    invalidate_cache(app)     # cache logic in view
```

With signals:
```python
# Clean — view only saves, everything else is decoupled
def update_status(request, pk):
    app.status = new_status
    app.save()   # signals fire automatically
```

The email, notification, and cache code lives in `signals.py` and reacts automatically whenever an Application is saved.

---

**Q: What is the difference between `pre_save` and `post_save`?**

A:
- `pre_save` — fires before `model.save()` executes. The record is NOT yet in the database.
- `post_save` — fires after `model.save()` completes. The record IS in the database.

In this project I use both:
```python
@receiver(pre_save, sender=Application)
def track_status_change(sender, instance, **kwargs):
    if instance.pk:
        old = Application.objects.get(pk=instance.pk)
        instance._previous_status = old.status  # capture old value before save

@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_status", None)
    if not created and previous != instance.status:
        # status actually changed — do something
        send_status_change_email.delay(instance.id, previous, instance.status)
```

I need `pre_save` to capture the old status before the update overwrites it in the database.

---

**Q: What is the `created` parameter in `post_save`?**

A: `created=True` when a new record is being inserted (INSERT). `created=False` when an existing record is being updated (UPDATE). This prevents the status-change logic from running on the initial creation of an application — when it's first created, there's no "previous status" to compare.

---

**Q: What is `@receiver` decorator?**

A:
```python
from django.dispatch import receiver
from django.db.models.signals import post_save

@receiver(post_save, sender=Application)
def my_handler(sender, instance, created, **kwargs):
    ...
```

`@receiver` connects the function to the signal. `sender=Application` means this handler only fires for `Application` model saves, not for every model. Without `sender`, the handler would fire for every model save in the entire project.

You must import signals in `apps.py` `ready()` method:
```python
def ready(self):
    import apps.jobs.signals  # noqa
```

Otherwise Django never loads the signal handlers.

---

**Q: What is a potential problem with signals and Celery?**

A: The signal fires inside the database transaction. If you dispatch a Celery task from the signal and the transaction rolls back (due to an error), the task has already been sent to the queue — but the data it tries to read doesn't exist in the database yet.

The fix is `transaction.on_commit()`:
```python
from django.db import transaction

@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    def dispatch():
        send_status_change_email.delay(instance.id)
    transaction.on_commit(dispatch)
```

This guarantees the Celery task only runs after the database transaction successfully commits.

---

## 8. CELERY & ASYNC TASKS

---

**Q: What is Celery and why use it?**

A: Celery is a distributed task queue. It lets you run code asynchronously — outside the HTTP request-response cycle.

Without Celery:
- User updates status → server sends email → user waits 2-3 seconds for email to send → response returned
- If email server is down, the entire request fails

With Celery:
- User updates status → task added to Redis queue → response returned immediately (< 100ms)
- Celery worker picks up the task in the background and sends the email
- If email fails, Celery can retry automatically

In this project Celery handles: welcome emails, status-change emails, interview reminders, and weekly summaries.

---

**Q: What is Redis's role in Celery?**

A: Redis serves as the **message broker** — the middleman between Django and Celery workers.

1. Django calls `.delay()` → serializes the task to JSON → pushes it to a Redis queue
2. Celery worker is constantly polling Redis
3. Worker picks up the task → deserializes → executes the function
4. Result (if needed) is stored back in Redis

Redis is also the **result backend** in this project (`CELERY_RESULT_BACKEND = REDIS_URL`), storing task results and states.

---

**Q: What is `@shared_task` and why use it instead of `@app.task`?**

A:
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    ...
```

`@shared_task` doesn't require a reference to the Celery app instance. This is important for reusable apps — the tasks file doesn't need to import the Celery app, avoiding circular imports. `@app.task` would require importing the `celery_app` object which creates tight coupling.

---

**Q: What is `bind=True` in a Celery task?**

A: `bind=True` passes the task instance as `self` (first argument). This gives you access to:
- `self.retry()` — retry the task with a delay
- `self.request.id` — the task ID
- `self.max_retries` — retry limit

```python
@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    try:
        # ... send email
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # retry after 60 seconds
```

Without `bind=True`, `self` wouldn't be available and you couldn't retry.

---

**Q: What is Celery Beat?**

A: Celery Beat is a scheduler — it sends tasks to the queue at defined intervals, like a cron job.

```python
app.conf.beat_schedule = {
    "send-interview-reminders-daily": {
        "task": "apps.tasks.email_tasks.send_interview_reminders",
        "schedule": crontab(hour=8, minute=0),  # Every day at 8:00 AM
    },
    "send-weekly-summary": {
        "task": "apps.tasks.email_tasks.send_weekly_summary",
        "schedule": crontab(day_of_week="monday", hour=9, minute=0),
    },
}
```

Beat is a separate process from the Celery worker. Beat puts tasks into the queue on schedule; workers execute them. You need both running.

---

**Q: How do you call a Celery task?**

A: Three ways:

```python
# 1. .delay() — simple async call
send_welcome_email.delay(user_id=1)

# 2. .apply_async() — with options
send_welcome_email.apply_async(args=[1], countdown=10, expires=3600)

# 3. Direct call (synchronous, bypasses Celery — for testing)
send_welcome_email(user_id=1)
```

In production I use `.delay()`. In tests I call the function directly to avoid needing a running Celery worker.

---

**Q: How did you test Celery tasks without running a worker?**

A:
```python
from unittest.mock import patch

@patch("apps.tasks.email_tasks.send_mail")
def test_interview_reminder_task(self, mock_send):
    InterviewRound.objects.create(...)
    result = send_interview_reminders()   # Call directly, not .delay()
    mock_send.assert_called_once()
```

I call the task function directly (synchronously) and mock `send_mail` so no actual email is sent. This tests the task logic without needing Redis or a Celery worker running.

---

## 9. DJANGO CHANNELS & WEBSOCKETS

---

**Q: What is Django Channels and what does it add to Django?**

A: Django is built on WSGI which is synchronous and request-response only. Django Channels extends Django to handle WebSockets, long-polling, and other asynchronous protocols using ASGI.

In this project, Channels powers real-time notifications — when an application status changes, the user's browser gets an instant push notification without polling.

---

**Q: What is ASGI vs WSGI?**

A:
- **WSGI** (Web Server Gateway Interface) — synchronous, one request at a time per connection, HTTP only
- **ASGI** (Asynchronous Server Gateway Interface) — asynchronous, handles long-lived connections, supports WebSockets, HTTP/2, etc.

```python
# asgi.py
application = ProtocolTypeRouter({
    "http": get_asgi_application(),        # Regular HTTP → Django
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)   # WebSocket → Channels consumer
    ),
})
```

HTTP requests still go to Django as normal. WebSocket connections go to Channels consumers.

---

**Q: What is a Consumer?**

A: A Consumer is the Channels equivalent of a Django view, but for WebSocket connections:

```python
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return
        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event))
```

`connect()` — called when client opens WebSocket. Authenticate and add to a group.
`disconnect()` — called when connection closes. Remove from group.
`send_notification()` — custom method that sends data to this specific client.

---

**Q: What is a Channel Layer and Channel Group?**

A: The Channel Layer is a pub-sub system backed by Redis. It lets different parts of the application communicate across process boundaries.

- **Channel** — a unique address for one WebSocket connection
- **Group** — a named set of channels. Broadcasting to a group sends to all members.

```python
# In utils.py — from Django signal handler (different process than WebSocket)
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f"notifications_{user.id}",      # Group name
    {"type": "send_notification", "title": "...", "message": "..."}
)
```

`type: "send_notification"` maps to the `send_notification` method on the consumer. The `type` key uses dots replaced with underscores to find the method.

---

**Q: Why use `async_to_sync`?**

A: Django signals are synchronous. Channels consumers are async. `async_to_sync` is a bridge from `asgiref` that lets synchronous code call async functions:

```python
from asgiref.sync import async_to_sync

async_to_sync(channel_layer.group_send)(...)
```

This blocks the sync code until the async function completes, safely calling async code from a sync context (like a Django signal handler).

---

## 10. REDIS & CACHING

---

**Q: How did you implement caching in this project?**

A: I cached the dashboard endpoint because it involves multiple aggregate queries and doesn't need to be real-time:

```python
@action(detail=False, methods=["get"])
def dashboard(self, request):
    cache_key = f"dashboard_{request.user.id}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    # ... expensive DB queries ...

    cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes
    return Response(data)
```

Per-user cache key ensures users only see their own data. 5-minute timeout prevents stale data from showing too long.

---

**Q: How do you invalidate the cache?**

A: When an application is updated (status change, new application created), I delete the user's dashboard cache:

```python
def perform_update(self, serializer):
    instance = serializer.save()
    cache.delete(f"dashboard_{self.request.user.id}")
```

Also in the signal:
```python
cache.delete(f"dashboard_{instance.user.id}")
```

This is "cache-aside" pattern — write to DB, invalidate cache. Next dashboard request rebuilds fresh data and re-caches it.

---

**Q: What are the different Django cache backends?**

A:
- `LocMemCache` — in-memory, per-process, for development/testing
- `FileBasedCache` — stores in filesystem
- `RedisCache` — production-grade, shared across processes/servers
- `DatabaseCache` — stores in DB table
- `Memcached` — alternative to Redis for caching

In this project I use `RedisCache`:
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
```

Redis is already running for Celery, so reusing it for cache saves infrastructure cost.

---

**Q: What is Redis used for in this project?**

A: Redis serves three roles:
1. **Celery message broker** — task queue between Django and Celery workers
2. **Celery result backend** — stores task execution results
3. **Django cache** — stores dashboard data with TTL
4. **Channels layer** — pub-sub for WebSocket group messaging

This is fine for development. In high-load production, you'd use separate Redis instances for each role.

---

## 11. DJANGO ADMIN

---

**Q: What customizations did you make to Django Admin?**

A: Several significant ones:

**1. Colored status column:**
```python
def colored_status(self, obj):
    colors = {"applied": "#3498db", "offer": "#27ae60", "rejected": "#e74c3c"}
    return format_html('<span style="color: {};">{}</span>', colors[obj.status], obj.get_status_display())
colored_status.short_description = "Status"
```

**2. Inline models** — view and edit contacts and interviews directly on the application page:
```python
class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0

class ApplicationAdmin(admin.ModelAdmin):
    inlines = [ContactInline, InterviewRoundInline]
```

**3. Bulk actions** — select multiple applications and mark them as rejected:
```python
@admin.action(description="Mark selected as Rejected")
def mark_rejected(self, request, queryset):
    queryset.update(status=Application.Status.REJECTED)
```

**4. `list_filter`, `search_fields`, `list_display`** — makes the admin usable for large datasets.

---

**Q: What is `format_html` and why use it instead of string formatting?**

A: `format_html` safely escapes HTML to prevent XSS attacks:

```python
# UNSAFE — XSS vulnerability
return f'<span style="color: {color};">{text}</span>'

# SAFE — format_html escapes the variables
return format_html('<span style="color: {};">{}</span>', color, text)
```

If `text` contained `<script>alert('xss')</script>`, `format_html` would escape it to `&lt;script&gt;...` making it harmless. Always use `format_html` when returning HTML from admin methods.

---

## 12. TESTING

---

**Q: What types of tests did you write?**

A:

**Model tests** — test model properties, constraints, string representations
**API tests** — test endpoints with `APIClient` (auth, CRUD, permissions)
**Signal tests** — verify signals fire and trigger the right actions
**Celery task tests** — call tasks directly, mock `send_mail`, verify behavior
**Permission tests** — verify unauthenticated requests get 401, cross-user access gets 404

---

**Q: What is `APIClient` and how is it different from Django's `TestClient`?**

A:
- `TestClient` — Django's built-in test client, works with views directly
- `APIClient` — DRF's test client, adds support for `force_authenticate()`, JSON content type, and JWT headers

```python
class ApplicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email="test@test.com", password="Pass123!")
        self.client.force_authenticate(user=self.user)
```

`force_authenticate()` bypasses JWT validation — you don't need to generate tokens in tests. You're testing the view logic, not the auth middleware.

---

**Q: What is `unittest.mock.patch` and how did you use it?**

A: `patch` temporarily replaces a real function with a `MagicMock` during a test:

```python
@patch("apps.tasks.email_tasks.send_mail")
def test_interview_reminder_task(self, mock_send):
    send_interview_reminders()
    mock_send.assert_called_once()
```

This replaces Django's `send_mail` function with a mock so no actual email is sent during tests. After the test, the real function is restored automatically. `mock_send.assert_called_once()` verifies the function was called exactly once.

---

**Q: How do you test that cross-user data access is prevented?**

A:
```python
def test_list_own_companies_only(self):
    other = CustomUser.objects.create_user(email="other@test.com", password="Pass!")
    Company.objects.create(name="OtherCo", user=other)
    Company.objects.create(name="MyCo", user=self.user)

    res = self.client.get(self.url)  # authenticated as self.user

    self.assertEqual(len(res.data["results"]), 1)          # Only sees 1 company
    self.assertEqual(res.data["results"][0]["name"], "MyCo")  # Only their own
```

This confirms the `get_queryset` filtering works correctly and user B's data is never exposed to user A.

---

**Q: What is `setUp` in Django tests?**

A: `setUp` runs before each individual test method. It sets up the initial state — database objects, authenticated client, etc. Each test gets a fresh setup because Django wraps each test in a database transaction that's rolled back after the test.

Using `setUpTestData` (class method) runs once for the entire test class and is faster, but requires all tests to treat the data as read-only.

---

## 13. SETTINGS & CONFIGURATION

---

**Q: What is `AUTH_USER_MODEL` and when must it be set?**

A:
```python
AUTH_USER_MODEL = "accounts.CustomUser"
```

This tells Django which model to use for authentication. It must be set **before running the first migration**. Django's built-in models (like `ForeignKey` to the user model) use `settings.AUTH_USER_MODEL` internally. If you change it after migrations exist, you'll have to reset the entire database or write a complex data migration.

Always use `settings.AUTH_USER_MODEL` or `get_user_model()` in your code instead of importing `CustomUser` directly — this avoids circular imports.

---

**Q: What is `INSTALLED_APPS` and what happens if you forget to add an app?**

A: `INSTALLED_APPS` tells Django which apps are active. If you forget to add an app:
- Its models won't be included in migrations
- Its admin registrations won't load
- Its signals won't be connected
- Template tags won't be found
- `AppConfig.ready()` won't run (signals won't fire)

I organize them as `DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS` for clarity.

---

**Q: What does `DEFAULT_AUTO_FIELD` do?**

A:
```python
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

This sets the default primary key field type for all models that don't explicitly define one. `BigAutoField` uses a 64-bit integer (up to 9.2 × 10^18) instead of the old default `AutoField` (32-bit, max ~2 billion). For a production app you should always use `BigAutoField` to avoid running out of IDs.

---

## 14. DOCKER & DEPLOYMENT

---

**Q: Explain your docker-compose setup.**

A: I have 5 services:

```yaml
services:
  db:      # PostgreSQL database
  redis:   # Redis for Celery + cache + Channels
  web:     # Django application server
  celery:  # Celery worker (processes tasks)
  celery-beat:  # Celery Beat (schedules periodic tasks)
```

All services share the same Docker network so they can communicate by service name (`db:5432`, `redis:6379`). That's why `DATABASE_URL=postgres://postgres:postgres@db:5432/jobtracker` uses `db` as the hostname — Docker DNS resolves it.

---

**Q: What is Gunicorn and why use it instead of `runserver`?**

A: `python manage.py runserver` is Django's development server — single-threaded, not optimized, not secure for production.

Gunicorn is a production WSGI server:
```dockerfile
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

`--workers 3` spawns 3 worker processes. The general formula is `2 * CPU_cores + 1`. Each worker handles requests independently, so you can handle multiple concurrent requests. Gunicorn also handles graceful shutdowns, worker timeouts, and logging properly.

---

**Q: What is WhiteNoise and why use it?**

A: WhiteNoise serves static files (CSS, JS, images) directly from Django/Gunicorn without needing a separate Nginx server for static files. In development this is fine. In production it serves files with proper caching headers and compression.

```python
# middleware
"whitenoise.middleware.WhiteNoiseMiddleware",

# settings
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

For very high traffic you'd still use a CDN or Nginx for static files, but WhiteNoise is perfect for most deployments.

---

## 15. SECURITY

---

**Q: What security measures are in this project?**

A:

**Authentication** — JWT tokens, blacklisting on logout
**Authorization** — `IsAuthenticated` on all endpoints, queryset scoping prevents cross-user access
**CORS** — `django-cors-headers` controls which origins can call the API (all in dev, restricted in prod)
**Password validation** — Django's built-in validators (minimum length, common passwords, similarity)
**Production settings** — HTTPS redirect, HSTS, XSS filter, X-Frame-Options: DENY, secure cookies
**`format_html`** — prevents XSS in admin
**`SECRET_KEY` in env** — never hardcoded, never committed to git
**`.env` in `.gitignore`** — secrets never pushed to GitHub

---

**Q: What is CORS and how does it work?**

A: CORS (Cross-Origin Resource Sharing) prevents malicious websites from making API calls on behalf of your users from their browser.

If your API is on `api.jobtracker.com` and your frontend is on `app.jobtracker.com`, the browser blocks cross-origin requests by default. `django-cors-headers` adds response headers:
```
Access-Control-Allow-Origin: https://app.jobtracker.com
```

In development I set `CORS_ALLOW_ALL_ORIGINS = True` for convenience. In production I'd set `CORS_ALLOWED_ORIGINS = ["https://app.jobtracker.com"]`.

---

**Q: What is CSRF and how does Django protect against it?**

A: CSRF (Cross-Site Request Forgery) — a malicious website tricks a logged-in user's browser into making unwanted requests to your API using their session cookie.

Django's `CsrfViewMiddleware` requires a CSRF token on state-changing requests (POST, PUT, DELETE). JWT-based APIs are inherently less vulnerable to CSRF because JWT tokens are sent in the `Authorization` header (which cross-site requests can't set), not cookies. DRF's JWT authentication doesn't use CSRF protection by default for this reason.

---

## 16. PERFORMANCE & SCALABILITY

---

**Q: What is the N+1 query problem and how did you avoid it?**

A: N+1 happens when you fetch N objects and then make 1 additional query per object to get related data.

```python
# N+1 — BAD
applications = Application.objects.filter(user=user)  # 1 query
for app in applications:
    print(app.company.name)  # 1 query per application = N queries
# Total: N+1 queries
```

Fix with `select_related`:
```python
# 1 query with JOIN
applications = Application.objects.filter(user=user).select_related("company")
for app in applications:
    print(app.company.name)  # No extra query — already loaded
```

I use `select_related("company")` in the ApplicationViewSet queryset and `select_related("application", "application__company")` in the InterviewRound queryset.

---

**Q: How would you scale this application?**

A:
1. **Multiple Gunicorn workers** — already configured (`--workers 3`)
2. **Multiple Celery workers** — run more worker processes/containers
3. **Database connection pooling** — use `pgBouncer` or `django-db-geventpool`
4. **Read replicas** — route read queries to replica DBs
5. **Redis cluster** — for high-availability Redis
6. **CDN** — serve static/media files from CloudFront or similar
7. **Horizontal scaling** — because JWT is stateless and Celery/Channels use Redis (shared state), you can run multiple Django containers behind a load balancer
8. **Database indexing** — add indexes on frequently filtered fields (`status`, `applied_date`, `user`)

---

**Q: What database indexes would you add?**

A:
```python
class Application(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),      # filter by user+status
            models.Index(fields=["user", "applied_date"]), # sort by date per user
            models.Index(fields=["company"]),              # filter by company
        ]
```

`user` + `status` is the most common query pattern (list my applications filtered by status). Without an index, PostgreSQL does a full table scan. With it, it uses the B-tree index — much faster at scale.

---

## 17. DATABASE & MIGRATIONS

---

**Q: What is a Django migration and what commands do you use?**

A: A migration is a Python file that describes a database schema change. Django tracks which migrations have been applied.

```bash
python manage.py makemigrations    # Detect model changes, create migration files
python manage.py migrate           # Apply pending migrations to the database
python manage.py showmigrations    # List all migrations and their status
python manage.py sqlmigrate jobs 0001  # Show the SQL a migration would run
python manage.py migrate jobs 0001     # Migrate to a specific migration (rollback)
```

Migration files should be committed to git so all team members and production environments run the same schema changes.

---

**Q: What is a data migration vs schema migration?**

A:
- **Schema migration** — changes the database structure (add column, create table, add index). Generated by `makemigrations`.
- **Data migration** — changes the data in existing tables (populate a new column, transform data). Written manually.

```python
# Data migration example
from django.db import migrations

def set_default_role(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    CustomUser.objects.filter(role="").update(role="user")

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(set_default_role, migrations.RunPython.noop),
    ]
```

`RunPython.noop` as the reverse function means the migration can't be reversed (no data to restore).

---

**Q: Why use PostgreSQL instead of SQLite?**

A: SQLite is a file-based database — great for development and testing but not for production:
- No concurrent writes (one write at a time)
- No network access (can't be on a separate server)
- Limited data types
- No full-text search

PostgreSQL is production-grade:
- Full ACID compliance with concurrent writes
- Advanced data types (JSONB, Arrays, UUID)
- Full-text search
- Row-level locking
- Used by most production Django applications
- Required for Django Channels' database layer and some ORM features

---

## 18. TRICKY / ADVANCED QUESTIONS

---

**Q: What happens if two users register with the same email simultaneously?**

A: Django's `email = models.EmailField(unique=True)` creates a `UNIQUE` constraint in PostgreSQL. If two requests arrive at the exact same millisecond, PostgreSQL's constraint enforcement ensures only one INSERT succeeds — the other gets an `IntegrityError`. DRF's serializer validates uniqueness before saving, but the database constraint is the ultimate safety net. This is why database constraints are essential — you can't rely on application-level checks alone for race conditions.

---

**Q: How does your dashboard handle concurrent requests?**

A:
```python
cached = cache.get(cache_key)
if cached:
    return Response(cached)
# ... compute data ...
cache.set(cache_key, data, timeout=300)
```

There's a race condition called "cache stampede" — if 100 requests hit simultaneously on a cache miss, all 100 compute the expensive queries before any has set the cache. For this project it's acceptable (low traffic). The production solution is "cache lock":

```python
with cache.lock(f"dashboard_lock_{user.id}"):
    cached = cache.get(cache_key)
    if not cached:
        # compute and set
```

Or use `django-cache-stampede` library.

---

**Q: If you had to add a "resume upload" feature, how would you design it?**

A: I'd add a `Document` model:
```python
class Document(TimeStampedModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="resumes/%Y/%m/")
    version = models.CharField(max_length=50)
    file_type = models.CharField(choices=[("resume", "Resume"), ("cover_letter", "Cover Letter")])
```

In production, files shouldn't be stored on the Django server — use `django-storages` with S3:
```python
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
```

Files go directly to S3, Django stores only the S3 key. Return pre-signed S3 URLs for secure, time-limited downloads.

---

**Q: How would you add rate limiting to the API?**

A: Use `django-ratelimit` or DRF's throttling:
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/hour",    # Unauthenticated
        "user": "1000/day",   # Authenticated
    }
}
```

For the login endpoint specifically I'd use stricter limits to prevent brute-force attacks:
```python
class LoginRateThrottle(AnonRateThrottle):
    rate = "5/minute"
```

---

**Q: What would you change if you had to make this multi-tenant (SaaS)?**

A: Instead of each user owning their own data, I'd add an `Organization` model:
- Users belong to Organizations (ManyToMany with role: owner/admin/member)
- Companies and Applications belong to Organizations, not individual Users
- All querysets filter on `organization` instead of `user`
- Middleware reads the organization from the subdomain (`acme.jobtracker.com`) or JWT claim
- Each organization gets its own Celery queue priority level

This is the "shared database, shared schema" multi-tenancy model. For stronger isolation you'd use row-level security in PostgreSQL or separate schemas per tenant.

---

**Q: What is `__str__` and why is it important?**

A:
```python
def __str__(self):
    return f"{self.job_title} at {self.company.name} [{self.status}]"
```

`__str__` defines the human-readable string representation of a model instance. It's used:
- In Django Admin list views — shown in columns and dropdowns
- In Django shell — `print(application)` shows something meaningful
- In error messages and logs
- In `ForeignKey` dropdown widgets in forms

Without it, you'd see `Application object (1)` everywhere in admin.

---

**Q: What is `related_name` and when is it important?**

A:
```python
company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="applications")
```

`related_name` sets the name of the reverse relation from `Company` back to `Application`. Without it, Django uses `application_set` by default.

With `related_name="applications"`:
```python
company.applications.all()          # Get all applications for a company
company.applications.count()        # Count
company.applications.filter(status="offer")  # Filter
```

It's also required when you have two ForeignKeys to the same model on one model — Django would throw an error about conflicting reverse accessors without distinct `related_name` values.

---

**Q: What is `AppConfig.ready()` and what do you put in it?**

A:
```python
class JobsConfig(AppConfig):
    name = "apps.jobs"

    def ready(self):
        import apps.jobs.signals  # noqa
```

`ready()` is called once when Django has fully loaded all apps. It's the correct place to:
- Import signal handlers (so they get connected to signals)
- Register custom checks
- Start background threads

If you import signals at module level or in `models.py`, you risk circular import errors. `ready()` is guaranteed to run after all models are loaded.

---

*Built by Rama Bharti — Headstarter AI Fellowship*
*This document covers every major concept in the job-tracker-django project for technical interviews.*

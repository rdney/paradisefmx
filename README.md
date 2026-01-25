# Paradise FMX

Church facility management system. Dutch-first, senior-friendly UI.

## Features

- Repair request submission (anonymous or logged-in)
- Facilities dashboard for triage and assignment
- Asset tracking with categories and status
- Work log / timeline for each request
- Bilingual: Dutch (default) and English
- Large fonts, high contrast, accessible

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Compile translations
python manage.py compilemessages

# Run server
python manage.py runserver
```

## Initial Configuration

### Create Groups

In Django admin (`/admin/`), create these groups:

1. **Aanvragers** (Requesters)
   - View own requests

2. **Facilitair** (Facilities)
   - View all requests
   - Triage and assign
   - View assets

3. **Beheerders** (Admins)
   - Full access

### Create Locations

Add locations via admin before users can submit requests:
- Kerkzaal
- Foyer
- Keuken
- Kantoor
- etc.

### Email Configuration

Set environment variables:

```bash
# Development (console output)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Production
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@example.com
FACILITIES_INBOX_EMAIL=facilities@example.com
```

## Translations

Update translations:

```bash
# Extract messages
python manage.py makemessages -l nl -l en

# Edit .po files in locale/

# Compile
python manage.py compilemessages
```

## Routes

| Path | Description |
|------|-------------|
| `/` | Home |
| `/requests/new/` | Submit repair request |
| `/requests/dashboard/` | Facilities dashboard |
| `/requests/` | Request list |
| `/requests/<id>/` | Request detail |
| `/assets/` | Asset list |
| `/assets/<id>/` | Asset detail |
| `/account/login/` | Login |
| `/admin/` | Django admin |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev key | Django secret key |
| `DEBUG` | True | Debug mode |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | Comma-separated hosts |
| `DATABASE_URL` | - | Database URL (optional) |
| `FACILITIES_INBOX_EMAIL` | facilities@paradisefmx.local | Email for notifications |

## Tests

```bash
python manage.py test
```

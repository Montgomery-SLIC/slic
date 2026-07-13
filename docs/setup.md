# Development Setup

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- A `.env` file (copy from `.env.example`)

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `BLIND_INDEX_KEY` | Yes | 32-byte hex key for email HMAC lookups |
| `FIELD_ENCRYPTION_KEY` | Yes | Fernet key for encrypting PII fields |
| `RECAPTCHA_PUBLIC_KEY` | No | Google reCAPTCHA v2 site key (participant home page) |
| `RECAPTCHA_PRIVATE_KEY` | No | Google reCAPTCHA v2 secret key |
| `ADMIN_NAME` | No | Name for Django error email recipient |
| `ADMIN_EMAIL` | No | Email for Django error email recipient |
| `DB_NAME` | No | Database name (default: `slic_django_dev`) |
| `DB_USER` | No | Database user (default: `postgres`) |
| `DB_PASSWORD` | No | Database password |
| `DB_HOST` | No | Database host (default: `localhost`) |
| `DB_PORT` | No | Database port (default: `5432`) |

### Generating keys

```bash
# BLIND_INDEX_KEY - 32 random bytes as hex
python -c "import secrets; print(secrets.token_hex(32))"

# FIELD_ENCRYPTION_KEY - Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY - Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## First-time setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in values
cp .env.example .env

# Create the database
createdb slic_django_dev

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

## Creating a researcher account

Researcher registration requires an invitation code. Generate one as an admin:

1. Sign in at `/accounts/login/` with your superuser credentials.
2. Go to **Admin tools → Invitations → New invitation**.
3. Copy the code and use it on the registration page (`/accounts/signup/`).

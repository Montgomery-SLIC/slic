# Architecture

## Overview

SLIC is a two-flow web application:

1. **Researcher flow** - authenticated users create and manage experiments, upload audio, and download results.
2. **Participant flow** - unauthenticated users access a public slug URL, complete tasks in order, and submit responses.

## Apps

| App | Purpose |
|-----|---------|
| `accounts` | Custom user model, authentication backend, researcher invitations, profile management |
| `experiments` | Experiment CRUD, publishing, XLSX result generation |
| `tasks` | Multi-table inheritance task model (question, sample, listening, click, intermediate screen) |
| `responses` | Participant session, click-event XHR, EAF file parsing |

## Authentication

Authentication is handled by **django-allauth** with a custom backend (`accounts.backends.HMACEmailBackend`) that overrides allauth's default email lookup.

### Why a custom backend?

The user's email address is stored encrypted (`email_ciphertext`) with a separate HMAC blind index (`email_bidx`) for lookups. Allauth's default `filter_users_by_email` queries `email=<plaintext>`, which never matches. The custom backend calls `User.objects.get_by_natural_key(email)` instead, which computes the HMAC and queries `email_bidx`.

```
Login request
    │
    ▼
HMACEmailBackend._authenticate_by_email()
    │  computes HMAC(email) → email_bidx
    ▼
UserManager.get_by_natural_key()
    │  SELECT WHERE email_bidx = <hmac>
    ▼
user.check_password()
```

**Key settings:**

```python
ACCOUNT_USER_MODEL_EMAIL_FIELD = None   # prevents allauth touching email_bidx directly
AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.HMACEmailBackend',
]
```

## User Model

`accounts.models.User` extends `AbstractBaseUser`. PII fields are stored in `EncryptedTextField` columns (suffix `_ciphertext`). Each encrypted field has a Python property that transparently reads/writes it:

```python
user.email          # reads email_ciphertext
user.email = '…'   # writes email_ciphertext AND recomputes email_bidx
```

The `BLIND_INDEX_KEY` (32-byte hex) and `FIELD_ENCRYPTION_KEY` (Fernet key) must be set in the environment.

## Task Model

Tasks use Django's concrete multi-table inheritance. The base `Task` model is owned by exactly one of `Experiment` or `SampleTask` (enforced by a `CheckConstraint`).

- **Top-level tasks** - owned by an `Experiment`.
- **Sub-tasks** - owned by a `SampleTask` (e.g. click tasks and question tasks nested inside a sample).

Task types: `QuestionTask`, `SampleTask`, `ListeningTask`, `ClickTask`, `IntermediateScreenTask`.

## Frontend

Static assets live in `static/`. The base template (`templates/base.html`) loads:

- Bootstrap 4.6 (CDN)
- Font Awesome 5 (CDN)
- Select2 4.1 (CDN)
- **htmx 1.9.12** (CDN) - CSRF header wired via `hx-headers` on `<body>`
- **Alpine.js 3.14.1** (CDN, `defer`) - used for flash message dismissal

Flash messages use Alpine's `x-show` / `x-transition` and Bootstrap alert classes. Error → `alert-danger`, success → `alert-success`.

## Media Files

Researcher-uploaded audio files are stored under `MEDIA_ROOT`. In production, Nginx serves them via `X-Accel-Redirect` (the Django view sets the header; Nginx intercepts and streams the file). In development, Django serves them directly (`X_ACCEL_REDIRECT = False`).

## Authorization

Object-level permissions use the **rules** library (`accounts/rules.py`, `experiments/rules.py`, `tasks/rules.py`). Admin-only views use `AdminRequiredMixin` which checks `user.admin`.

# Deployment

The application is deployed on a university VM behind Nginx, using Gunicorn as the WSGI server and systemd for process management.

## Stack

```
Internet → Nginx → Gunicorn (WSGI) → Django
                       │
                   PostgreSQL
```

Static files are served directly by Nginx (WhiteNoise collects them into `STATIC_ROOT`).
Media files (researcher audio uploads) are served by Nginx via `X-Accel-Redirect`.

## Files

| File | Purpose |
|------|---------|
| `nginx_django_production.conf` | Nginx server block for production |
| `nginx_django_staging.conf` | Nginx server block for staging |
| `gunicorn_prod.conf.py` | Gunicorn config (workers, bind, logging) |
| `slic_production.service` | systemd unit for production |
| `slic_staging.service` | systemd unit for staging |

## Environment

Production reads from `/etc/slic.env` (or the path set in the systemd unit's `EnvironmentFile`). All the variables in [setup.md](setup.md#environment-variables) apply, plus:

| Variable | Production value |
|----------|-----------------|
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | The VM's hostname / domain |
| `STATIC_ROOT` | Absolute path to static file output dir |
| `MEDIA_ROOT` | Absolute path to uploaded file storage |
| `X_ACCEL_REDIRECT` | `True` |

## uv installation (once, on the VM)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Deployment steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Install any new dependencies
uv sync

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Apply migrations
python manage.py migrate

# 6. Restart the application service
sudo systemctl restart slic_production
```

## Gunicorn configuration

Both configs set `workers = (2 x CPU cores) + 1`, `timeout = 120`, and log to `/var/log/slic/`. The log directory must exist and be writable by the service user before starting.

| | Staging (`gunicorn.conf.py`) | Production (`gunicorn_prod.conf.py`) |
|-|------------------------------|--------------------------------------|
| Bind | `127.0.0.1:9294` | `127.0.0.1:9295` |
| Access log | `/var/log/slic/access.log` | `/var/log/slic/access_prod.log` |
| Error log | `/var/log/slic/error.log` | `/var/log/slic/error_prod.log` |
| Log level | `info` | `warning` |

Django itself also logs warnings and above to `/var/log/slic/django.log` (production only, configured in `slic/settings/production.py`).

## Nginx configuration

The production Nginx config:

1. Redirects HTTP → HTTPS.
2. Serves `/static/` from `STATIC_ROOT`.
3. Serves `/media/` via `internal` location (Nginx honours the `X-Accel-Redirect` header set by Django).
4. Proxies everything else to the Gunicorn socket.

## Database backups

Use `pg_dump` on a cron schedule:

```bash
pg_dump slic_production | gzip > /backups/slic_$(date +%Y%m%d).sql.gz
```

Keep the `BLIND_INDEX_KEY` and `FIELD_ENCRYPTION_KEY` backed up separately and securely - without them, the encrypted columns in a backup cannot be decrypted.

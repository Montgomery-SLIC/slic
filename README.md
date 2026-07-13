# SLIC - Salient Language In Context

A Django web application for running audio perception experiments. Researchers build experiments from audio samples, click tasks, and question pages. Participants complete them via a public URL with no account required. Results export as XLSX.

Live site: https://slic.shef.ac.uk

## Stack

- Python 3.12, Django 4.2, PostgreSQL 14+
- Gunicorn + Nginx (production)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in values
python manage.py migrate
python manage.py runserver
```

App runs at http://localhost:8000. Researcher accounts require an invitation code - generate one via the admin panel.

## Docs

- [Setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [User guide](docs/USER_DOCUMENTATION.md)

## Contact

Chris Montgomery - <c.montgomery@sheffield.ac.uk>, The University of Sheffield.

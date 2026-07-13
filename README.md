# SLIC - Salient Language In Context

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?logo=postgresql&logoColor=white)
[![Tests](https://github.com/Montgomery-SLIC/slic/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Montgomery-SLIC/slic/actions/workflows/test.yml)

A Django web application for running audio perception experiments. Researchers build experiments from audio samples, click tasks, and question pages. Participants complete them via a public URL with no account required. Results export as XLSX.

Live site: https://slic.shef.ac.uk

## Stack

- Python 3.12, Django 4.2, PostgreSQL 14+
- Gunicorn + Nginx (production)
- PII encrypted at rest (Fernet), HMAC blind index for email lookups

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## License

SLIC is free to use for non-commercial research purposes. See [LICENSE](LICENSE) for full terms. The companion Praat scripts are distributed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.html).

## Contact

Dr Chris Montgomery - <c.montgomery@sheffield.ac.uk>, The University of Sheffield.

# Rulio
[![test badge](https://github.com/Uninett/Argus/actions/workflows/python.yml/badge.svg)](https://github.com/Uninett/Rulio/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/main/graph/badge.svg)]([https://codecov.io/gh/Uninett/Argus](https://app.codecov.io/gh/Uninett/Rulio/tree/main/src%2Fbackend))
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A simple vendor agnostic web interface to generate router ACLs, powered by the [Aerleon](https://github.com/aerleon/aerleon) project.

## Prerequisites 

Rulio requires:

- Django verion 5.0++
- Django-ninja version 1.1.0++
- pytest 7.0.0++
- psycopg2 2.9.0++
- aerleon 0.1.0++
- pytest-django 4.0.0++
- pytest-cov 7.0.0++

## Set up a virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r src/requirements.txt
```

## Set up the project locally

Firstly, set up a .env file with credentials for the database and the admin user for the instance, required fields are:

- `DATABASE_NAME`,
- `DATABASE_USER`,
- `DATABASE_PASS`,
- `SECRET_KEY`,
- `DJANGO_SUPERUSER_USERNAME`,
- `DJANGO_SUPERUSER_EMAIL`,
- `DJANGO_SUPERUSER_PASSWORD`,

Then, build the docker container,

```bash
cd src
sudo docker compose up --build
```


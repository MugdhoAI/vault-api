# Vault API

A production grade REST API for secure data management, built with FastAPI and PostgreSQL.

Vault provides authenticated users with a private space for storing secrets. Passwords are protected with Argon2, access is controlled with JWT tokens, and secret values are encrypted before they are stored in PostgreSQL.

## What it demonstrates

Vault is built as a small backend system rather than a simple CRUD example. The project focuses on authentication, authorization, encrypted persistence, asynchronous database access, validation, testing, Docker based development, and continuous integration.

## Stack

Python 3.12
FastAPI
PostgreSQL
SQLAlchemy 2
Pydantic
Argon2
JWT
Fernet encryption
pytest
Docker
GitHub Actions

## API

`GET /health` checks service availability.

`POST /auth/register` creates a user account and returns an access token.

`POST /auth/token` authenticates an existing user.

`POST /secrets` stores an encrypted secret for the authenticated user.

`GET /secrets` lists the authenticated user's secrets.

`GET /secrets/{secret_id}` returns one secret owned by the authenticated user.

`PATCH /secrets/{secret_id}` updates a secret.

`DELETE /secrets/{secret_id}` removes a secret.

FastAPI also provides interactive API documentation at `/docs` while the application is running.

## Security model

Passwords are never stored directly. They are hashed with Argon2.

Secret values are encrypted before database persistence. The encryption key is supplied through the environment and is not part of the application source.

Every secret query is scoped to the authenticated user's ID. A valid token alone does not grant access to another user's records.

The development Docker configuration contains a local encryption key only to make the project immediately runnable. Production deployments should provide their own secret values through a proper secret manager or environment configuration.

## Run locally

Install the development dependencies:

```bash
python -m venv .venv
pip install -e ".[dev]"
```

Start PostgreSQL and the API with Docker:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

Open `http://localhost:8000/docs` to use the interactive API documentation.

For a non Docker setup, copy `.env.example` to `.env`, provide a PostgreSQL connection string, generate a Fernet encryption key, and start the application with:

```bash
uvicorn app.main:app --reload
```

Generate an encryption key with:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Testing

Run the test suite with:

```bash
pytest
```

Static checks use Ruff:

```bash
ruff check .
```

GitHub Actions runs both checks against a real PostgreSQL service for every push to `main` and every pull request.

## Project structure

```text
app/
  config.py       Application configuration
  crypto.py       Secret encryption and decryption
  db.py           Async SQLAlchemy setup
  main.py         API routes and authentication flow
  models.py       Database models
  schemas.py      Request and response validation
  security.py     Password hashing and JWT handling

tests/
  test_health.py
  test_security.py

Dockerfile
docker-compose.yml
pyproject.toml
```

## Current scope

Vault currently provides the core service layer for authenticated secret storage. Database schema creation is handled during application startup for this first version.

The next engineering stages can introduce migration management, rate limiting, audit logging, refresh tokens, stronger deployment configuration, and broader integration coverage.

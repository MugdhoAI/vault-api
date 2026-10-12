# Vault API

A FastAPI REST API for authenticated secret storage, using PostgreSQL, Argon2 password hashing, JWT authentication, and Fernet encryption.

This project demonstrates backend engineering fundamentals through an asynchronous API, owner-scoped data access, request validation, integration tests, Docker based development, and continuous integration.

## What it demonstrates

* User registration and authentication
* Authorization and per-user data isolation
* Encryption of secret values before database persistence
* Asynchronous database access with SQLAlchemy
* Request validation and predictable API errors
* PostgreSQL-backed integration testing
* Containerized local development and CI

## Stack

* Python 3.12
* FastAPI
* PostgreSQL
* SQLAlchemy 2
* Pydantic
* Argon2
* JWT
* Fernet encryption
* pytest
* Docker
* GitHub Actions

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Check service and database availability |
| POST | `/auth/register` | Create a user and return an access token |
| POST | `/auth/token` | Authenticate an existing user |
| POST | `/secrets` | Store an encrypted secret |
| GET | `/secrets` | List the authenticated user's secrets |
| GET | `/secrets/{secret_id}` | Return one secret owned by the authenticated user |
| PATCH | `/secrets/{secret_id}` | Update a secret |
| DELETE | `/secrets/{secret_id}` | Delete a secret |

FastAPI exposes interactive API documentation at `/docs` while the application is running.

## Security model

Passwords are hashed with Argon2 rather than stored as plain text. Secret values are encrypted before they are persisted to PostgreSQL. The application scopes secret queries to the authenticated user's ID, and does not grant access to another user's records just because a valid token is supplied.

The API decrypts a secret when returning it to its authenticated owner. This is server-side encryption, not end-to-end encryption.

The Docker Compose configuration contains credentials and an encryption key intended only for local development. Do not reuse these values in a deployed environment. Use unique secrets supplied through an appropriate secret manager or deployment configuration.

The encryption key is required to decrypt stored values. Losing it can make those values unrecoverable. This version does not provide an encryption key rotation workflow.

## Run locally

Create a virtual environment and install the development dependencies:

```bash
python -m venv .venv
pip install -e ".[dev]"
```

Start PostgreSQL and the API with Docker:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Open `http://localhost:8000/docs` for the interactive API documentation.

For a non-Docker setup, copy `.env.example` to `.env`, provide a PostgreSQL connection string and a generated Fernet key, then run:

```bash
uvicorn app.main:app --reload
```

Generate a Fernet key with:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Testing

Run the test suite:

```bash
pytest
```

Run static checks with Ruff:

```bash
ruff check .
```

Tests cover password hashing, token handling, configuration validation, duplicate registration, invalid credentials, database health, secret CRUD operations, owner isolation, and request schema validation. GitHub Actions runs Ruff and the PostgreSQL-backed test suite for pushes to `main` and pull requests.

## Current limitations

**This project is not production ready.** It is a learning and portfolio project that demonstrates a core authenticated secret storage API. A passing test suite does not establish production readiness.

Known gaps include:

* Database tables are created at application startup. There is no versioned migration workflow yet.
* Authentication endpoints do not have rate limiting or brute-force protection.
* Security-sensitive actions are not recorded in an audit log.
* Encryption key rotation and recovery procedures are not implemented.
* Production deployment hardening, including TLS termination, operational monitoring, backup and restore validation, and deployment-specific secret management, has not been established by this repository.

These are follow-up engineering requirements, not implemented features. They should be addressed and tested before considering a real deployment with sensitive data.

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
  test_auth.py
  test_config.py
  test_health.py
  test_schema_validation.py
  test_security.py
  test_secrets.py

Dockerfile
docker-compose.yml
pyproject.toml
```

## License

MIT

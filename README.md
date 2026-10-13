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

Successful secret creation, listing, retrieval, updates, and deletion are recorded in `audit_events` with the action, user ID, secret ID when applicable, and timestamp. Secret values are not included in these events. Authentication attempts are not currently audited.

The Docker Compose configuration contains credentials and an encryption key intended only for local development. Do not reuse these values in a deployed environment. Use unique secrets supplied through an appropriate secret manager or deployment configuration.

The encryption key is required to decrypt stored values. Losing all keys that can decrypt existing values can make those values unrecoverable. Back up the database and key material before rotating keys.

### Rotate the encryption key

1. Back up the database and securely preserve the current key.
2. Generate a new Fernet key and set it as `ENCRYPTION_KEY`.
3. Set `ENCRYPTION_KEY_PREVIOUS` to the old key. Multiple previous keys can be comma separated.
4. In a maintenance window, run `python scripts/rotate_encryption_key.py` once. The command re-encrypts stored values in a transaction using the new primary key.
5. Verify that stored values can be retrieved, then remove the old key from `ENCRYPTION_KEY_PREVIOUS` and restart the application.

Do not remove the previous key before the rotation command completes successfully. Keep the backup until verification is complete.

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

For a non-Docker setup, PostgreSQL must be running separately. Copy `.env.example` to `.env`, configure the connection string and generated secrets, then apply the database migrations before starting the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

New Docker containers apply migrations before the API starts. The application no longer creates tables automatically at startup.

If you have a database created by an older version that used automatic table creation, back it up first. Do not run the initial migration against tables that already exist. After confirming that the existing schema exactly matches the initial migration, mark it as migrated with `alembic stamp head`; otherwise, create a fresh database and migrate it.

Generate a Fernet key with:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Testing

Run the test suite against a dedicated PostgreSQL test database:

```bash
pytest
```

The test session applies pending Alembic migrations before running integration tests. Do not point the test suite at a database containing data you need to preserve.

Run static checks with Ruff:

```bash
ruff check .
```

Tests cover password hashing, token handling, configuration validation, duplicate registration, invalid credentials, database health, secret CRUD operations, owner isolation, and request schema validation. GitHub Actions runs Ruff and the PostgreSQL-backed test suite for pushes to `main` and pull requests.

## Current limitations

**This project is not production ready.** It is a learning and portfolio project that demonstrates a core authenticated secret storage API. A passing test suite does not establish production readiness.

Known gaps include:

* Authentication endpoints do not have rate limiting or brute-force protection.
* Secret lifecycle actions are recorded in an audit log, but authentication attempts are not.
* Key rotation is an operator run procedure. Automated key recovery and external key management are not provided.
* Production deployment hardening, including TLS termination, operational monitoring, backup and restore validation, and deployment-specific secret management, has not been established by this repository.

The audit log records action names, user IDs, secret IDs, and timestamps. It does not store secret values. These remaining gaps should be addressed and tested before considering a real deployment with sensitive data.

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
alembic.ini
migrations/
docker-compose.yml
pyproject.toml
```

## License

MIT

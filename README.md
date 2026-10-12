# Vault API

A secure REST API for storing and managing secrets with FastAPI and PostgreSQL.

Vault provides authenticated users with a private space for their secrets. Passwords are protected with Argon2, access is controlled with JWT tokens, and secret values are encrypted before they are stored in PostgreSQL.

## What it demonstrates

This project is built as a small backend system rather than a basic CRUD example.

It focuses on:

* Authentication and authorization
* Encrypted persistence
* Asynchronous database access
* Input validation
* Integration testing
* Docker based development
* Continuous integration

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

FastAPI also provides interactive API documentation at `/docs` while the application is running.

## Security model

Passwords are never stored directly. They are hashed with Argon2.

Secret values are encrypted before database persistence. The encryption key comes from the environment and is not part of the application source.

Every secret query is scoped to the authenticated user's ID. A valid token does not grant access to another user's records.

The development Docker configuration includes a local encryption key so the project can run immediately. Production deployments should provide their own secrets through appropriate environment configuration or a secret manager.

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

The API will be available at `http://localhost:8000`.

Open `http://localhost:8000/docs` for the interactive API documentation.

For a non Docker setup, copy `.env.example` to `.env`, provide a PostgreSQL connection string, generate a Fernet encryption key, and start the application:

```bash
uvicorn app.main:app --reload
```

Generate an encryption key with:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## Testing

Run the complete test suite:

```bash
pytest
```

Static checks use Ruff:

```bash
ruff check .
```

The test suite covers password hashing, token handling, production configuration validation, duplicate registration, invalid credentials, the database health check, secret creation, retrieval, update, deletion, and access isolation between users.

GitHub Actions runs the test suite against a real PostgreSQL service for every push to `main` and every pull request.

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
  test_security.py
  test_secrets.py

Dockerfile
docker-compose.yml
pyproject.toml
```

## Current scope

Vault currently provides the core service layer for authenticated secret storage. Database schema creation happens during application startup in this first version.

Future engineering work could introduce migration management, rate limiting, audit logging, refresh tokens, stronger deployment configuration, and additional integration coverage.

## License

MIT

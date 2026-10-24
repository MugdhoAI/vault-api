from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.crypto import decrypt_value, encrypt_value
from app.db import engine, get_session
from app.models import AuditEvent, Secret, User
from app.schemas import SecretCreate, SecretRead, SecretUpdate, Token, UserCreate
from app.security import create_access_token, decode_subject, hash_password, verify_password


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await engine.dispose()


settings = get_settings()
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.rate_limit_storage_uri)
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def prevent_sensitive_response_caching(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/secrets" or path.startswith(("/auth/", "/secrets/")):
        response.headers["Cache-Control"] = "no-store"
    return response


bearer_scheme = HTTPBearer(auto_error=False)
Session = Annotated[AsyncSession, Depends(get_session)]
# Keep the password verification cost similar for unknown and existing accounts.
DUMMY_PASSWORD_HASH = hash_password("vault-api-dummy-password-not-for-login")


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.auth_rate_limit)
async def register(request: Request, data: UserCreate, session: Session) -> Token:
    existing = await session.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")

    password_hash = await run_in_threadpool(hash_password, data.password)
    user = User(email=data.email, password_hash=password_hash)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from exc

    return Token(access_token=create_access_token(data.email))


@app.post("/auth/token", response_model=Token)
@limiter.limit(settings.auth_rate_limit)
async def login(request: Request, data: UserCreate, session: Session) -> Token:
    user = await session.scalar(select(User).where(User.email == data.email))
    password_hash_to_check = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_matches = await run_in_threadpool(
        verify_password,
        data.password,
        password_hash_to_check,
    )
    if user is None or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.email))


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Session,
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = decode_subject(credentials.credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def record_audit_event(
    session: AsyncSession,
    user_id: int,
    action: str,
    secret_id: int | None = None,
) -> None:
    session.add(AuditEvent(user_id=user_id, action=action, secret_id=secret_id))


def present_secret(secret: Secret) -> SecretRead:
    try:
        value = decrypt_value(secret.value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored secret could not be decrypted",
        ) from exc

    return SecretRead.model_validate(
        {"id": secret.id, "name": secret.name, "value": value,
         "created_at": secret.created_at, "updated_at": secret.updated_at}
    )


@app.post("/secrets", response_model=SecretRead, status_code=status.HTTP_201_CREATED)
async def create_secret(data: SecretCreate, user: Annotated[User, Depends(current_user)], session: Session) -> SecretRead:
    secret = Secret(owner_id=user.id, name=data.name, value=encrypt_value(data.value))
    session.add(secret)
    await session.flush()
    record_audit_event(session, user.id, "secret.create", secret.id)
    await session.commit()
    await session.refresh(secret)
    return present_secret(secret)


@app.get("/secrets", response_model=list[SecretRead])
async def list_secrets(user: Annotated[User, Depends(current_user)], session: Session) -> list[SecretRead]:
    result = await session.scalars(select(Secret).where(Secret.owner_id == user.id).order_by(Secret.id))
    secrets = [present_secret(secret) for secret in result]
    record_audit_event(session, user.id, "secret.list")
    await session.commit()
    return secrets


@app.get("/secrets/{secret_id}", response_model=SecretRead)
async def get_secret(secret_id: int, user: Annotated[User, Depends(current_user)], session: Session) -> SecretRead:
    secret = await session.scalar(select(Secret).where(Secret.id == secret_id, Secret.owner_id == user.id))
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    response = present_secret(secret)
    record_audit_event(session, user.id, "secret.read", secret.id)
    await session.commit()
    return response


@app.patch("/secrets/{secret_id}", response_model=SecretRead)
async def update_secret(secret_id: int, data: SecretUpdate, user: Annotated[User, Depends(current_user)], session: Session) -> SecretRead:
    secret = await session.scalar(select(Secret).where(Secret.id == secret_id, Secret.owner_id == user.id))
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    if data.name is not None:
        secret.name = data.name
    if data.value is not None:
        secret.value = encrypt_value(data.value)
    record_audit_event(session, user.id, "secret.update", secret.id)
    await session.commit()
    await session.refresh(secret)
    return present_secret(secret)


@app.delete("/secrets/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(secret_id: int, user: Annotated[User, Depends(current_user)], session: Session) -> None:
    secret = await session.scalar(select(Secret).where(Secret.id == secret_id, Secret.owner_id == user.id))
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    record_audit_event(session, user.id, "secret.delete", secret.id)
    await session.delete(secret)
    await session.commit()

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import decrypt_value, encrypt_value
from app.db import Base, engine, get_session
from app.models import Secret, User
from app.schemas import SecretCreate, SecretRead, Token, UserCreate
from app.security import create_access_token, decode_subject, hash_password, verify_password

app = FastAPI(title=get_settings().app_name, version="0.1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

Session = Annotated[AsyncSession, Depends(get_session)]


@app.on_event("startup")
async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: Session) -> Token:
    existing = await session.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(email=data.email, password_hash=hash_password(data.password))
    session.add(user)
    await session.commit()
    return Token(access_token=create_access_token(data.email))


@app.post("/auth/token", response_model=Token)
async def login(data: UserCreate, session: Session) -> Token:
    user = await session.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.email))


async def current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Session) -> User:
    email = decode_subject(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.post("/secrets", response_model=SecretRead, status_code=status.HTTP_201_CREATED)
async def create_secret(data: SecretCreate, user: Annotated[User, Depends(current_user)], session: Session) -> Secret:
    secret = Secret(owner_id=user.id, name=data.name, value=encrypt_value(data.value))
    session.add(secret)
    await session.commit()
    await session.refresh(secret)
    secret.value = decrypt_value(secret.value)
    return secret


@app.get("/secrets", response_model=list[SecretRead])
async def list_secrets(user: Annotated[User, Depends(current_user)], session: Session) -> list[SecretRead]:
    result = await session.scalars(select(Secret).where(Secret.owner_id == user.id).order_by(Secret.id))
    return [
        SecretRead.model_validate({**secret.__dict__, "value": decrypt_value(secret.value)})
        for secret in result
    ]

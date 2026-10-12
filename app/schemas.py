from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SecretCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=10000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Secret name cannot be blank")
        return value


class SecretUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    value: str | None = Field(default=None, min_length=1, max_length=10000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Secret name cannot be blank")
        return value

    @model_validator(mode="after")
    def require_update_field(self) -> "SecretUpdate":
        if self.name is None and self.value is None:
            raise ValueError("At least one of name or value must be provided")
        return self


class SecretRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    value: str
    created_at: datetime
    updated_at: datetime

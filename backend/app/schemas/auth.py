"""
Pydantic schemas for auth request bodies and response shapes.

Schemas are separate from SQLAlchemy models:
- Models define what's in the database
- Schemas define what comes in from HTTP requests and goes out in responses
This separation lets you control exactly what fields are exposed via the API.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Enforce minimum 8-character password at the schema layer."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe user representation — never includes password_hash."""
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}  # Allows Pydantic to read SQLAlchemy models


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
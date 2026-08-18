"""Pydantic schemas for authentication endpoints."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credentials submitted to POST /auth/login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT returned on successful login."""

    access_token: str
    token_type: str = "bearer"

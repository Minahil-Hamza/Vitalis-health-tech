"""Pydantic schemas for staff management endpoints."""
from pydantic import BaseModel

from app.models.user import Role


class UserCreate(BaseModel):
    """Data required to add a staff member to the admin's facility."""

    full_name: str
    email: str
    password: str
    role: Role


class UserOut(BaseModel):
    """Fields returned after creating, listing, or deactivating a staff member."""

    id: str
    full_name: str
    email: str
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}

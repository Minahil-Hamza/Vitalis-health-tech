"""Pydantic schemas for record endpoints."""
from pydantic import BaseModel

from app.models.record import RecordType


class RecordCreate(BaseModel):
    """Data required to add a clinical record."""

    record_type: RecordType
    title: str
    details: str


class RecordOut(BaseModel):
    """Fields returned after creating a record."""

    id: str
    record_type: RecordType
    title: str

    model_config = {"from_attributes": True}

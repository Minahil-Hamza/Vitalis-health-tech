"""Pydantic schemas for chronic condition endpoints."""
from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.condition import BodyRegion


class ConditionCreate(BaseModel):
    """Data required to add a chronic condition. body_region is optional (some
    conditions, e.g. diabetes, are systemic rather than localized to one body part)."""

    name: str
    diagnosed_date: Optional[date] = None
    notes: Optional[str] = None
    body_region: Optional[BodyRegion] = None


class ConditionOut(BaseModel):
    """A chronic condition, as returned in the patient detail JSON."""

    id: str
    name: str
    diagnosed_date: Optional[date] = None
    notes: Optional[str] = None
    body_region: Optional[BodyRegion] = None

    model_config = {"from_attributes": True}

"""Pydantic schemas for medication endpoints."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class MedicationCreate(BaseModel):
    """Data required to add a medication."""

    drug_name: str
    brand_name: Optional[str] = None
    dose: str
    frequency: str
    started_at: date


class MedicationOut(BaseModel):
    """Fields returned after adding or stopping a medication."""

    id: str
    drug_name: str
    dose: str
    stopped_at: Optional[date] = None

    model_config = {"from_attributes": True}

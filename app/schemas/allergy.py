"""Pydantic schemas for allergy endpoints."""
from pydantic import BaseModel

from app.models.allergy import Severity


class AllergyCreate(BaseModel):
    """Data required to add a patient allergy."""

    substance: str
    severity: Severity


class AllergyOut(BaseModel):
    """Fields returned after adding an allergy."""

    id: str
    substance: str
    severity: Severity

    model_config = {"from_attributes": True}

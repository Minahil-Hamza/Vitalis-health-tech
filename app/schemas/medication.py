"""Pydantic schemas for medication endpoints."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas.safety import validate_override_reason_length


class MedicationCreate(BaseModel):
    """Data required to add a medication. override_reason is only used when a safety check blocks the save."""

    drug_name: str
    brand_name: Optional[str] = None
    dose: str
    frequency: str
    started_at: date
    override_reason: Optional[str] = None

    @field_validator("override_reason")
    @classmethod
    def check_override_reason(cls, value: Optional[str]) -> Optional[str]:
        """If an override reason is given, it must meet the minimum length."""
        return validate_override_reason_length(value)


class MedicationOut(BaseModel):
    """Fields returned after stopping a medication."""

    id: str
    drug_name: str
    dose: str
    stopped_at: Optional[date] = None

    model_config = {"from_attributes": True}


class MedicationCreateResponse(MedicationOut):
    """Fields returned after adding a medication, including any non-blocking safety warnings."""

    warnings: list[str] = []


class MedicationDetailOut(BaseModel):
    """Full medication fields, as shown on the patient detail page."""

    id: str
    drug_name: str
    brand_name: Optional[str] = None
    dose: str
    frequency: str
    started_at: date
    stopped_at: Optional[date] = None

    model_config = {"from_attributes": True}

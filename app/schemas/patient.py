"""Pydantic schemas for patient endpoints."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.patient import Gender

CNIC_PATTERN = re.compile(r"^\d{5}-\d{7}-\d$")


class PatientCreate(BaseModel):
    """Data required to register a new patient."""

    cnic: str
    full_name: str
    date_of_birth: date
    gender: Gender
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    consent_sharing: bool = True

    @field_validator("cnic")
    @classmethod
    def validate_cnic_format(cls, value: str) -> str:
        """Ensure the CNIC matches Pakistan's NNNNN-NNNNNNN-N format."""
        if not CNIC_PATTERN.match(value):
            raise ValueError("CNIC must match the format 12345-1234567-1")
        return value


class PatientOut(BaseModel):
    """Minimal patient fields returned after creation or from a CNIC search."""

    id: str
    cnic: str
    full_name: str

    model_config = {"from_attributes": True}

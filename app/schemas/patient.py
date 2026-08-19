"""Pydantic schemas for patient endpoints."""
import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.patient import Gender
from app.models.record import RecordType
from app.schemas.allergy import AllergyOut
from app.schemas.condition import ConditionOut
from app.schemas.medication import MedicationDetailOut

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


class RecordDetailOut(BaseModel):
    """A clinical record, tagged with the facility and author it belongs to."""

    id: str
    record_type: RecordType
    title: str
    details: str
    created_at: datetime
    facility_name: str
    author_name: str


class PatientDetailOut(BaseModel):
    """The full patient summary: demographics plus allergies, conditions, medications, and records."""

    id: str
    cnic: str
    full_name: str
    date_of_birth: date
    gender: Gender
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    consent_sharing: bool
    created_by_facility_id: str
    created_at: datetime
    is_creating_facility: bool
    allergies: list[AllergyOut]
    conditions: list[ConditionOut]
    active_medications: list[MedicationDetailOut]
    past_medications: list[MedicationDetailOut]
    records: list[RecordDetailOut]

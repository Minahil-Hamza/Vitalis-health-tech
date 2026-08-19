"""Pydantic schemas for record endpoints."""
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.models.record import RecordType
from app.schemas.safety import validate_override_reason_length


class RecordCreate(BaseModel):
    """Data required to add a clinical record.

    drug_name is required when record_type is "prescription" (so the safety checks have
    something to check) and must be absent otherwise; override_reason is only used when
    a safety check blocks the save.
    """

    record_type: RecordType
    title: str
    details: str
    drug_name: Optional[str] = None
    override_reason: Optional[str] = None

    @field_validator("override_reason")
    @classmethod
    def check_override_reason(cls, value: Optional[str]) -> Optional[str]:
        """If an override reason is given, it must meet the minimum length."""
        return validate_override_reason_length(value)

    @model_validator(mode="after")
    def check_drug_name_matches_record_type(self) -> "RecordCreate":
        """drug_name is required for prescriptions, and meaningless for anything else."""
        if self.record_type == RecordType.PRESCRIPTION and not (self.drug_name and self.drug_name.strip()):
            raise ValueError("drug_name is required for a prescription record")
        if self.record_type != RecordType.PRESCRIPTION and self.drug_name:
            raise ValueError("drug_name is only valid for a prescription record")
        return self


class RecordOut(BaseModel):
    """Fields returned after creating a record, including any non-blocking safety warnings."""

    id: str
    record_type: RecordType
    title: str
    drug_name: Optional[str] = None
    warnings: list[str] = []

    model_config = {"from_attributes": True}

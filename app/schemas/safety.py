"""Schema for the blocking 409 response returned when a medication needs an override reason."""
from typing import Optional

from pydantic import BaseModel

MIN_OVERRIDE_REASON_LENGTH = 10


def validate_override_reason_length(value: Optional[str]) -> Optional[str]:
    """Shared validator body: if an override reason is given at all, it must be substantive."""
    if value is not None and len(value.strip()) < MIN_OVERRIDE_REASON_LENGTH:
        raise ValueError(f"Override reason must be at least {MIN_OVERRIDE_REASON_LENGTH} characters")
    return value


class InteractionWarning(BaseModel):
    """A single drug interaction warning, in plain language."""

    drug_a: str
    drug_b: str
    severity: str
    description: str
    recommendation: str


class SafetyBlockedDetail(BaseModel):
    """409 response body: why a medication was blocked and what triggered it."""

    message: str
    interactions: list[InteractionWarning] = []
    allergy_hits: list[str] = []

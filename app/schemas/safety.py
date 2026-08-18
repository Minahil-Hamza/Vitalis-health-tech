"""Schema for the blocking 409 response returned when a medication needs an override reason."""
from pydantic import BaseModel


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

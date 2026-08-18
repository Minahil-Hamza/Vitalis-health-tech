"""Shared patient-lookup and consent-gate logic used across patient sub-resource routes."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User

CONSENT_DENIED_DETAIL = "This patient has not consented to sharing with your facility"


def get_patient_or_404(db: Session, patient_id: str) -> Patient:
    """Load a patient by id, raising 404 if not found."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def has_consent_access(patient: Patient, user: User) -> bool:
    """True if the user's facility may access this patient's record (own facility, or consent given)."""
    return patient.consent_sharing or user.facility_id == patient.created_by_facility_id

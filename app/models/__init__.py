"""Import all models so they register on Base.metadata (needed by Alembic and create_all)."""
from app.models.facility import Facility
from app.models.user import Role, User
from app.models.audit_log import AuditAction, AuditLog
from app.models.patient import Gender, Patient
from app.models.allergy import Allergy, Severity
from app.models.condition import Condition
from app.models.medication import Medication
from app.models.record import Record, RecordType

__all__ = [
    "Facility",
    "User",
    "Role",
    "AuditLog",
    "AuditAction",
    "Patient",
    "Gender",
    "Allergy",
    "Severity",
    "Condition",
    "Medication",
    "Record",
    "RecordType",
]

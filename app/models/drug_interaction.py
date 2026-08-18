"""Drug interaction reference table, populated by the founder via CSV import."""
import enum
import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InteractionSeverity(str, enum.Enum):
    """Severity of a drug-drug interaction."""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class DrugInteraction(Base):
    """A known interaction between two generic drug names (both stored lowercase)."""

    __tablename__ = "drug_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drug_a: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    drug_b: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    severity: Mapped[InteractionSeverity] = mapped_column(
        Enum(InteractionSeverity, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

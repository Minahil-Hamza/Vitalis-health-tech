"""Chronic condition model."""
import enum
import uuid
from datetime import date as date_type

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BodyRegion(str, enum.Enum):
    """Approximate anatomical region for the 3D patient visualization.

    Not every condition maps cleanly onto one body part (e.g. diabetes is metabolic,
    not localized) — GENERAL covers those rather than forcing an arbitrary placement.
    """

    HEAD = "head"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    BACK = "back"
    GENERAL = "general"


class Condition(Base):
    """A chronic condition recorded for a patient."""

    __tablename__ = "conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosed_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_region: Mapped[BodyRegion | None] = mapped_column(
        Enum(BodyRegion, values_callable=lambda e: [m.value for m in e]), nullable=True
    )

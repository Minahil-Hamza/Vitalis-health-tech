"""Pydantic schemas for the admin dashboard JSON view."""
from pydantic import BaseModel

from app.schemas.user import UserOut


class AdminDashboardOut(BaseModel):
    """This facility's staff list and simple counts, as shown on the admin dashboard."""

    staff: list[UserOut]
    patients_created: int
    records_this_month: int
    current_user_id: str

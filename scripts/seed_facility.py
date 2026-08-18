"""One-time admin script: creates the first facility and its admin user.

Run manually after applying migrations: python scripts/seed_facility.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.facility import Facility
from app.models.user import Role, User
from app.services.security import hash_password


def seed():
    """Prompt for facility and admin details, then create both rows."""
    db = SessionLocal()
    try:
        name = input("Facility name: ").strip()
        city = input("City: ").strip()
        address = input("Address: ").strip()
        license_number = input("License number: ").strip()

        facility = Facility(name=name, city=city, address=address, license_number=license_number)
        db.add(facility)
        db.flush()

        admin_name = input("Admin full name: ").strip()
        admin_email = input("Admin email: ").strip()
        admin_password = input("Admin password: ").strip()

        admin = User(
            facility_id=facility.id,
            full_name=admin_name,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role=Role.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Created facility '{facility.name}' and admin user '{admin.email}'.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

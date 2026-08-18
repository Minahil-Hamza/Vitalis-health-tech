"""Non-interactive demo seed script: 2 facilities, 4 users, 3 patients, 10 drug interactions.

Run after applying migrations: python scripts/seed_demo.py

Safe to run once against a fresh database. Re-running will fail on unique constraints
(CNIC/email) rather than silently duplicating data — drop the dev DB and re-migrate if
you want a clean slate again.

The drug interactions below are well-documented, widely taught examples (not exhaustive
or a substitute for a clinical reference) — review before relying on them for anything
beyond local demoing.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.allergy import Allergy, Severity
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.facility import Facility
from app.models.medication import Medication
from app.models.patient import Gender, Patient
from app.models.user import Role, User
from app.services.security import hash_password

DEMO_PASSWORD = "Demo1234!"

INTERACTIONS = [
    ("aspirin", "warfarin", InteractionSeverity.MAJOR,
     "Increased risk of major bleeding.", "Avoid combination; if unavoidable, monitor INR closely."),
    ("warfarin", "ibuprofen", InteractionSeverity.MAJOR,
     "NSAIDs increase bleeding risk with warfarin.", "Avoid; use paracetamol for pain relief instead."),
    ("warfarin", "amiodarone", InteractionSeverity.MAJOR,
     "Amiodarone raises warfarin levels, increasing INR.", "Reduce warfarin dose and monitor INR closely."),
    ("simvastatin", "clarithromycin", InteractionSeverity.MAJOR,
     "Increased risk of myopathy/rhabdomyolysis.", "Avoid combination or temporarily suspend the statin."),
    ("digoxin", "amiodarone", InteractionSeverity.MAJOR,
     "Amiodarone increases digoxin levels, risking toxicity.", "Reduce digoxin dose by roughly half and monitor levels."),
    ("sildenafil", "nitrates", InteractionSeverity.MAJOR,
     "Risk of severe, life-threatening hypotension.", "Contraindicated together."),
    ("lisinopril", "spironolactone", InteractionSeverity.MODERATE,
     "Combined risk of hyperkalemia.", "Monitor serum potassium regularly."),
    ("clopidogrel", "omeprazole", InteractionSeverity.MODERATE,
     "Omeprazole may reduce clopidogrel's antiplatelet effect.", "Consider pantoprazole as an alternative PPI."),
    ("ciprofloxacin", "theophylline", InteractionSeverity.MAJOR,
     "Ciprofloxacin increases theophylline levels, risking toxicity.", "Monitor theophylline levels; consider dose reduction."),
    ("lithium", "ibuprofen", InteractionSeverity.MODERATE,
     "NSAIDs can reduce lithium clearance, risking toxicity.", "Monitor lithium levels if used together."),
]


def seed():
    """Populate a fresh database with a demo-ready dataset."""
    db = SessionLocal()
    try:
        clinic_a = Facility(name="City Care Clinic", city="Lahore", address="12 Mall Road", license_number="DEMO-A")
        clinic_b = Facility(name="Al-Shifa Clinic", city="Karachi", address="45 Clifton Ave", license_number="DEMO-B")
        db.add_all([clinic_a, clinic_b])
        db.flush()

        users = [
            User(facility_id=clinic_a.id, full_name="Dr. Amina Malik", email="admin@citycare.demo",
                 password_hash=hash_password(DEMO_PASSWORD), role=Role.ADMIN),
            User(facility_id=clinic_a.id, full_name="Dr. Bilal Ahmed", email="doctor@citycare.demo",
                 password_hash=hash_password(DEMO_PASSWORD), role=Role.DOCTOR),
            User(facility_id=clinic_b.id, full_name="Sana Qureshi", email="admin@alshifa.demo",
                 password_hash=hash_password(DEMO_PASSWORD), role=Role.ADMIN),
            User(facility_id=clinic_b.id, full_name="Zara Hussain", email="pharmacist@alshifa.demo",
                 password_hash=hash_password(DEMO_PASSWORD), role=Role.PHARMACIST),
        ]
        db.add_all(users)
        db.flush()
        admin_a = users[0]

        patients = [
            Patient(cnic="35202-1234567-1", full_name="Ahmed Raza", date_of_birth=date(1980, 3, 15),
                    gender=Gender.MALE, blood_group="B+", phone="03001234567",
                    address="House 7, Model Town, Lahore", created_by_facility_id=clinic_a.id),
            Patient(cnic="42101-7654321-2", full_name="Fatima Sheikh", date_of_birth=date(1992, 7, 22),
                    gender=Gender.FEMALE, blood_group="O+", phone="03211234567",
                    address="Flat 3B, Clifton, Karachi", created_by_facility_id=clinic_b.id),
            Patient(cnic="35201-9988776-3", full_name="Usman Tariq", date_of_birth=date(1965, 11, 2),
                    gender=Gender.MALE, blood_group="A-", phone="03331234567",
                    address="Street 5, Gulberg, Lahore", created_by_facility_id=clinic_a.id),
        ]
        db.add_all(patients)
        db.flush()
        ahmed, _fatima, usman = patients

        db.add(Allergy(patient_id=ahmed.id, substance="Penicillin", severity=Severity.SEVERE, noted_by_user_id=admin_a.id))
        db.add(Medication(
            patient_id=usman.id, drug_name="warfarin", dose="5mg", frequency="once daily",
            started_at=date(2024, 1, 10), prescribed_by_user_id=admin_a.id, facility_id=clinic_a.id,
        ))

        for drug_a, drug_b, severity, description, recommendation in INTERACTIONS:
            db.add(DrugInteraction(
                drug_a=drug_a, drug_b=drug_b, severity=severity,
                description=description, recommendation=recommendation,
            ))

        db.commit()

        print("Demo data seeded.")
        print("\nFacilities:")
        print("  City Care Clinic (Lahore)")
        print("  Al-Shifa Clinic (Karachi)")
        print(f"\nLogins (all use password '{DEMO_PASSWORD}'):")
        for u in users:
            facility_name = "City Care Clinic" if u.facility_id == clinic_a.id else "Al-Shifa Clinic"
            print(f"  {u.email} — {u.role.value} at {facility_name}")
        print("\nDemo patients:")
        print("  Ahmed Raza (CNIC 35202-1234567-1) — severe penicillin allergy")
        print("  Fatima Sheikh (CNIC 42101-7654321-2)")
        print("  Usman Tariq (CNIC 35201-9988776-3) — on warfarin; try adding aspirin for him")
        print(f"\n{len(INTERACTIONS)} drug interactions loaded into the reference table.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

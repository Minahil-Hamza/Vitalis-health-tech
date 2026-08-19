VITALIS — Product & Technical Specification

Version 1.0 | Spec-Driven Development Document

Founder: Pharmacist + AI Engineer | Solo builder using Cursor



HOW TO USE THIS DOCUMENT (instructions for the AI assistant)

You are helping a solo founder build Vitalis. Follow these working rules:





Build ONE phase at a time, in order. Never skip ahead.



Before writing code for a phase, list the files you will create/modify

and wait for my confirmation.



After completing each task, tell me exactly how to test it manually

(commands + what I should see in the browser).



Write clean, commented code. Every function gets a docstring.



If a decision is ambiguous, ask me instead of assuming.



Never store secrets in code. Use a .env file and python-dotenv.



After each phase, write/update pytest tests and run them.



Keep a PROGRESS.md file updated: what is done, what is next.



If I paste an error, explain the cause in one sentence before fixing.



Prefer boring, proven technology over clever solutions.





1. PRODUCT OVERVIEW

Product name: Vitalis
One-liner: One patient, one record — a centralized electronic health
record (EHR) platform that lets any connected clinic or hospital in
Pakistan retrieve a patient's complete medical history using their CNIC
(national ID), with built-in medication safety checks.

Problem: Patient medical records in Pakistan are fragmented across
hospitals and paper registers. When a patient visits a new facility,
their history, allergies, and current medications are unknown, causing
dangerous prescribing errors and wasted time.

Target users (v1): Small private clinics (1–5 doctors) in Pakistan.
Roles: Doctor, Pharmacist, Nurse, Receptionist, Clinic Admin.

Unique differentiators:





CNIC-based universal patient identity



Cross-facility record sharing with consent + full audit trail



Drug interaction & allergy alerts at prescription time (founder is a
pharmacist — clinical safety is the core brand)

Non-goals for v1 (do NOT build these yet):





Patient-facing mobile app



Insurance/billing module



Government system integration



Multi-language UI (English only for v1; Urdu later)





2. TECH STACK (fixed — do not substitute)





Backend: Python 3.12, FastAPI, SQLAlchemy 2.x ORM



Database: SQLite for development, PostgreSQL for production
(write code that works with both via SQLAlchemy)



Auth: JWT tokens (python-jose), passwords hashed with bcrypt
(passlib)



Frontend: Server-rendered Jinja2 templates + vanilla JS + a single
CSS file. NO React/Vue in v1 (solo founder must be able to maintain it)

AMENDMENT (2026-08-19): the founder approved a parallel React
frontend initiative (Phases 7-10, tracked in PROGRESS.md, outside
this document's phase list below) to build a 3D patient
visualization: Node.js, npm, Vite, React, react-router-dom,
react-three-fiber, Three.js, @react-three/drei, Vitest, and React
Testing Library are approved for that initiative only. The Jinja2 +
vanilla JS app above remains the default, spec-compliant app for
Phases 0-6 and stays in place until a deliberate cutover decision.



Migrations: Alembic



Testing: pytest + httpx TestClient



Config: pydantic-settings reading from .env

Project structure:

vitalis/
├── app/
│   ├── main.py            # FastAPI app entry
│   ├── config.py          # Settings from .env
│   ├── database.py        # Engine, session, Base
│   ├── models/            # SQLAlchemy models (one file per domain)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # API + page routes (one file per domain)
│   ├── services/          # Business logic (interactions, audit, auth)
│   ├── templates/         # Jinja2 HTML
│   └── static/            # style.css, app.js
├── tests/
├── alembic/
├── .env.example
├── requirements.txt
└── PROGRESS.md





3. DATA MODEL

Facility — id (uuid), name, city, address, license_number, is_active,
created_at

User (staff) — id, facility_id (FK), full_name, email (unique),
password_hash, role enum [admin, doctor, pharmacist, nurse, receptionist],
is_active, created_at

Patient — id, cnic (unique, format ^\d{5}-\d{7}-\d$), full_name,
date_of_birth, gender enum, blood_group, phone, address,
consent_sharing (bool, default true), created_by_facility_id, created_at

Allergy — id, patient_id (FK), substance, severity enum
[mild, moderate, severe], noted_by_user_id, created_at

Condition (chronic) — id, patient_id, name, diagnosed_date, notes
(AMENDMENT 2026-08-19: + body_region, a nullable enum [head, chest,
abdomen, pelvis, left_arm, right_arm, left_leg, right_leg, back,
general], added to support the Phase 9 3D patient visualization —
not part of the original v1.0 data model; left null for systemic
conditions like diabetes rather than forced onto a fake location)

Medication (current meds) — id, patient_id, drug_name (generic),
brand_name, dose, frequency, started_at, stopped_at (nullable),
prescribed_by_user_id, facility_id

Record — id, patient_id, facility_id, author_user_id, record_type
enum [visit, prescription, lab_report, admission, discharge],
title, details (text), created_at

DrugInteraction (reference table) — id, drug_a (generic, lowercase),
drug_b, severity enum [minor, moderate, major], description,
recommendation
(Founder will populate this table himself — build an admin CSV-import
endpoint for it.)

AuditLog — id, user_id, facility_id, patient_id, action enum
[viewed_summary, created_record, updated_patient, added_medication,
login, login_failed], timestamp, ip_address
(Append-only. No update/delete endpoints may exist for this table.)





4. FEATURES BY PHASE (build strictly in this order)



PHASE 0 — Project skeleton





Project structure above, config, database setup, Alembic init



Health-check endpoint GET /health



PROGRESS.md created



Acceptance: uvicorn app.main:app runs; /health returns
{"status":"ok"}; pytest passes with one dummy test.



PHASE 1 — Auth & facilities





Facility registration (admin-only seed script creates first facility





admin user)



Staff login: POST /auth/login returns JWT; JWT contains user_id,
facility_id, role



Role-based dependency: require_role([...]) for route protection



Login page (Jinja2) + logout



Audit log entries for login and login_failed



Acceptance: admin can log in via browser; wrong password shows
error and creates login_failed audit entry; tests cover both.



PHASE 2 — Patients





Create patient (any staff role except nurse), CNIC validated + unique



Search patient by exact CNIC: GET /patients/search?cnic=



Patient summary page: demographics, ALLERGY BANNER (red, top of page,
always visible if any allergy exists), chronic conditions, current
medications, latest 10 records from ALL facilities



Every summary view writes an AuditLog row (viewed_summary)



Consent check: if patient.consent_sharing is false and requesting
facility != creating facility, return 403 page explaining consent



Acceptance: patient created at Facility A is fully visible when a
Facility B user searches the CNIC; audit page shows both accesses.



PHASE 3 — Records & medications





Add record form (type, title, details) on patient page



Add/stop medication; medication list shows active meds distinctly



Add allergy with severity



Timeline view: all records newest-first, each tagged with facility
name and author



Acceptance: records created at two different facilities appear in
one timeline; stopping a medication moves it to "past medications".



PHASE 4 — CLINICAL SAFETY ENGINE (the differentiator)





services/interactions.py:





check_interactions(new_drug, patient) → list of conflicts against
the patient's ACTIVE medications using DrugInteraction table
(match on lowercase generic names)



check_allergy(new_drug, patient) → warning if drug or its family
matches a recorded allergy substance (exact + substring match v1)



When staff adds a prescription-type record or a medication:





Run both checks BEFORE saving



If MAJOR interaction or any allergy hit: show blocking warning

page; user must type a reason to override; the override reason is
 stored in the record and flagged in the audit log



Minor/moderate: show non-blocking yellow warning



Admin CSV import for DrugInteraction table: POST /admin/interactions/import



Acceptance: adding "aspirin" for a patient on "warfarin" (seeded
in the interaction table) triggers a blocking warning; override
requires a reason; everything is auditable. Tests cover block,
override, and clean-pass paths.



PHASE 5 — Audit & admin





Patient access-history page: who viewed/edited, when, from which
facility (visible to admin + the record's facility staff)



Facility admin dashboard: staff management (add/deactivate users),
simple counts (patients created, records this month)



Acceptance: deactivated user cannot log in; audit page paginates.



PHASE 6 — Polish & deploy-readiness





Rate limiting on auth endpoints (slowapi)



Proper error pages (404, 403, 500)



Seed script: 2 facilities, 4 users, 3 demo patients, 10 interactions



README with local setup + deployment notes (single VPS + PostgreSQL





Caddy/Nginx; no Docker required in v1 unless trivial)



Acceptance: fresh clone → follow README → working demo in under
10 minutes.



BACKLOG (do not build until told): AI record summarization,

prescription OCR, Urdu UI, patient OTP consent, offline mode,
FHIR export, patient mobile app.





5. SECURITY REQUIREMENTS (non-negotiable, apply from Phase 1)





All passwords bcrypt-hashed; JWT expiry 12h; no refresh tokens in v1



Every patient-data endpoint requires authentication; no public data



SQL only via ORM/parameterized queries



CNIC and phone are PII: never write them to application logs



AuditLog is append-only by design (no ORM update/delete paths)



CORS locked to same origin in v1



.env for secrets; .env in .gitignore; provide .env.example





6. UI GUIDELINES





Clean clinical look: white background, deep green (#0E7A5F) primary,
red (#C4331B) reserved EXCLUSIVELY for allergy/interaction warnings



Patient safety information (allergy banner) must be visible without
scrolling on every patient page



Every page usable on a phone (clinic staff often use phones)



Fonts: system font stack (no external font dependency in the app)



Warning pages must state the clinical reason in plain language





7. DEFINITION OF DONE (every phase)





Code runs locally with documented commands



pytest green



Manual test steps given to founder and confirmed by founder



PROGRESS.md updated



No TODOs left in code without a matching PROGRESS.md entry





FIRST PROMPT TO START (founder: paste this after the spec)

"Read the full VITALIS spec above. Confirm you understand the working
rules. Then begin PHASE 0: list the files you will create, wait for my
go-ahead, then build the skeleton."


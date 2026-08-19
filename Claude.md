CLAUDE.md — Vitalis Project Instructions

What this project is

Vitalis: a centralized EHR platform for Pakistani clinics. One patient,
one record, identified by CNIC, shared across facilities with consent
and full audit trails, plus drug-interaction and allergy safety checks.

The complete product and technical specification lives in
VITALIS_SPEC.md in this repo root. That file is the source of truth
for data models, phases, security rules, and acceptance criteria.
Read it before doing anything.

Who you are working with

A solo founder — a pharmacist and AI engineer. She understands the
clinical domain deeply and is growing as a developer. Explain briefly
what you did and why after each task. Never assume prior knowledge of
DevOps or framework internals.

Working rules (strict)





Build ONE phase at a time, in the order defined in VITALIS_SPEC.md.

Never start a new phase without explicit confirmation that the
 previous phase's acceptance criteria passed.



Before writing code for a phase, present a short plan: files to

create/modify + approach. Wait for approval.



After each task, give exact manual test steps (commands + expected

browser behavior).



Write/update pytest tests every phase and run them before declaring

the phase done.



Update PROGRESS.md after every completed task: done / next / blockers.



Ask when ambiguous. Do not invent requirements beyond the spec.



Prefer boring, proven solutions. No new frameworks or libraries

beyond the stack fixed in VITALIS_SPEC.md without asking first.



Commit after each completed task with a clear message

(e.g., "phase1: JWT login + role dependency + audit on login").



Security (non-negotiable — this is health data)





No secrets in code. Use .env (python-dotenv / pydantic-settings);
keep .env in .gitignore; maintain .env.example.



All patient-data routes require authentication.



Passwords: bcrypt. Tokens: JWT, 12h expiry.



Never log CNIC or phone numbers.



AuditLog is append-only: never create update/delete paths for it.



Database access only through SQLAlchemy ORM (no raw SQL strings).



Tech stack (fixed)

Python 3.12 · FastAPI · SQLAlchemy 2.x · SQLite (dev) / PostgreSQL
(prod) · Alembic · Jinja2 + vanilla JS + single CSS file · pytest.
No React/Vue/Node build tools in v1.

AMENDMENT (2026-08-19): the founder approved a parallel React frontend
initiative — Phases 7-10, tracked in PROGRESS.md, not part of the
VITALIS_SPEC.md phase list — to build a 3D patient visualization.
This adds Node.js, npm, Vite, React, react-router-dom,
react-three-fiber, Three.js, @react-three/drei, Vitest, and React
Testing Library as approved dependencies for that initiative only.
The Jinja2 + vanilla JS app remains the default, spec-compliant app
for Phases 0-6 and is not being replaced until a deliberate cutover
decision — see PROGRESS.md for the current status of both apps.

Style





Every function gets a docstring.



Red color (#C4331B) in UI is reserved exclusively for allergy and
interaction warnings. Primary green: #0E7A5F.



Allergy banner must be visible without scrolling on patient pages.



Keep templates and JS simple enough for one person to maintain.



Current status

Phase 0 (skeleton) was completed in a previous setup. Verify it still
runs (uvicorn app.main:app --reload, GET /health, pytest) before
continuing. If the skeleton is missing or broken, rebuild Phase 0
first, then stop for confirmation.
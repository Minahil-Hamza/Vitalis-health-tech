# Vitalis — Progress

## Done
- Phase 0: project skeleton
  - `app/` package with `main.py` (FastAPI app + `GET /health`), `config.py` (pydantic-settings), `database.py` (SQLAlchemy engine/session/Base)
  - Empty `models/`, `schemas/`, `routers/`, `services/` packages ready for Phase 1
  - `app/templates/` and `app/static/style.css` (brand colors: primary `#0E7A5F`, warning `#C4331B`) and `app.js` placeholders
  - `tests/test_health.py`: dummy test + `/health` test
  - `.env.example`, `.env` (gitignored), `.gitignore`, `requirements.txt`
  - Own git repo initialized inside `Vitalis/` (previously the folder had no repo of its own; a stray repo rooted at the Windows user profile was in use — not used for this project)

- Phase 1: Auth & facilities
  - `Facility`, `User` (role enum: admin/doctor/pharmacist/nurse/receptionist), `AuditLog` (append-only, no update/delete path anywhere) models + Alembic migration `07862e4ba847`
  - `app/services/security.py`: bcrypt hashing, JWT (12h expiry, `user_id`/`facility_id`/`role` claims), `get_current_user` and `require_role([...])` dependencies (read JWT from `Authorization: Bearer` header or an HttpOnly `access_token` cookie)
  - `app/services/audit.py`: single `log_action()` helper — the only way audit rows are written
  - `POST /auth/login` (JSON API + sets cookie), `GET /login` (Jinja2 page, vanilla-JS form submit), `GET /logout`
  - `GET /` protected dashboard page proving `get_current_user`/`require_role` work end-to-end
  - `scripts/seed_facility.py`: interactive one-time script to create the first facility + admin user (not an HTTP endpoint, per spec)
  - `tests/conftest.py` (isolated in-memory test DB) + `tests/test_auth.py`: login success/failure/unknown-email (each asserts the correct audit row), protected-route auth check, `require_role` allow/block
  - Fixed a passlib/bcrypt incompatibility: passlib 1.7.4 doesn't support bcrypt ≥4.0 (removed `__about__`, and 4.x/5.x reject >72-byte inputs during passlib's internal self-test instead of truncating) — pinned `bcrypt==3.2.2` in `requirements.txt`

## Next
- Phase 2: Patients — create patient (CNIC validated + unique), search by CNIC, patient summary page with allergy banner, consent check across facilities, audit on every summary view. Waiting for go-ahead.

## Blockers
- None. Note: port 8000 on this machine is occupied by Docker Desktop/WSL port-forwarding (unrelated to this project) — local dev server testing used port 8001 instead.

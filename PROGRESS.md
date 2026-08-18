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

- Phase 2: Patients
  - `Patient` (cnic unique + regex `^\d{5}-\d{7}-\d$`, gender enum male/female/other, consent_sharing), `Allergy` (severity enum), `Condition`, `Medication`, `Record` (record_type enum) models + Alembic migration `f7a674ec8897`. Only `Patient` has create/read endpoints this phase — Allergy/Condition/Medication/Record are queried by the summary page but have no create endpoints yet (that's Phase 3), so a freshly created patient shows empty sections until then.
  - `POST /patients` + `GET /patients/new` (role-protected: everyone except nurse), CNIC format + uniqueness validated with clean 422/409 errors
  - `GET /patients/search?cnic=` — exact match, any authenticated role, minimal `{id, cnic, full_name}` response
  - `GET /patients/{id}` — summary page: allergy banner (red, top of page, only rendered when allergies exist), chronic conditions, current medications (`stopped_at IS NULL`), latest 10 records across all facilities. Writes a `viewed_summary` audit row on every successful view.
  - Consent check: if `consent_sharing` is false and the viewer's facility isn't the creating facility, returns a 403 page in plain language and does **not** write an audit row (nothing was actually viewed); the creating facility can always view its own patient regardless of consent
  - Dashboard gained a CNIC search box + "Add patient" link
  - `tests/test_patients.py` (11 tests): create success/invalid-CNIC/duplicate-CNIC/forbidden-for-nurse, search found/not-found, cross-facility view + audit row, consent-denied 403 + no audit row, same-facility access despite no consent, allergy banner shown/hidden, conditions/medications render (stopped meds excluded), records truncated to latest 10
  - Manually verified end-to-end with two seeded facilities via curl: cross-facility search/view, allergy banner rendering, consent 403, and confirmed the exact expected rows landed in the real dev-DB audit log

## Next
- Phase 3: Records & medications — add record form, add/stop medication, add allergy with severity, timeline view tagged by facility + author. Waiting for go-ahead.

## Blockers
- None. Note: port 8000 on this machine is occupied by Docker Desktop/WSL port-forwarding (unrelated to this project) — local dev server testing used port 8001 instead.

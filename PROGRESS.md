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

- Phase 3: Records & medications
  - `app/services/patient_access.py`: shared `get_patient_or_404`/`has_consent_access` helpers, now reused by the Phase 2 summary route too (small refactor, no behavior change there)
  - `POST /patients/{id}/records` (audited `created_record`), `GET /patients/{id}/timeline` (all records, newest-first, tagged with facility + author — separate from the summary's latest-10)
  - `POST /patients/{id}/medications` (audited `added_medication`), `POST /patients/{id}/medications/{id}/stop` (sets `stopped_at` to today; 400 if already stopped)
  - `POST /patients/{id}/allergies` (no audit row — the spec's `AuditAction` enum has no matching action; flagged and left as-is per your go-ahead)
  - All four write actions apply the same consent gate as viewing: blocked with 403 if the patient hasn't consented and you're not from the creating facility. No role restriction beyond being logged in (spec didn't specify one for this phase, unlike patient creation).
  - Add-record/medication/allergy forms are inline on `patient_summary.html` itself (per the spec's "on patient page" wording) with a "Stop" button per active medication; summary page now also shows a "Past medications" section
  - `tests/test_records.py`, `tests/test_medications.py`, `tests/test_allergies.py` (11 new tests): create + audit row, consent gate blocking all three write actions, stop-medication moving a drug to past (and rejecting a double-stop), timeline showing both facilities' records newest-first
  - Manually verified end-to-end via curl across two seeded facilities: added allergy/medication/record at Facility A, added a cross-facility record at Facility B, confirmed the timeline shows both newest-first, stopped the medication and confirmed it moved to "Past medications" (and a second stop attempt correctly 400s), then confirmed the real dev-DB audit log had exactly the expected rows (login, added_medication, created_record ×2, viewed_summary ×2 — no rows for the allergy add or the stop)

- Phase 4: Clinical safety engine
  - `DrugInteraction` reference model (drug_a/drug_b lowercase, severity enum minor/moderate/major — a distinct value set from `Allergy.severity`'s mild/moderate/severe) + Alembic migration `75a7c785008b`, which also adds a nullable `override_reason` column to both `Medication` and `AuditLog`
  - `app/services/interactions.py`: `check_interactions()` (matches the new drug against active medications only, either direction) and `check_allergy()` (bidirectional substring match, covers exact match too)
  - Safety checks run only on `POST /patients/{id}/medications` — `Record` has no drug-name field for them to check against, so "prescription-type record" in the spec is being treated as the medication-add flow (flagged for your confirmation in the plan; free-text prescription records are unaffected)
  - Major interaction or any allergy hit blocks the save with 409 and full warning details unless an `override_reason` is submitted, in which case it's stored on the medication **and** flagged on the `added_medication` audit row; a blocked (unsaved) attempt writes no audit row, consistent with how denied views work in Phase 2. Minor/moderate interactions save immediately and just return non-blocking warnings.
  - Summary page's medication form now catches the 409, prompts for an override reason via `window.prompt`, and resubmits; a yellow (not the reserved red) `.interaction-warning-banner` style was added to the stylesheet for the non-blocking case
  - `POST /admin/interactions/import` (admin-only): CSV upload with columns `drug_a,drug_b,severity,description,recommendation`; bad rows are skipped and reported individually rather than failing the whole import
  - `tests/test_interactions.py` (service-level), `tests/test_medication_safety.py`, `tests/test_admin.py` (18 new tests): clean pass, major-interaction block + override + audit flag, allergy-hit block, minor-interaction non-blocking warning, stopped medications excluded from interaction checks, CSV import success/bad-row-skip/admin-only
  - Manually verified the spec's exact acceptance scenario via curl: seeded aspirin↔warfarin (major) and metformin↔ibuprofen (moderate) via CSV import, put a patient on warfarin, confirmed adding aspirin without a reason 409s with the interaction details, confirmed it saves with `override_reason` stored and the audit row flagged when a reason is given, confirmed a clean drug (paracetamol) saves normally, and confirmed the moderate case (ibuprofen after metformin) saves immediately with a non-blocking warning — then inspected the real dev-DB audit log and confirmed no row exists for the blocked attempt

- Phase 5: Audit & admin
  - `GET /patients/{id}/access-history` — paginated (20/page) list of every `AuditLog` row tied to the patient: when, action, staff name, facility, and the override reason if one was flagged in Phase 4. Restricted to staff at the patient's *creating* facility only — stricter than the general consent-based viewing rule from Phase 2, since this reveals who else has looked at the record. A link appears on the summary page only when you're at the creating facility.
  - `GET /admin` (admin-only, scoped to the admin's own facility): staff list, "Patients created" (all-time total for this facility) and "Records this month" (since the 1st of the current calendar month) counts, an add-staff form, and a "Deactivate" button per active staff member
  - `POST /admin/users` (add staff) and `POST /admin/users/{id}/deactivate` — an admin can't deactivate their own account (self-lockout guard, not spec-mandated but added for safety) or a user at another facility; deactivated users are already blocked from logging in by the Phase 1 login check, confirmed here with new test coverage
  - No audit rows for staff add/deactivate — no matching `AuditAction` enum value exists, same reasoning as allergy-add/medication-stop in Phase 3
  - `tests/test_access_history.py`, `tests/test_admin_dashboard.py` (14 new tests): creating-facility visibility vs. cross-facility 403, override reason rendering, pagination boundaries, add/deactivate staff, self- and cross-facility deactivation rejected, deactivated user blocked from login, dashboard counts
  - Manually verified via curl across two seeded facilities: added and deactivated a nurse (confirmed login blocked after), confirmed self-deactivation and admin-dashboard counts, and confirmed Facility B can view a patient's summary (consent allows it) but gets a 403 on that same patient's access-history page

- Phase 6: Polish & deploy-readiness
  - Rate limiting on `POST /auth/login` via `slowapi` (5/minute per IP, `app/rate_limit.py`), with a custom 429 handler matching the app's `{"detail": ...}` convention. Tests reset the limiter's shared in-memory state before every test (autouse fixture) since it lives on the single `app` instance and the suite logs in dozens of times.
  - Global 404/403/500 handlers (`app/main.py`) render friendly HTML pages (`404.html`, `403.html`, `500.html`) when the request looks like a real browser navigation (`Accept: text/html`), and fall back to the existing plain JSON otherwise — so none of the app's JS `fetch()` calls changed behavior. This also fixed real gaps: a nurse hitting `/admin` or a bad patient URL previously got raw JSON even when browsing.
  - `scripts/seed_demo.py`: new **non-interactive** script (2 facilities, 4 users, 3 demo patients, 10 drug interactions) for the README's quick-start path — distinct from Phase 1's interactive `seed_facility.py`, which is for real one-time onboarding. The interaction data is well-documented textbook examples (aspirin+warfarin, sildenafil+nitrates, etc.); worth a sanity check from you before it's used beyond local demoing.
  - `README.md`: local setup, testing, and deployment notes (single VPS + PostgreSQL + Caddy/Nginx + systemd, no Docker) per spec
  - `tests/test_rate_limit.py`, `tests/test_error_pages.py` (8 new tests): 6th login attempt in a minute returns 429, HTML vs. JSON for 404/403/500 depending on the `Accept` header
  - **Verified the "fresh clone → under 10 minutes" acceptance criterion for real**: cloned the repo into a scratch directory and followed the README's own instructions end-to-end (venv, install, migrate, seed, run, log in, search a demo patient, and reproduce the aspirin/warfarin block). Total time ~4–5 minutes (venv 59s, `pip install` 177s, migrate+seed 20s). Found and fixed one real bug this way: `seed_demo.py`'s em-dash characters rendered as mojibake in a default Windows console codepage — replaced with plain hyphens.

## 3D UI rewrite (post-Phase-6 initiative, tracked outside the VITALIS_SPEC.md phase list)

Decided 2026-08-19: founder wants a full 3D immersive, patient-centric rewrite — a React
frontend with a 3D patient body/avatar visualization (chronic conditions shown as spatial
markers on the body; allergies/medications/records in a conventional side panel, since
they don't have a real anatomical location). This is a full frontend rewrite: the FastAPI
backend becomes a pure JSON API, React replaces Jinja2/vanilla JS entirely. Rolling out in
parallel with the current app (nothing breaks until cutover) via this sub-roadmap:

- **Phase 7 — Backend JSON API readiness (DONE, this entry)**
  - `app/services/content_negotiation.py`: `wants_json(request)`, the JSON-side
    counterpart to Phase 6's HTML-error-page negotiation
  - `GET /auth/me` (new endpoint — the one thing genuinely missing, not duplicated):
    returns the logged-in user's profile including `facility_name`
  - Made four existing page routes content-negotiate on the same URL — JSON if
    `Accept: application/json`, otherwise the exact same HTML as before (fully
    backward-compatible; nothing today sends that header, so zero behavior change for
    existing callers): `GET /patients/{id}` (full summary), `GET
    /patients/{id}/timeline`, `GET /patients/{id}/access-history`, `GET /admin`. `GET
    /logout` similarly returns a JSON confirmation instead of a redirect when asked.
  - New schemas: `UserMeOut`, `ConditionOut`, `RecordDetailOut`, `PatientDetailOut`,
    `MedicationDetailOut`, `AdminDashboardOut`, `AccessHistoryEntryOut`/`PageOut`
  - Centralized the "not consented" message (`CONSENT_DENIED_DETAIL`), previously
    duplicated as a string constant in three router files, into `patient_access.py`
  - `tests/test_auth.py`, `test_patients.py`, `test_records.py`, `test_access_history.py`,
    `test_admin_dashboard.py` (12 new tests): JSON shape matches HTML page's data, same
    audit-writing/consent-gate behavior in both modes, HTML mode unaffected
  - Manually verified against the real dev server: `/auth/me`, JSON patient detail
    (allergies/conditions/medications), JSON timeline, JSON access-history, JSON admin
    dashboard, and JSON logout (with a real cookie-jar round-trip confirming the cookie
    actually clears) — all while confirming the old HTML pages still render identically
  - No new libraries, no migration — pure response-shaping on existing data
- **Phase 8 — React app shell (2D)**: not started. Scaffold `frontend/` (Vite + plain JS
  + React, no TypeScript by default), recreate login/dashboard/patient
  search-create-summary/admin/timeline/access-history as React components calling the
  Phase 7 JSON endpoints. Functional parity with the current app before any 3D work.
- **Phase 9 — 3D patient visualization**: not started. react-three-fiber + Three.js; body
  model sourcing and the condition-to-body-region mapping (leaning toward a manual
  "body region" field on Condition rather than guessing from free text) still need
  deciding.
- **Phase 10 — Polish, mobile, cutover**: not started. Phone performance testing (a WebGL
  scene is a real risk on low-end phones), README/deploy updates for the Node build step,
  retire the Jinja2 templates only once parity is confirmed.

## Blockers
- None. Note: port 8000 on this machine is occupied by Docker Desktop/WSL port-forwarding (unrelated to this project) — local dev server testing used port 8001 instead.

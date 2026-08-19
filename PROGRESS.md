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
- **Phase 8 — React app shell (2D) — DONE**
  - `frontend/`: Vite + plain JS + React (no TypeScript) + react-router-dom, scaffolded
    with `npm create vite@latest`
  - Pages: `LoginPage`, `DashboardPage`, `PatientNewPage`, `PatientSummaryPage` (allergy
    banner + inline add-allergy/medication/record forms + stop-medication, replicating
    the Jinja2 page's `window.prompt` override-reason flow for blocked medications),
    `PatientTimelinePage`, `AccessHistoryPage` (with pagination), `AdminDashboardPage`
    (staff list, add/deactivate, counts) — full functional parity with the current app
  - `src/api.js`: thin fetch wrapper always sending `Accept: application/json` +
    `credentials: 'same-origin'`; `src/AuthContext.jsx`: current-user state via
    `GET /auth/me`, used by `ProtectedRoute` for route guarding (including role checks)
  - `vite.config.js`: dev-server proxy to the backend (port 8001), with a `bypass`
    function that inspects the `Accept` header — a real browser navigation to e.g.
    `/patients/:id` falls through to Vite's own SPA shell, while the app's own
    `Accept: application/json` fetches get proxied to FastAPI. **No backend changes
    were needed for this** — Phase 7's content-negotiation design turned out to be
    exactly right for it. (Production won't need this at all: the built SPA will be
    served by FastAPI itself, same-origin, no proxy.)
  - `styles.css` ported from `app/static/style.css` unchanged (same brand colors, same
    `.allergy-banner`/`.interaction-warning-banner`/`.form-error` classes)
  - 8 Vitest + React Testing Library tests: `api.js` request/error-shape behavior,
    unauthenticated redirect to `/login`, admin-only dashboard link visibility,
    login-page error display and API-call shape
  - Verified against the real backend with both dev servers running: login and
    `/auth/me` through the proxy, and — the key architectural test — hit the exact same
    URL (`/patients/{id}`) twice, once with `Accept: application/json` (proxied to
    FastAPI, got JSON) and once without (Vite served its own `index.html`), confirming
    the dual-purpose routing actually works end to end, not just in theory
  - Old Jinja2 app fully untouched; `pytest` still 70/70
- **Phase 9 — 3D patient visualization — DONE**
  - Resolved the two open decisions from the Phase 8 notes: **body model** is a simple
    procedural low-poly figure built from Three.js primitives (sphere head, cylinder
    torso/pelvis/limbs) — no external asset, no licensing question, trivial for one
    person to tweak. **Condition-to-region mapping** is a manual `body_region` field
    (enum: head/chest/abdomen/pelvis/left_arm/right_arm/left_leg/right_leg/back/general)
    picked when adding a condition, rather than guessing from free text — systemic
    conditions (e.g. diabetes) can be left unset rather than forced onto a fake location.
  - **New backend capability, not just plumbing**: conditions had no creation endpoint
    at all before this (only ever inserted directly in tests/seed data) — added
    `POST /patients/{id}/conditions` (`app/routers/conditions.py`), `body_region` column
    + migration `d6e08c880ceb`, `ConditionCreate`/`ConditionOut` moved into their own
    `app/schemas/condition.py` (previously `ConditionOut` lived inline in
    `schemas/patient.py`, inconsistent with every other domain having its own file).
    Same consent gate as allergies/medications/records; no audit action (none exists in
    the enum for this, same reasoning as allergy-add).
  - Added a matching "Add condition" form to the **old Jinja2 page too** (not just
    React) so both apps stay at parity — cheap, and avoids the old app looking
    incomplete next to the new capability.
  - `frontend/src/components/Body3D.jsx`: react-three-fiber `<Canvas>`, clickable
    markers positioned per `body_region`, click-to-toggle an HTML tooltip (via drei)
    showing name/diagnosed date/notes. Conditions with no `body_region` are left off the
    3D view and still shown in the existing plain-text conditions list — a WebGL-free
    fallback that costs nothing and hedges the phone-performance risk Phase 10 is meant
    to address properly.
  - `tests/test_conditions.py` (4 backend tests): create with/without body_region,
    appears correctly in the JSON patient detail, consent gate blocks cross-facility add.
    `Body3D.test.jsx` (2 tests): the empty-state path (no localized conditions) is real
    since it returns before touching `<Canvas>`; the populated path mocks
    `@react-three/fiber`/`@react-three/drei` since jsdom has no WebGL context to test
    against for real — full rendering/interaction genuinely needs a browser.
  - `seed_demo.py` updated with conditions across all three demo patients (including one
    deliberately left as `body_region=None` to demonstrate the systemic case)
  - Manually verified end-to-end with both dev servers: seeded conditions appear
    correctly in the JSON patient detail, added a new condition via `curl` and confirmed
    it rendered correctly on the **old** Jinja2 page (parity check), then re-verified the
    same patient's condition data (including `body_region`) flows correctly through the
    Vite dev proxy that Phase 8 built — the exact data `Body3D` consumes. (Caught and
    correctly diagnosed a `curl` cookie-jar artifact along the way — `127.0.0.1` and
    `localhost` are different hosts to curl's cookie store, not an app bug.)
  - Known tradeoff for Phase 10: the production JS bundle is ~1.16MB (320KB gzipped)
    now that Three.js is in it — fine on a dev machine, a real risk on the low-end
    phones this app targets. Code-splitting so the 3D bundle only loads on the patient
    page (not login/dashboard) is Phase 10's job, not fixed here.
  - Old Jinja2 app and all Phase 1–8 backend behavior unaffected; `pytest` 74/74,
    frontend Vitest 10/10, both dev-mode and production builds verified
- **Phase 10 — Polish, mobile, cutover — mostly done; cutover itself deliberately not done**
  - **Route-based code splitting** (`App.jsx`, `React.lazy` + `Suspense`): the Three.js
    bundle now only loads when a patient page is actually visited. Measured, not just
    claimed — production build before this change: one 1.16MB bundle for every page.
    After: login/dashboard/admin dropped to ~1–3KB each (~75KB shared base), with the
    heavy ~916KB (244KB gzipped) chunk isolated to the patient page alone.
  - **WebGL detection** (`hasWebGL.js`): `Body3D` checks support before attempting to
    render and falls back to the existing plain-text conditions list if it's missing,
    instead of a blank canvas or console errors.
  - **Error boundary** (`ErrorBoundary.jsx`): wraps `Body3D` on the patient page so a
    runtime Three.js failure degrades to a fallback message instead of blanking the
    whole page.
  - **Canvas perf settings**: `dpr={[1, 2]}` caps device pixel ratio (avoids full native
    DPR — 3x+ on some phones — driving up fill-rate cost), `frameloop="demand"` stops
    the continuous 60fps render loop for this mostly-static scene (drei's `OrbitControls`
    still triggers re-renders on interaction automatically under `demand` mode). Canvas
    height also drops on narrow viewports via a media query.
  - **Honest limit on verification**: none of the above was profiled on a real low-end
    phone — no device/browser tooling is available in this environment (same constraint
    noted since Phase 6). These are the standard, well-documented react-three-fiber
    mitigations for exactly this risk, applied deliberately rather than skipped, but they
    are not a substitute for testing on an actual device before any cutover decision.
  - **README**: documented the production deployment path for the frontend (`npm run
    build` → static files served by Caddy/Nginx, API routes reverse-proxied to FastAPI —
    the production equivalent of the Vite dev proxy from Phase 8) with an example
    Caddyfile.
  - **Cutover (making React the default app, retiring the Jinja2 templates) was
    deliberately NOT done.** That's a product decision about the live app, not a routine
    implementation step, and depends on verifying real-device behavior this environment
    can't do — it needs your explicit go-ahead once you've tried it on an actual phone.
    Both apps currently run side by side against the same backend/database; nothing
    about today's work forces that decision either way.
  - 13 frontend tests (3 new: WebGL-unavailable fallback, error-boundary catch/no-catch),
    `pytest` untouched at 74/74 (no backend changes this phase), both dev-mode and
    production builds verified against the real backend + demo data through the full
    stack (login → search → patient page → all new JS modules serving without error)

## Blockers
- None. Note: port 8000 on this machine is occupied by Docker Desktop/WSL port-forwarding (unrelated to this project) — local dev server testing used port 8001 instead.

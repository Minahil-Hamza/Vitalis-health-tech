# Vitalis — Progress

## Done
- Phase 0: project skeleton
  - `app/` package with `main.py` (FastAPI app + `GET /health`), `config.py` (pydantic-settings), `database.py` (SQLAlchemy engine/session/Base)
  - Empty `models/`, `schemas/`, `routers/`, `services/` packages ready for Phase 1
  - `app/templates/` and `app/static/style.css` (brand colors: primary `#0E7A5F`, warning `#C4331B`) and `app.js` placeholders
  - `tests/test_health.py`: dummy test + `/health` test
  - `.env.example`, `.env` (gitignored), `.gitignore`, `requirements.txt`
  - Own git repo initialized inside `Vitalis/` (previously the folder had no repo of its own; a stray repo rooted at the Windows user profile was in use — not used for this project)

## Next
- Phase 1: Auth & facilities — facility seed script, `POST /auth/login` (JWT), `require_role()` dependency, login page, audit log on login/login_failed. Waiting for go-ahead.

## Blockers
- None.

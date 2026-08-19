# Vitalis

One patient, one record. A centralized electronic health record (EHR) platform for
Pakistani clinics — patients are identified by CNIC and shared across facilities with
consent and a full audit trail, plus drug-interaction and allergy safety checks.

See `Vitalis.md` for the full product and technical specification.

## Local setup

Requires Python 3.12.

```bash
git clone <this-repo-url> vitalis
cd vitalis

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux

alembic upgrade head
python scripts/seed_demo.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/login and sign in with any of the demo accounts printed by
`seed_demo.py` (all use the password `Demo1234!`), for example:

- `admin@citycare.demo` — admin at City Care Clinic (Lahore)
- `doctor@citycare.demo` — doctor at City Care Clinic
- `admin@alshifa.demo` — admin at Al-Shifa Clinic (Karachi)
- `pharmacist@alshifa.demo` — pharmacist at Al-Shifa Clinic

Three demo patients are seeded, including one (Usman Tariq, CNIC `35201-9988776-3`)
already on warfarin — try adding aspirin for him from either facility's login to see the
drug-interaction safety check block the save. All three have a few chronic conditions
seeded with a body region, for the React frontend's 3D visualization (see below).

### Running tests

```bash
pytest
```

## React frontend (in progress, not yet the default app)

A React rewrite lives in `frontend/`, being built in parallel with the app above per the
roadmap in `PROGRESS.md` — nothing here replaces the Jinja2 app until it reaches full
parity and a deliberate cutover. Covers login/dashboard/patient/admin pages, plus a 3D
patient view (react-three-fiber) on the patient summary page showing chronic conditions
as clickable markers on a stylized body — click a marker to see its details.

Requires Node.js (v20+) and the backend running per the steps above.

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173/) and log in with any seeded
demo account. The dev server proxies API calls to the backend on port 8001 — start the
backend with `uvicorn app.main:app --reload --port 8001` if you're running both at once.

```bash
npm test    # Vitest + React Testing Library
npm run build
```

## Project structure

```
app/
├── main.py            # FastAPI app entry, error handlers, rate limiter
├── config.py           # Settings from .env
├── database.py          # SQLAlchemy engine/session/Base
├── models/              # One file per domain
├── schemas/              # Pydantic request/response schemas
├── routers/               # Routes, one file per domain
├── services/               # Auth, audit, safety-check business logic
├── templates/                # Jinja2 HTML
└── static/                    # style.css, app.js
alembic/                        # Migrations
scripts/
├── seed_facility.py             # Interactive: create the first real facility + admin
└── seed_demo.py                  # Non-interactive: demo dataset (this README's path)
tests/
frontend/                         # React rewrite, in progress — see the section above
```

## Deployment notes

Vitalis has no hard dependency on Docker or any particular cloud provider. A minimal,
boring deployment:

1. **Server**: a single small VPS (e.g. 1–2 vCPU, 2GB RAM is plenty for a handful of
   clinics). Ubuntu LTS is a safe default.
2. **Database**: PostgreSQL instead of SQLite in production. Set `DATABASE_URL` in
   `.env` to a `postgresql://` connection string and add `psycopg2-binary` to
   `requirements.txt` — the app's models use portable SQLAlchemy types throughout, so no
   code changes are needed beyond that.
3. **Process manager**: run `uvicorn app.main:app` (or `gunicorn -k
   uvicorn.workers.UvicornWorker app.main:app`) under `systemd`, so it restarts on crash
   and on server reboot.
4. **Reverse proxy + TLS**: Caddy or Nginx in front of uvicorn, terminating HTTPS and
   proxying to `127.0.0.1:8000`. Caddy is the simpler option — it handles Let's Encrypt
   certificates automatically with a two-line Caddyfile.
5. **Migrations on deploy**: run `alembic upgrade head` before restarting the app
   service, so the schema is current before new code runs against it.
6. **Secrets**: set a strong, unique `SECRET_KEY` in the production `.env` (never reuse
   the dev value) and keep `.env` out of version control (already covered by
   `.gitignore`).

No Docker is required for v1. If you later want containers, the app is stateless aside
from the database, so a straightforward `Dockerfile` running `uvicorn` would work without
restructuring anything.

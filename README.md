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

**Bundle size / phone performance**: `npm run build` code-splits by route, so the 3D
patient view's Three.js dependency (the bulk of the bundle) only downloads when someone
actually opens a patient page — login/dashboard/admin stay small (~75KB gzipped each).
`Body3D` also checks for WebGL support before attempting to render, falling back to the
plain-text conditions list on a device/browser without it, and is wrapped in an error
boundary so a runtime WebGL failure degrades gracefully instead of blanking the page.
The Canvas itself caps its device pixel ratio (`dpr={[1, 2]}`) and only re-renders on
interaction (`frameloop="demand"`) rather than a continuous 60fps loop, since the scene
is mostly static. None of this was measured on a real low-end phone (no device/browser
tooling available while building it) — it's the standard set of react-three-fiber
mitigations for exactly this risk, not a substitute for testing on an actual device
before this becomes the default app.

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

### Deploying the React frontend (once it's ready to go live)

The frontend isn't wired up as the default app yet — see "React frontend" above and the
roadmap in `PROGRESS.md`. When it is, deployment doesn't need Node.js running as a
service: `npm run build` produces static files in `frontend/dist/` that Caddy/Nginx can
serve directly, with API routes reverse-proxied to the FastAPI backend — the same
Accept-header-based split the Vite dev proxy does locally, just handled by the production
reverse proxy instead. Example Caddyfile:

```
vitalis.example.com {
    root * /srv/vitalis/frontend/dist
    file_server

    @api path /auth/* /logout /patients/* /admin/*
    reverse_proxy @api 127.0.0.1:8000

    try_files {path} /index.html
}
```

`try_files ... /index.html` is what makes client-side routes like `/patients/:id` work on
a hard refresh — same purpose as Vite's dev-time SPA fallback. Rebuild and redeploy
`frontend/dist/` as part of your normal deploy step, same as running migrations.

**Cutting over** — making the React app the one real users land on, and retiring the
Jinja2 templates — is a deliberate decision for you to make once you've confirmed it
covers everything you need on a real device, not something to flip silently as part of
routine development. Until then, both apps keep working side by side against the same
backend and database.

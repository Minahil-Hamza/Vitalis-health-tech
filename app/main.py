"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import allergies, auth, medications, pages, patients, records

app = FastAPI(title="Vitalis")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(patients.router)
app.include_router(records.router)
app.include_router(medications.router)
app.include_router(allergies.router)


@app.get("/health")
def health_check():
    """Return service status for uptime checks."""
    return {"status": "ok"}

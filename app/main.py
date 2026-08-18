"""FastAPI application entry point."""
from fastapi import FastAPI

app = FastAPI(title="Vitalis")


@app.get("/health")
def health_check():
    """Return service status for uptime checks."""
    return {"status": "ok"}

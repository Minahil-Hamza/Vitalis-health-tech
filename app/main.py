"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.rate_limit import limiter
from app.routers import admin, allergies, auth, medications, pages, patients, records

app = FastAPI(title="Vitalis")
app.state.limiter = limiter

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(patients.router)
app.include_router(records.router)
app.include_router(medications.router)
app.include_router(allergies.router)
app.include_router(admin.router)

error_templates = Jinja2Templates(directory="app/templates")
HTML_ERROR_TEMPLATES = {404: "404.html", 403: "403.html"}


def _wants_html(request: Request) -> bool:
    """True for a real browser navigation, false for our own JS fetch() calls (which don't send this)."""
    return "text/html" in request.headers.get("accept", "")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return the same {"detail": ...} shape used everywhere else, so error banners read correctly."""
    return JSONResponse(
        status_code=429, content={"detail": "Too many attempts. Please wait a minute and try again."}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Render a friendly HTML page for browser navigations; keep JSON for API/JS callers."""
    template_name = HTML_ERROR_TEMPLATES.get(exc.status_code)
    if template_name and _wants_html(request):
        return error_templates.TemplateResponse(request, template_name, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak a traceback: a friendly page for browsers, a generic message for API callers."""
    if _wants_html(request):
        return error_templates.TemplateResponse(request, "500.html", status_code=500)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health_check():
    """Return service status for uptime checks."""
    return {"status": "ok"}

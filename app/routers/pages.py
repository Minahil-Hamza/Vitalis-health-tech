"""Simple authenticated HTML pages."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.services.security import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user)):
    """Show a minimal landing page proving login and route protection work end-to-end."""
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})

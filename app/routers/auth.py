"""Login/logout routes: a JSON API endpoint plus the browser-facing login page."""
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.audit import log_action
from app.services.security import create_access_token, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "access_token"


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(credentials: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """Verify credentials, return a JWT, set it as a cookie, and audit the attempt."""
    ip_address = request.client.host if request.client else None
    user = db.query(User).filter(User.email == credentials.email).first()

    if user is None or not user.is_active or not verify_password(credentials.password, user.password_hash):
        log_action(
            db,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id if user else None,
            facility_id=user.facility_id if user else None,
            ip_address=ip_address,
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid email or password"}
        )

    token = create_access_token(user)
    log_action(db, action=AuditAction.LOGIN, user_id=user.id, facility_id=user.facility_id, ip_address=ip_address)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.access_token_expire_hours * 3600,
        samesite="lax",
    )
    return TokenResponse(access_token=token)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Render the login form."""
    return templates.TemplateResponse(request, "login.html")


@router.get("/logout")
def logout():
    """Clear the auth cookie and send the user back to the login page."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(COOKIE_NAME)
    return response

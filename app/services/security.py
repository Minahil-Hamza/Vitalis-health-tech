"""Password hashing, JWT helpers, and auth dependencies for route protection."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import Role, User

JWT_ALGORITHM = "HS256"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash."""
    return _pwd_context.verify(password, password_hash)


def create_access_token(user: User) -> str:
    """Create a signed JWT for a logged-in user, valid for the configured expiry."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    payload = {
        "user_id": user.id,
        "facility_id": user.facility_id,
        "role": user.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT, raising JWTError if it is invalid or expired."""
    return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])


def _extract_token(authorization: Optional[str], access_token_cookie: Optional[str]) -> Optional[str]:
    """Pull a bearer token from the Authorization header, falling back to the access_token cookie."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return access_token_cookie


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the logged-in user from the request's JWT (Authorization header or cookie)."""
    token = _extract_token(authorization, access_token)
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not token:
        raise unauthorized
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise unauthorized
    user = db.get(User, payload.get("user_id"))
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_role(allowed_roles: list[Role]):
    """Build a dependency that only allows users whose role is in allowed_roles."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted for this role")
        return user

    return _check

"""Account and session operations (PostgreSQL)."""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import storage
from src.auth.passwords import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    burn_verification_time,
    hash_password,
    needs_rehash,
    verify_password,
)
from src.config import get_settings
from src.db.models import LoginSession, User, utcnow
from src.errors import ApiError, conflict, validation_error

logger = logging.getLogger(__name__)

SESSION_TOUCH_INTERVAL = timedelta(hours=1)


def normalize_email(email: str) -> str:
    try:
        return validate_email(email.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise validation_error({"email": f"Invalid email: {exc}"})


def check_password(password: str, email: str = "") -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise validation_error({"password": f"Password must have at least {MIN_PASSWORD_LENGTH} characters"})
    if len(password) > MAX_PASSWORD_LENGTH:
        raise validation_error({"password": f"Password must have at most {MAX_PASSWORD_LENGTH} characters"})
    if email and password.lower() == email.lower():
        raise validation_error({"password": "Password must not be your email"})


def create_user(session: Session, email: str, password: str, is_admin: bool = False) -> User:
    """Create the account and its game save. The save is removed again if anything fails."""
    email = normalize_email(email)
    check_password(password, email)

    user = User(email=email, password_hash=hash_password(password), is_admin=is_admin)
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise conflict("This email is already registered", {"email": "This email is already registered"})

    try:
        storage.create_player(user.id, storage.default_player_name(email))
    except Exception:
        session.rollback()
        raise
    logger.info("Created account %s (id %s, admin=%s)", email, user.id, is_admin)
    return user


def register_user(session: Session, email: str, password: str, confirm_password: str) -> User:
    if not get_settings().registration_enabled:
        raise ApiError(403, "registration_disabled", "Registration is disabled")
    if password != confirm_password:
        raise validation_error({"confirmPassword": "Passwords do not match"})
    return create_user(session, email, password)


def authenticate(session: Session, email: str, password: str) -> User:
    invalid = ApiError(401, "invalid_credentials", "Invalid email or password")
    try:
        email = normalize_email(email)
    except ApiError:
        burn_verification_time(password)
        raise invalid

    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        burn_verification_time(password)
        raise invalid
    if not verify_password(user.password_hash, password):
        raise invalid
    if not user.is_active:
        raise ApiError(403, "account_disabled", "This account is disabled")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = utcnow()
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def start_session(session: Session, user: User, ip: Optional[str], user_agent: Optional[str]) -> str:
    """Create a login session and return the (unhashed) cookie token."""
    token = secrets.token_urlsafe(32)
    now = utcnow()
    session.add(LoginSession(
        token_hash=_hash_token(token),
        user_id=user.id,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=get_settings().session_days),
        ip=(ip or "")[:64] or None,
        user_agent=(user_agent or "")[:255] or None,
    ))
    return token


def resolve_session(session: Session, token: str) -> Optional[User]:
    """Return the active user behind a cookie token, refreshing the session when it is old."""
    login = session.get(LoginSession, _hash_token(token))
    if login is None:
        return None

    now = utcnow()
    expires_at = login.expires_at if login.expires_at.tzinfo else login.expires_at.replace(tzinfo=now.tzinfo)
    if expires_at <= now:
        session.delete(login)
        return None

    user = session.get(User, login.user_id)
    if user is None or not user.is_active:
        return None

    last_seen = login.last_seen_at if login.last_seen_at.tzinfo else login.last_seen_at.replace(tzinfo=now.tzinfo)
    if now - last_seen > SESSION_TOUCH_INTERVAL:
        login.last_seen_at = now
        login.expires_at = now + timedelta(days=get_settings().session_days)
    return user


def end_session(session: Session, token: str) -> None:
    session.execute(delete(LoginSession).where(LoginSession.token_hash == _hash_token(token)))


def end_all_sessions(session: Session, user_id: int) -> None:
    session.execute(delete(LoginSession).where(LoginSession.user_id == user_id))


def purge_expired_sessions(session: Session) -> int:
    result = session.execute(delete(LoginSession).where(LoginSession.expires_at <= utcnow()))
    return result.rowcount or 0


def ensure_player(user: User) -> None:
    """Recreate the game save if it is missing (e.g. after a database restore)."""
    if not storage.player_exists(user.id):
        storage.create_player(user.id, storage.default_player_name(user.email))
        logger.warning("Recreated the missing game save of account %s", user.id)


def ensure_admin(session: Session, email: str, password: str) -> Optional[User]:
    """Create the bootstrap admin from the environment if it does not exist yet."""
    if not email or not password:
        return None
    email = normalize_email(email)
    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        return existing
    return create_user(session, email, password, is_admin=True)


def user_to_dict(user: User, player: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    data: Dict[str, object] = {
        "id": user.id,
        "email": user.email,
        "isAdmin": user.is_admin,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
    }
    if player is not None:
        data["player"] = player
    return data

"""SQLAlchemy models for accounts and login sessions."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# BigInteger primary keys must be plain INTEGER on SQLite to auto-increment (used by the tests).
PrimaryKey = BigInteger().with_variant(Integer, "sqlite")

# Player ids start above the ids of the bundled PvP opponents (100000050...).
FIRST_PLAYER_ID = 200000000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    """An account. Its ``id`` is also the in-game player id (``fb_sig_user``)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PrimaryKey, Identity(start=FIRST_PLAYER_ID), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["LoginSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class LoginSession(Base):
    """A browser login. Only the SHA-256 of the cookie token is stored."""

    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(PrimaryKey, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class Friendship(Base):
    """A friendship (neighbours in the game) between two accounts.

    The pair is stored once, ordered (``low_id`` < ``high_id``), so it cannot be duplicated in
    the other direction. ``requester_id`` remembers who asked, for the pending/accepted flow.
    """

    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("low_id", "high_id", name="uq_friendship_pair"),
        CheckConstraint("low_id < high_id", name="ck_friendship_ordered"),
    )

    id: Mapped[int] = mapped_column(PrimaryKey, Identity(start=1), primary_key=True)
    low_id: Mapped[int] = mapped_column(PrimaryKey, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    high_id: Mapped[int] = mapped_column(PrimaryKey, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    requester_id: Mapped[int] = mapped_column(PrimaryKey, ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), default="accepted", server_default="accepted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AppSetting(Base):
    """A server-wide setting changed from the admin panel (a key/value pair)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
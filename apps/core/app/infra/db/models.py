from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.schema import Base

class GoogleOAuthToken(Base):
    __tablename__ = "google_oauth_tokens"

    # v0.1: один пользователь/один аккаунт. Позже добавим user_id/tenant.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Bearer")
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    expiry_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

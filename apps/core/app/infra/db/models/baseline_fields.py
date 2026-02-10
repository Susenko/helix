from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, Integer, Boolean, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.schema import Base


class BaselineField(Base):
    """
    BaselineField = фон/ландшафт.

    Пример:
      - Jutly (работа, коммуникации+код)
      - Filmax (созидание, deep work)
      - Household (быт: продукты, счета)
      - Health (спорт, сон)
    """

    __tablename__ = "baseline_fields"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)           # "Jutly"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # режим по умолчанию для этого поля
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="any")

    # Цели/квоты (минуты в неделю) — чтобы фон был "обслужен"
    min_quota_min_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_quota_min_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Предпочтительные окна (простая структура, потом расширим)
    # пример:
    # {
    #   "timezone": "Europe/Bucharest",
    #   "windows": [
    #     {"days": ["mon","tue","wed","thu","fri"], "start":"10:00", "end":"12:00"}
    #   ]
    # }
    preferred_windows: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("mode IN ('any','focus','admin','reflect')", name="ck_baseline_fields_mode"),
        CheckConstraint("min_quota_min_per_week >= 0", name="ck_baseline_fields_min_quota"),
        CheckConstraint("max_quota_min_per_week >= 0", name="ck_baseline_fields_max_quota"),
    )

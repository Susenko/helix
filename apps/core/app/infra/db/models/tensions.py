from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.schema import Base


class Tension(Base):
    __tablename__ = "tensions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # связь с фоном (необязательно)
    field_id: Mapped[int | None] = mapped_column(
        ForeignKey("baseline_fields.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)

    # стадия жизни напряжения (не task-status)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="held")

    # давление (0..5 или 1..5)
    charge: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # вектор формы
    vector: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")

    # момент возврата
    return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # периодика (если это “полевое”/циклическое)
    cadence: Mapped[str | None] = mapped_column(Text, nullable=True)  # 'daily'|'weekly'|'monthly'
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    events: Mapped[list["TensionEvent"]] = relationship(
        "TensionEvent",
        back_populates="tension",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("status IN ('held','forming','released','parked','dropped')", name="ck_tensions_status"),
        CheckConstraint("charge BETWEEN 0 AND 5", name="ck_tensions_charge"),
        CheckConstraint(
            "vector IN ('unknown','action','message','meeting','focus_block','decision','research','delegate','drop')",
            name="ck_tensions_vector",
        ),
        CheckConstraint(
            "cadence IS NULL OR cadence IN ('daily','weekly','monthly')",
            name="ck_tensions_cadence",
        ),
    )

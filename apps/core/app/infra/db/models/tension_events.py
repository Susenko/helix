from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.schema import Base

if TYPE_CHECKING:
    from app.infra.db.models.tensions import Tension


class TensionEvent(Base):
    __tablename__ = "tension_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tension_id: Mapped[int] = mapped_column(
        ForeignKey("tensions.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False, default="helix")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    tension: Mapped["Tension"] = relationship("Tension", back_populates="events")

    __table_args__ = (
        CheckConstraint(
            "type IN ("
            "'captured','edited','charge_changed','vector_changed','stage_changed',"
            "'return_scheduled','returned','postponed','accepted','rejected',"
            "'form_proposed','form_chosen','form_applied','released','dropped'"
            ")",
            name="ck_tension_events_type",
        ),
        CheckConstraint("actor IN ('user','helix','system')", name="ck_tension_events_actor"),
    )

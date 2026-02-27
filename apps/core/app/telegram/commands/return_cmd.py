from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.tension_events import TensionEvent
from app.infra.db.models.tensions import Tension
from app.infra.db.session import SessionLocal


@dataclass
class ReturnResult:
    tension: Tension | None
    reason: str


def _now_utc() -> datetime:
    return datetime.utcnow()


def _suggest_form(vector: str) -> str:
    v = (vector or "unknown").lower().strip()
    if v == "message":
        return "Сделать черновик сообщения?"
    if v == "action":
        return "Сделать 5 минут сейчас?"
    if v == "decision":
        return "Принять решение сейчас или поставить 15 минут фокуса?"
    return "15 минут фокуса сегодня?"


async def pick_tension_for_return(session: AsyncSession) -> ReturnResult:
    """
    V1:
    1) due (return_at <= now) -> earliest due
    2) else highest charge, then oldest
    """
    now = _now_utc()
    active_filter = Tension.status.in_(("held", "forming"))

    q_last_returned = (
        select(TensionEvent.tension_id)
        .where(
            and_(
                TensionEvent.type == "returned",
                TensionEvent.actor == "helix",
            )
        )
        .order_by(TensionEvent.created_at.desc(), TensionEvent.id.desc())
        .limit(1)
    )
    last_returned_result = await session.execute(q_last_returned)
    last_returned_id = last_returned_result.scalar_one_or_none()

    q_due = (
        select(Tension)
        .where(
            and_(
                active_filter,
                Tension.return_at.is_not(None),
                Tension.return_at <= now,
            )
        )
        .order_by(Tension.return_at.asc(), Tension.created_at.asc())
        .limit(2 if last_returned_id is not None else 1)
    )
    due_result = await session.execute(q_due)
    due_items = list(due_result.scalars().all())
    t_due = next((item for item in due_items if item.id != last_returned_id), None)
    if t_due is None and due_items:
        t_due = due_items[0]
    if t_due:
        reason = "due_no_repeat" if t_due.id != last_returned_id else "due"
        return ReturnResult(tension=t_due, reason=reason)

    q_top = (
        select(Tension)
        .where(active_filter)
        .order_by(Tension.charge.desc(), Tension.created_at.asc())
        .limit(2 if last_returned_id is not None else 1)
    )
    top_result = await session.execute(q_top)
    top_items = list(top_result.scalars().all())
    t_top = next((item for item in top_items if item.id != last_returned_id), None)
    if t_top is None and top_items:
        t_top = top_items[0]
    if t_top:
        reason = "top_score_no_repeat" if t_top.id != last_returned_id else "top_score"
        return ReturnResult(tension=t_top, reason=reason)

    return ReturnResult(tension=None, reason="empty")


async def log_return_event(session: AsyncSession, tension: Tension) -> None:
    now = _now_utc()
    event = TensionEvent(
        tension_id=tension.id,
        type="returned",
        actor="helix",
        payload={
            "reason": "telegram_return",
            "vector": tension.vector,
            "charge": tension.charge,
            "status": tension.status,
        },
        created_at=now,
    )
    session.add(event)

    if hasattr(tension, "last_returned_at"):
        setattr(tension, "last_returned_at", now)
    if hasattr(tension, "return_count"):
        current_count = getattr(tension, "return_count") or 0
        setattr(tension, "return_count", current_count + 1)
    if hasattr(tension, "updated_at"):
        setattr(tension, "updated_at", now)

    await session.commit()


def format_return_message(tension: Tension, reason: str) -> str:
    suggestion = _suggest_form(tension.vector)
    return (
        "🔁 Возврат напряжения\n\n"
        f"#{tension.id} | {tension.title}\n"
        f"status={tension.status} | charge={tension.charge} | vector={tension.vector}\n"
        f"reason={reason}\n\n"
        f"Форма: {suggestion}\n\n"
        "Ответь:\n"
        "✅ 'accept' - беру в работу\n"
        "🕒 'postpone 2h' - отложить на 2 часа\n"
        "🗑 'drop' - отпустить"
    )


async def cmd_return(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is None:
        return

    async with SessionLocal() as session:
        picked = await pick_tension_for_return(session)
        if not picked.tension:
            await update.message.reply_text("Пока нет активных напряжений. /add чтобы добавить.")
            return

        await log_return_event(session, picked.tension)
        await update.message.reply_text(format_return_message(picked.tension, picked.reason))

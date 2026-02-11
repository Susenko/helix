from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.tensions import Tension
from app.infra.db.models.tension_events import TensionEvent


class TensionsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tension(
        self,
        *,
        title: str,
        note: Optional[str] = None,
        charge: int = 3,
        vector: str = "unknown",
        status: str = "held",
        actor: str = "user",
    ) -> Tension:
        now = datetime.utcnow()

        t = Tension(
            title=title,
            charge=charge,
            vector=vector,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self.session.add(t)
        await self.session.flush()  # получаем t.id

        ev = TensionEvent(
            tension_id=t.id,
            type="captured",
            actor=actor,
            payload={
                "title": title,
                "note": note,
                "charge": charge,
                "vector": vector,
                "status": status,
            },
            created_at=now,
        )
        self.session.add(ev)

        await self.session.commit()
        await self.session.refresh(t)
        return t

    async def list_active(self, limit: int = 50) -> list[Tension]:
        # active = не завершено и не dropped
        q = (
            select(Tension)
            .where(Tension.status.in_(("held", "forming")))
            .order_by(Tension.created_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def get_by_id(self, tension_id: int) -> Tension | None:
        q = select(Tension).where(Tension.id == tension_id)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def update_tension(
        self,
        tension_id: int,
        *,
        charge: int | None = None,
        vector: str | None = None,
        status: str | None = None,
        actor: str = "user",
    ) -> Tension | None:
        t = await self.get_by_id(tension_id)
        if not t:
            return None

        now = datetime.utcnow()
        changed = False

        if charge is not None and charge != t.charge:
            prev = t.charge
            t.charge = charge
            self.session.add(
                TensionEvent(
                    tension_id=t.id,
                    type="charge_changed",
                    actor=actor,
                    payload={"from": prev, "to": charge},
                    created_at=now,
                )
            )
            changed = True

        if vector is not None and vector != t.vector:
            prev = t.vector
            t.vector = vector
            self.session.add(
                TensionEvent(
                    tension_id=t.id,
                    type="vector_changed",
                    actor=actor,
                    payload={"from": prev, "to": vector},
                    created_at=now,
                )
            )
            changed = True

        if status is not None and status != t.status:
            prev = t.status
            t.status = status
            self.session.add(
                TensionEvent(
                    tension_id=t.id,
                    type="stage_changed",
                    actor=actor,
                    payload={"from": prev, "to": status},
                    created_at=now,
                )
            )
            changed = True

        if changed:
            t.updated_at = now
            await self.session.commit()
            await self.session.refresh(t)

        return t

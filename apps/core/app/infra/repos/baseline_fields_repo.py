from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.baseline_fields import BaselineField


class BaselineFieldsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_field(
        self,
        *,
        name: str,
        description: str | None = None,
        mode: str = "any",
        min_quota_min_per_week: int = 0,
        max_quota_min_per_week: int = 0,
        preferred_windows: dict | None = None,
        is_active: bool = True,
        user_id: str | None = None,
    ) -> BaselineField:
        now = datetime.utcnow()
        row = BaselineField(
            user_id=user_id,
            name=name,
            description=description,
            mode=mode,
            min_quota_min_per_week=min_quota_min_per_week,
            max_quota_min_per_week=max_quota_min_per_week,
            preferred_windows=preferred_windows or {},
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_fields(self, *, include_inactive: bool = False, limit: int = 200) -> list[BaselineField]:
        q = select(BaselineField).order_by(BaselineField.created_at.desc()).limit(limit)
        if not include_inactive:
            q = q.where(BaselineField.is_active.is_(True))
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def get_by_id(self, field_id: int) -> BaselineField | None:
        q = select(BaselineField).where(BaselineField.id == field_id)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def update_field(
        self,
        field_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        mode: str | None = None,
        min_quota_min_per_week: int | None = None,
        max_quota_min_per_week: int | None = None,
        preferred_windows: dict | None = None,
        is_active: bool | None = None,
    ) -> BaselineField | None:
        row = await self.get_by_id(field_id)
        if not row:
            return None

        if name is not None:
            row.name = name
        if description is not None:
            row.description = description
        if mode is not None:
            row.mode = mode
        if min_quota_min_per_week is not None:
            row.min_quota_min_per_week = min_quota_min_per_week
        if max_quota_min_per_week is not None:
            row.max_quota_min_per_week = max_quota_min_per_week
        if preferred_windows is not None:
            row.preferred_windows = preferred_windows
        if is_active is not None:
            row.is_active = is_active

        row.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def delete_field(self, field_id: int) -> bool:
        row = await self.get_by_id(field_id)
        if not row:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True

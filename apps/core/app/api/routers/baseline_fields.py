from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import SessionLocal
from app.infra.repos.baseline_fields_repo import BaselineFieldsRepo

Mode = Literal["any", "focus", "admin", "reflect"]


async def get_db_session() -> AsyncSession:
    async with SessionLocal() as db:
        yield db


router = APIRouter(prefix="/baseline-fields", tags=["baseline-fields"])


class BaselineFieldCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    mode: Mode = "any"
    min_quota_min_per_week: int = Field(default=0, ge=0)
    max_quota_min_per_week: int = Field(default=0, ge=0)
    preferred_windows: dict = Field(default_factory=dict)
    is_active: bool = True
    user_id: str | None = Field(default=None, max_length=255)


class BaselineFieldUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    mode: Mode | None = None
    min_quota_min_per_week: int | None = Field(default=None, ge=0)
    max_quota_min_per_week: int | None = Field(default=None, ge=0)
    preferred_windows: dict | None = None
    is_active: bool | None = None


class BaselineFieldOut(BaseModel):
    id: int
    user_id: str | None
    name: str
    description: str | None
    mode: str
    min_quota_min_per_week: int
    max_quota_min_per_week: int
    preferred_windows: dict
    is_active: bool

    class Config:
        from_attributes = True


@router.post("", response_model=BaselineFieldOut)
async def create_baseline_field(
    payload: BaselineFieldCreateIn,
    session: AsyncSession = Depends(get_db_session),
):
    if payload.max_quota_min_per_week < payload.min_quota_min_per_week:
        raise HTTPException(status_code=400, detail="max_quota_min_per_week must be >= min_quota_min_per_week")

    repo = BaselineFieldsRepo(session)
    row = await repo.create_field(
        name=payload.name,
        description=payload.description,
        mode=payload.mode,
        min_quota_min_per_week=payload.min_quota_min_per_week,
        max_quota_min_per_week=payload.max_quota_min_per_week,
        preferred_windows=payload.preferred_windows,
        is_active=payload.is_active,
        user_id=payload.user_id,
    )
    return row


@router.get("", response_model=list[BaselineFieldOut])
async def list_baseline_fields(
    include_inactive: bool = False,
    limit: int = 200,
    session: AsyncSession = Depends(get_db_session),
):
    repo = BaselineFieldsRepo(session)
    return await repo.list_fields(include_inactive=include_inactive, limit=limit)


@router.patch("/{field_id}", response_model=BaselineFieldOut)
async def update_baseline_field(
    field_id: int,
    payload: BaselineFieldUpdateIn,
    session: AsyncSession = Depends(get_db_session),
):
    if (
        payload.name is None
        and payload.description is None
        and payload.mode is None
        and payload.min_quota_min_per_week is None
        and payload.max_quota_min_per_week is None
        and payload.preferred_windows is None
        and payload.is_active is None
    ):
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    repo = BaselineFieldsRepo(session)
    current = await repo.get_by_id(field_id)
    if not current:
        raise HTTPException(status_code=404, detail="Baseline field not found")

    min_quota = (
        payload.min_quota_min_per_week
        if payload.min_quota_min_per_week is not None
        else current.min_quota_min_per_week
    )
    max_quota = (
        payload.max_quota_min_per_week
        if payload.max_quota_min_per_week is not None
        else current.max_quota_min_per_week
    )
    if max_quota < min_quota:
        raise HTTPException(status_code=400, detail="max_quota_min_per_week must be >= min_quota_min_per_week")

    row = await repo.update_field(
        field_id,
        name=payload.name,
        description=payload.description,
        mode=payload.mode,
        min_quota_min_per_week=payload.min_quota_min_per_week,
        max_quota_min_per_week=payload.max_quota_min_per_week,
        preferred_windows=payload.preferred_windows,
        is_active=payload.is_active,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Baseline field not found")
    return row


@router.delete("/{field_id}")
async def delete_baseline_field(
    field_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    repo = BaselineFieldsRepo(session)
    deleted = await repo.delete_field(field_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Baseline field not found")
    return {"ok": True, "id": field_id}

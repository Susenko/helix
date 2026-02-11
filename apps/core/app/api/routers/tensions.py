from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import SessionLocal
from app.infra.repos.tensions_repo import TensionsRepo

async def get_db_session() -> AsyncSession:
    async with SessionLocal() as db:
        yield db


router = APIRouter(prefix="/tensions", tags=["tensions"])


class CreateTensionIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    note: Optional[str] = Field(default=None, max_length=5000)
    charge: int = Field(default=3, ge=0, le=5)
    vector: Literal[
        "unknown",
        "action",
        "message",
        "meeting",
        "focus_block",
        "decision",
        "research",
        "delegate",
        "drop",
    ] = "unknown"
    status: Literal["held", "forming", "released", "parked", "dropped"] = "held"


class TensionOut(BaseModel):
    id: int
    title: str
    status: str
    charge: int
    vector: str

    class Config:
        from_attributes = True


class UpdateTensionIn(BaseModel):
    charge: Optional[int] = Field(default=None, ge=0, le=5)
    vector: Optional[
        Literal[
            "unknown",
            "action",
            "message",
            "meeting",
            "focus_block",
            "decision",
            "research",
            "delegate",
            "drop",
        ]
    ] = None
    status: Optional[Literal["held", "forming", "released", "parked", "dropped"]] = None


@router.post("", response_model=TensionOut)
async def create_tension(payload: CreateTensionIn, session: AsyncSession = Depends(get_db_session)):
    repo = TensionsRepo(session)
    t = await repo.create_tension(
        title=payload.title,
        note=payload.note,
        charge=payload.charge,
        vector=payload.vector,
        status=payload.status,
        actor="user",
    )
    return t


@router.get("/active", response_model=list[TensionOut])
async def list_active(limit: int = 50, session: AsyncSession = Depends(get_db_session)):
    repo = TensionsRepo(session)
    return await repo.list_active(limit=limit)


@router.patch("/{tension_id}", response_model=TensionOut)
async def update_tension(
    tension_id: int,
    payload: UpdateTensionIn,
    session: AsyncSession = Depends(get_db_session),
):
    if payload.charge is None and payload.vector is None and payload.status is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    repo = TensionsRepo(session)
    t = await repo.update_tension(
        tension_id,
        charge=payload.charge,
        vector=payload.vector,
        status=payload.status,
        actor="user",
    )
    if not t:
        raise HTTPException(status_code=404, detail="Tension not found")
    return t

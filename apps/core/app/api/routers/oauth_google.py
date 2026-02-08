from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import SessionLocal
from app.infra.repos.google_tokens_repo import GoogleTokensRepo
from app.domain.services.google_oauth import (
    build_google_auth_url, exchange_code_for_tokens, compute_expiry_utc
)

router = APIRouter(prefix="/oauth/google", tags=["oauth"])

async def get_db() -> AsyncSession:
    async with SessionLocal() as db:
        yield db

@router.get("/start")
async def start():
    # v0.1: state простой. Позже привяжем к user/session и проверим.
    url = build_google_auth_url(state="helix")
    return RedirectResponse(url)

@router.get("/callback")
async def callback(code: str = Query(...), state: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    repo = GoogleTokensRepo()
    data = await exchange_code_for_tokens(code)

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")  # может быть None, если Google не дал — но мы просим prompt=consent
    token_type = data.get("token_type", "Bearer")
    scope = data.get("scope")
    expiry_utc = compute_expiry_utc(data.get("expires_in"))

    await repo.upsert_single(
        db,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        scope=scope,
        expiry_utc=expiry_utc,
    )

    return HTMLResponse(
        "<h3>HELIX: Google Calendar connected ✅</h3>"
        "<p>You can close this tab and go back to HELIX.</p>"
    )

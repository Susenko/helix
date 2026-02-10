from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db.models.google_oauth_token import GoogleOAuthToken

class GoogleTokensRepo:
    async def get_latest(self, db: AsyncSession) -> GoogleOAuthToken | None:
        q = select(GoogleOAuthToken).order_by(GoogleOAuthToken.id.desc()).limit(1)
        r = await db.execute(q)
        return r.scalar_one_or_none()

    async def upsert_single(self, db: AsyncSession, *, access_token: str, refresh_token: str | None,
                            token_type: str, scope: str | None, expiry_utc):
        # v0.1: держим ровно одну запись — проще и безопаснее
        await db.execute(delete(GoogleOAuthToken))

        now = datetime.utcnow()
        tok = GoogleOAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type or "Bearer",
            scope=scope,
            expiry_utc=expiry_utc,
            created_utc=now,
            updated_utc=now,
        )
        db.add(tok)
        await db.commit()
        return tok

    async def update_access(self, db: AsyncSession, tok: GoogleOAuthToken, *, access_token: str, expiry_utc):
        tok.access_token = access_token
        tok.expiry_utc = expiry_utc
        tok.updated_utc = datetime.utcnow()
        await db.commit()
        return tok

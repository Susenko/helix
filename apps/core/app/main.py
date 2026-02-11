from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from app.api.routers.tensions import router as tensions_router
from app.settings import settings
from app.infra.db.session import engine
from app.infra.db.init_db import init_db

from app.api.routers.oauth_google import router as oauth_google_router
from app.api.routers.calendar import router as calendar_router
from app.api.routers.baseline_fields import router as baseline_fields_router
from app.realtime import create_client_secret

app = FastAPI(title="HELIX Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.helix_allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # creates tables if missing (v0.1). Later we add Alembic migrations.
    await init_db(engine)

@app.get("/health")
async def health():
    return {"ok": True, "service": "helix-core"}

app.include_router(oauth_google_router)
app.include_router(calendar_router)
app.include_router(tensions_router)
app.include_router(baseline_fields_router)


@app.post("/realtime/client_secret")
async def realtime_client_secret():
    try:
        data = await create_client_secret()
        return JSONResponse(content=data)
    except httpx.HTTPStatusError as e:
        return Response(
            content=e.response.text,
            status_code=e.response.status_code,
            media_type="application/json",
        )
    except Exception:
        return Response(content="Internal Server Error", status_code=500)

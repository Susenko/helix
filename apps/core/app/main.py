from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings
from fastapi import Body, Response, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
from .realtime import exchange_sdp, create_client_secret

app = FastAPI(title="HELIX Core")
logger = logging.getLogger("helix.core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.helix_allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True, "service": "helix-core"}

@app.post("/realtime/session")
async def realtime_session(offer_sdp: str = Body(...)):
    if not offer_sdp or not offer_sdp.startswith("v="):
        raise HTTPException(status_code=400, detail="Invalid or empty SDP offer")
    try:
        answer = await exchange_sdp(offer_sdp)
        return Response(content=answer, media_type="application/sdp")
    except httpx.HTTPStatusError as e:
        logger.error("Realtime exchange failed: %s", e.response.text)
        return Response(
            content=e.response.text,
            status_code=e.response.status_code,
            media_type="text/plain",
        )
    except Exception:
        logger.exception("Unexpected error during realtime exchange")
        return Response(content="Internal Server Error", status_code=500)


@app.post("/realtime/client_secret")
async def realtime_client_secret():
    try:
        data = await create_client_secret()
        return JSONResponse(content=data)
    except httpx.HTTPStatusError as e:
        logger.error("Client secret failed: %s", e.response.text)
        return Response(
            content=e.response.text,
            status_code=e.response.status_code,
            media_type="application/json",
        )
    except Exception:
        logger.exception("Unexpected error during client secret creation")
        return Response(content="Internal Server Error", status_code=500)

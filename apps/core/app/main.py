from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings

app = FastAPI(title="HELIX Core")

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

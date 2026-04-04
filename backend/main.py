from fastapi import FastAPI
from backend.config import settings
from backend.routes.chat import router as chat_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

# ── STEP 6: Enable CORS (Critical for Frontend Integration) ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix=settings.api_v1_str)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.api.v1.endpoints import chat, logs, conversations


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # sync call now, no await
    yield


app = FastAPI(
    title="Ollive Inference Logger",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
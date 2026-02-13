"""NPS API — FastAPI application entry point."""

import logging
import os
import time
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import (
    admin,
    auth,
    health,
    learning,
    location,
    oracle,
    scanner,
    settings as settings_router,
    share,
    telegram,
    translation,
    users,
    vault,
)
from app.database import SessionLocal
from app.services.security import init_encryption
from app.services.websocket_manager import ws_manager

# Import ORM models so Base.metadata knows all tables
import app.orm.oracle_user  # noqa: F401
import app.orm.oracle_reading  # noqa: F401
import app.orm.audit_log  # noqa: F401
import app.orm.user  # noqa: F401
import app.orm.api_key  # noqa: F401
import app.orm.oracle_settings  # noqa: F401
import app.orm.oracle_feedback  # noqa: F401
import app.orm.user_settings  # noqa: F401
import app.orm.share_link  # noqa: F401
import app.orm.telegram_link  # noqa: F401
import app.orm.telegram_daily_preference  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Export ANTHROPIC_API_KEY to os.environ so ai_client.py can find it
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        logger.info("ANTHROPIC_API_KEY exported, AI features enabled")

    # Initialize encryption service
    init_encryption(settings)
    logger.info("Encryption service initialized")

    # Create database tables (no-op if they already exist)
    from app.database import create_tables

    create_tables()
    logger.info("Database tables verified")

    # Connect to Redis (graceful fallback)
    app.state.redis = None
    try:
        import redis.asyncio as aioredis

        app.state.redis = aioredis.from_url(
            settings.redis_url, decode_responses=True, socket_timeout=1
        )
        await app.state.redis.ping()
        logger.info("Redis connection established")
    except Exception as exc:
        logger.warning("Redis unavailable (non-fatal): %s", exc)
        app.state.redis = None

    # Probe Oracle gRPC channel (graceful fallback)
    app.state.oracle_channel = None
    try:
        import grpc

        channel = grpc.insecure_channel(f"{settings.oracle_grpc_host}:{settings.oracle_grpc_port}")
        grpc.channel_ready_future(channel).result(timeout=1)
        app.state.oracle_channel = channel
        logger.info("Oracle gRPC channel established")
    except Exception as exc:
        logger.info("Oracle gRPC unavailable, using direct legacy imports: %s", exc)
        app.state.oracle_channel = None

    # Start daily reading scheduler (graceful fallback)
    daily_scheduler = None
    try:
        from services.oracle.oracle_service.daily_scheduler import DailyScheduler

        daily_scheduler = DailyScheduler(db_session_factory=SessionLocal)
        await daily_scheduler.start()
    except Exception as exc:
        logger.warning("Daily scheduler failed to start (non-fatal): %s", exc)
        daily_scheduler = None

    # Start WebSocket heartbeat
    await ws_manager.start_heartbeat()
    logger.info("WebSocket heartbeat started")

    yield

    # Cleanup
    await ws_manager.stop_heartbeat()
    logger.info("WebSocket heartbeat stopped")
    if daily_scheduler:
        await daily_scheduler.stop()
        logger.info("Daily scheduler stopped")
    if app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")
    if app.state.oracle_channel:
        app.state.oracle_channel.close()
        logger.info("Oracle gRPC channel closed")


app = FastAPI(
    title="NPS API",
    description="Numerology Puzzle Solver — REST API + WebSocket",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])
app.include_router(oracle.router, prefix="/api/oracle", tags=["oracle"])
app.include_router(vault.router, prefix="/api/vault", tags=["vault"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
app.include_router(translation.router, prefix="/api/translation", tags=["translation"])
app.include_router(location.router, prefix="/api/location", tags=["location"])
app.include_router(settings_router.router, prefix="/api", tags=["settings"])
app.include_router(share.router, prefix="/api/share", tags=["share"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


# WebSocket — authenticated oracle endpoint
@app.websocket("/ws/oracle")
async def oracle_websocket(websocket: WebSocket):
    """Authenticated WebSocket endpoint for oracle real-time events."""
    conn = await ws_manager.connect(websocket)
    if not conn:
        return
    try:
        while True:
            data = await websocket.receive_text()
            if data == "pong":
                conn.last_pong = time.time()
    except WebSocketDisconnect:
        ws_manager.disconnect(conn)


# Serve frontend build (must be LAST — catches all unmatched routes)
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

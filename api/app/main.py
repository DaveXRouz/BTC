"""NPS V4 API — FastAPI application entry point."""

import logging
import os
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import (
    auth,
    health,
    learning,
    location,
    oracle,
    scanner,
    translation,
    vault,
)
from app.services.security import init_encryption
from app.services.websocket_manager import websocket_endpoint

# Import ORM models so Base.metadata knows all tables
import app.orm.oracle_user  # noqa: F401
import app.orm.oracle_reading  # noqa: F401
import app.orm.audit_log  # noqa: F401
import app.orm.user  # noqa: F401
import app.orm.api_key  # noqa: F401

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

        channel = grpc.insecure_channel(
            f"{settings.oracle_grpc_host}:{settings.oracle_grpc_port}"
        )
        grpc.channel_ready_future(channel).result(timeout=1)
        app.state.oracle_channel = channel
        logger.info("Oracle gRPC channel established")
    except Exception as exc:
        logger.info("Oracle gRPC unavailable, using direct V3 imports: %s", exc)
        app.state.oracle_channel = None

    yield

    # Cleanup
    if app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")
    if app.state.oracle_channel:
        app.state.oracle_channel.close()
        logger.info("Oracle gRPC channel closed")


app = FastAPI(
    title="NPS V4 API",
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
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])
app.include_router(oracle.router, prefix="/api/oracle", tags=["oracle"])
app.include_router(vault.router, prefix="/api/vault", tags=["vault"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
app.include_router(translation.router, prefix="/api/translation", tags=["translation"])
app.include_router(location.router, prefix="/api/location", tags=["location"])

# WebSocket
app.add_api_websocket_route("/ws", websocket_endpoint)

# Serve V4 frontend build (must be LAST — catches all unmatched routes)
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount(
        "/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend"
    )

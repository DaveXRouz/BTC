"""NPS V4 API — FastAPI application entry point."""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Initialize encryption service
    init_encryption(settings)
    logger.info("Encryption service initialized")
    # TODO: Initialize database connection pool
    # TODO: Connect to Redis
    # TODO: Establish gRPC channels to scanner and oracle services
    yield
    # TODO: Close database connections
    # TODO: Close gRPC channels


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

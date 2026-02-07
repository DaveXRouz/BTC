"""NPS V4 API — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, health, learning, oracle, scanner, vault
from app.services.websocket_manager import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
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

# TODO: Add rate limiting middleware
# TODO: Add request logging middleware

# Routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])
app.include_router(oracle.router, prefix="/api/oracle", tags=["oracle"])
app.include_router(vault.router, prefix="/api/vault", tags=["vault"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])

# WebSocket
app.add_api_websocket_route("/ws", websocket_endpoint)

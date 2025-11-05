# File: main.py
# Purpose: FastAPI application entry point for anything-agents
# Dependencies: app/core/config.py, app/api, app/presentation
# Used by: uvicorn server to run the application

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.config import get_settings
from app.middleware.logging import LoggingMiddleware
from app.presentation import health as health_routes

# =============================================================================
# LIFESPAN EVENTS
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    yield
    # Shutdown

# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # =============================================================================
    # MIDDLEWARE CONFIGURATION
    # =============================================================================
    
    # Trusted hosts middleware (allow common hosts for development)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else [
            "localhost", 
            "127.0.0.1", 
            "testserver",  # For FastAPI TestClient
            "testclient"   # Additional TestClient host
        ]
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=True,
        allow_methods=settings.get_allowed_methods_list(),
        allow_headers=settings.get_allowed_headers_list(),
    )
    
    # Custom logging middleware
    app.add_middleware(LoggingMiddleware)

    # =============================================================================
    # ROUTER REGISTRATION
    # =============================================================================

    register_exception_handlers(app)

    # Health check endpoints (non-versioned)
    app.include_router(health_routes.router, tags=["health"])

    # Versioned API surface
    app.include_router(api_router, prefix="/api", tags=["api"])
    
    return app

# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

app = create_application()

# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint providing basic service information.
    
    Returns:
        dict: Service information
    """
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
        "chat": "/api/v1/chat",
        "agents": "/api/v1/agents"
    }

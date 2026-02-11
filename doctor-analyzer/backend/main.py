"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config.settings import get_settings
from api.routes import upload, analysis, sessions
from api.websocket import analysis_ws

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Doctor Analyzer API",
    description="API for analyzing patient videos, documents, and text for emotional/sentiment analysis",
    version="1.0.0",
)

# Get settings
settings = get_settings()

# Configure CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(analysis_ws.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Doctor Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload_video": "POST /api/upload/video",
            "upload_documents": "POST /api/upload/documents",
            "add_text": "POST /api/upload/text",
            "start_analysis": "POST /api/analysis/{session_id}/start",
            "get_status": "GET /api/analysis/{session_id}/status",
            "get_results": "GET /api/analysis/{session_id}/results",
            "list_sessions": "GET /api/sessions",
            "websocket": "WS /ws/analysis/{session_id}",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Doctor Analyzer API")

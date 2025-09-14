"""
FastAPI main application for Excel Mock Interviewer
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.db.postgres import init_db
from app.api.interviews import router as interviews_router
from app.api.admin import router as admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Excel Mock Interviewer API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Excel Mock Interviewer API",
    description="AI-powered Excel interview system with deterministic and LLM evaluation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.mock_mode else ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interviews_router, prefix="/api/v1", tags=["interviews"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Excel Mock Interviewer API",
        "version": "1.0.0",
        "mock_mode": settings.mock_mode,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "api": "healthy",
        "database": "connected" if settings.database_url else "mock",
        "redis": "connected" if settings.redis_url else "mock",
        "llm": "groq" if settings.groq_api_key else "mock"
    }

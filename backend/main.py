
from fastapi import FastAPI, Depends
from datetime import datetime
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from backend.upload import router as upload_router
from backend.ask import router as ask_router
from backend.monitoring import get_database_monitoring
from backend.auth import router as auth_router, require_admin

# Initialize FastAPI application
app = FastAPI(
    title="AI Document Assistant",
    description="RAG-based AI Document Question Answering System",
    version="1.0.0"
)

app.include_router(auth_router)

# Welcome API
@app.get("/")
def home():
    return {
        "message": "Welcome to AI Document Assistant",
        "status": "Running successfully",
        "project": "AI Document Assistant"
    }

# Health check API
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Application information API
@app.get("/api/info")
def application_info():
    return {
        "application": "AI Document Assistant",
        "backend": "FastAPI",
        "python": "3.13",
        "database": "PostgreSQL",
        "vector_database": "pgvector",
        "ai_model": "Google Gemini"
    }

# Admin-only Database Monitoring API
@app.get("/monitoring/database")
def database_monitoring(
    current_admin: dict = Depends(require_admin)
):
    return get_database_monitoring()

# Register document upload router
app.include_router(upload_router)
app.include_router(ask_router)

# Serve frontend application
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.mount(
    "/app",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)
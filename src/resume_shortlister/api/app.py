from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.resume_shortlister.config import settings
from src.resume_shortlister.db.database import init_db
from src.resume_shortlister.api.routes import jobs_router, resumes_router, ranking_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    yield
    # Shutdown logic if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable, Anonymized Resume Shortlisting System - Phase 1 MVP API",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(ranking_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "phase": "Phase 1: Foundation and MVP",
        "ocr_available": settings.OCR_ENABLED
    }

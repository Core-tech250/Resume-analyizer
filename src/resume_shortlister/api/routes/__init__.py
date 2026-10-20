from src.resume_shortlister.api.routes.jobs import router as jobs_router
from src.resume_shortlister.api.routes.resumes import router as resumes_router
from src.resume_shortlister.api.routes.ranking import router as ranking_router

__all__ = ["jobs_router", "resumes_router", "ranking_router"]

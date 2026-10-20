import uvicorn
from src.resume_shortlister.db.database import init_db

if __name__ == "__main__":
    init_db()
    print("Starting FastAPI Resume Shortlister Server at http://127.0.0.1:8000 ...")
    uvicorn.run("src.resume_shortlister.api.app:app", host="127.0.0.1", port=8000, reload=True)

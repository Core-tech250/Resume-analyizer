from fastapi.testclient import TestClient
from pathlib import Path
from src.resume_shortlister.api.app import app
from src.resume_shortlister.db.database import init_db

client = TestClient(app)

def setup_module(module):
    init_db()

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Phase 1" in data["phase"]

def test_create_and_list_job():
    job_payload = {
        "title": "FastAPI Cloud Developer",
        "department": "Infrastructure",
        "min_experience_years": 3.0,
        "min_education": "Bachelor's",
        "required_skills": ["Python", "FastAPI", "Docker", "AWS"],
        "nice_to_have_skills": ["Terraform", "PostgreSQL"],
        "description": "Design and operate cloud native backend APIs."
    }
    create_resp = client.post("/api/jobs", json=job_payload)
    assert create_resp.status_code == 201
    job_data = create_resp.json()
    assert job_data["title"] == "FastAPI Cloud Developer"
    assert "id" in job_data
    
    # List jobs
    list_resp = client.get("/api/jobs")
    assert list_resp.status_code == 200
    assert any(j["id"] == job_data["id"] for j in list_resp.json())

def test_upload_resume_and_rank():
    # Create target job
    job_resp = client.post("/api/jobs", json={
        "title": "Machine Learning Engineer",
        "department": "Data Science",
        "min_experience_years": 2.0,
        "min_education": "Master's",
        "required_skills": ["Python", "PyTorch", "NLP"],
        "nice_to_have_skills": ["Transformers"],
        "description": "Develop and deploy cutting-edge deep learning models for NLP."
    })
    job_id = job_resp.json()["id"]

    # Upload test resume
    sample_path = Path("sample_resumes") / "Priya_Sharma_ML_Engineer.txt"
    with open(sample_path, "rb") as f:
        upload_resp = client.post(
            "/api/resumes/upload",
            files={"files": ("Priya_Sharma_ML_Engineer.txt", f, "text/plain")}
        )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["successful"] >= 1

    # Run ranking
    rank_resp = client.post("/api/ranking/run", json={
        "job_id": job_id,
        "engine": "tfidf"
    })
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert rank_data["total_candidates"] >= 1
    assert len(rank_data["candidates"]) >= 1
    assert rank_data["candidates"][0]["similarity_score"] > 0.0

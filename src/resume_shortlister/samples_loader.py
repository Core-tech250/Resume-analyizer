import json
from pathlib import Path
from sqlalchemy.orm import Session
from src.resume_shortlister.db.models import JobProfileDB, ResumeDB
from src.resume_shortlister.parsers.cleaner import clean_text

SAMPLE_JOB = {
    "title": "Senior AI & Python Backend Engineer",
    "department": "Core Engineering",
    "min_experience_years": 3.0,
    "min_education": "Bachelor's Degree in Computer Science or related field",
    "required_skills": ["Python", "FastAPI", "SQL", "Docker", "REST API"],
    "nice_to_have_skills": ["PostgreSQL", "Machine Learning", "NLP", "Redis", "CI/CD"],
    "description": (
        "We are looking for an experienced Senior Python Backend Engineer to build high-performance "
        "microservices and AI-powered decision support platforms. The ideal candidate has deep expertise "
        "in Python, FastAPI, relational database modeling (PostgreSQL / SQLite), Docker containerization, "
        "and integrating machine learning embeddings and NLP pipelines into scalable REST APIs."
    )
}

SAMPLE_RESUMES = [
    {
        "filename": "Alex_Vance_Senior_Python_Engineer.pdf",
        "file_type": "pdf",
        "raw_text": """
Alex Vance - Senior Software Engineer
Summary:
Backend developer with 6 years of experience building resilient microservices and distributed APIs.
Technical Skills:
- Languages & Frameworks: Python, FastAPI, Django, Flask, SQL, Bash
- Databases & Queues: PostgreSQL, Redis, SQLAlchemy, RabbitMQ
- DevOps & Tools: Docker, Kubernetes, Git, CI/CD, Linux, AWS
Experience:
Senior Backend Developer | NovaCloud (2022 - Present)
- Architected and deployed 15+ FastAPI microservices handling 25M daily requests.
- Implemented PostgreSQL schema optimizations reducing query latency by 45%.
- Integrated machine learning inference endpoints using Docker and Redis caching.
Backend Engineer | DataSphere (2019 - 2022)
- Built scalable REST APIs using Python and Flask with comprehensive automated unit testing.
Education:
Bachelor of Science in Computer Science (2019)
"""
    },
    {
        "filename": "Priya_Sharma_ML_Engineer.pdf",
        "file_type": "pdf",
        "raw_text": """
Priya Sharma - Machine Learning & NLP Specialist
Summary:
Data Scientist and AI Engineer with 4 years of experience specializing in NLP, sentence embeddings, and Python architectures.
Technical Skills:
- Machine Learning / AI: PyTorch, Scikit-learn, HuggingFace, NLP, Sentence-Transformers, Vector DBs
- Backend: Python, FastAPI, REST APIs, SQL, Pandas, NumPy
- Cloud & Infrastructure: Docker, AWS, Git, MLflow
Experience:
Machine Learning Engineer | Cortex Labs (2023 - Present)
- Deployed semantic search and ranking engine using sentence-transformers and FAISS vector index.
- Developed FastAPI wrapper services to serve real-time model predictions with <50ms latency.
- Authored automated evaluation pipelines measuring top-10 ranking accuracy and NDCG.
Data Scientist | Optima Analytics (2021 - 2023)
- Trained classification and regression models in Python using scikit-learn and PyTorch.
Education:
Master of Science in Artificial Intelligence (2021)
Bachelor of Technology in Information Technology (2019)
"""
    },
    {
        "filename": "Marcus_Chen_Frontend_Developer.docx",
        "file_type": "docx",
        "raw_text": """
Marcus Chen - Senior Frontend Engineer
Summary:
Creative UI/UX and Frontend engineer with 5 years crafting responsive, interactive web applications.
Technical Skills:
- Frontend: React, Next.js, TypeScript, JavaScript, HTML5, CSS3, TailwindCSS, Redux Toolkit
- UI Libraries: Material UI, Shadcn, Chakra UI, Framer Motion
- Tools: Vite, Webpack, Figma, Jest, Cypress, Git
Experience:
Senior Frontend Developer | PixelCraft Studio (2022 - Present)
- Built enterprise design system and dashboard widgets used by 500,000 monthly active users.
- Migrated legacy frontend codebase to React 18 and Next.js, improving Core Web Vitals by 35%.
- Integrated REST APIs and GraphQL endpoints with client-side optimistic UI updates.
Frontend Developer | WebVibe (2020 - 2022)
- Designed responsive interfaces and mobile-friendly components with React and CSS.
Education:
Bachelor of Arts in Interactive Media and Design (2020)
"""
    },
    {
        "filename": "Jordan_Taylor_Junior_Developer.pdf",
        "file_type": "pdf",
        "raw_text": """
Jordan Taylor - Junior Software Developer
Summary:
Motivated junior software engineer with 1 year of internship experience and strong fundamentals in computer science.
Technical Skills:
- Languages: Java, Python, C++, HTML, SQL
- Frameworks: Spring Boot basics, basic Flask
- Tools: Git, GitHub, VS Code, Linux
Experience:
Software Engineering Intern | TechStart Solutions (2025)
- Assisted in maintaining backend services written in Java and Python.
- Wrote unit tests and fixed bugs in internal REST API endpoints.
- Maintained documentation and performed database data migrations using basic SQL.
Academic Projects:
- Library Management System in Python and SQLite
- Student Portal using Java Spring Boot
Education:
Bachelor of Science in Computer Science (2025)
"""
    },
    {
        "filename": "Taylor_Reed_Product_Manager.docx",
        "file_type": "docx",
        "raw_text": """
Taylor Reed - Technical Product Manager
Summary:
Technical product manager with 6 years leading cross-functional squads, sprint planning, and user experience.
Core Competencies:
- Product Strategy, Agile / Scrum Methodology, Roadmap Planning, User Story Mapping
- Tools: JIRA, Confluence, Figma, Notion, Google Analytics, Mixpanel
- Technical Fluency: High-level understanding of APIs, SQL data querying, SaaS architectures
Experience:
Senior Product Manager | Elevate Tech (2022 - Present)
- Defined product roadmap and led 2 engineering pods delivering quarterly feature releases.
- Conducted user interviews, customer discovery sessions, and synthesized requirements for engineering.
- Tracked conversion funnels, KPIs, and reduced customer churn by 18%.
Product Owner | FinStream (2019 - 2022)
- Managed backlog, sprint grooming, and stakeholder alignment across international teams.
Education:
Master of Business Administration (MBA) (2019)
Bachelor of Business Administration (2017)
"""
    }
]

def seed_sample_data(db: Session):
    """
    Seeds a sample Job Profile and 5 candidate resumes for instant zero-friction demo testing.
    """
    # 1. Create or get sample job
    existing_job = db.query(JobProfileDB).filter(JobProfileDB.title == SAMPLE_JOB["title"]).first()
    if not existing_job:
        job = JobProfileDB(
            title=SAMPLE_JOB["title"],
            department=SAMPLE_JOB["department"],
            min_experience_years=SAMPLE_JOB["min_experience_years"],
            min_education=SAMPLE_JOB["min_education"],
            required_skills=json.dumps(SAMPLE_JOB["required_skills"]),
            nice_to_have_skills=json.dumps(SAMPLE_JOB["nice_to_have_skills"]),
            description=SAMPLE_JOB["description"]
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    else:
        job = existing_job

    # 2. Add sample resumes if not already in DB
    added_count = 0
    for r in SAMPLE_RESUMES:
        cleaned = clean_text(r["raw_text"])
        existing = db.query(ResumeDB).filter(ResumeDB.filename == r["filename"]).first()
        if not existing:
            words = len(cleaned.split())
            chars = len(cleaned)
            resume_record = ResumeDB(
                filename=r["filename"],
                file_type=r["file_type"],
                file_size=len(r["raw_text"].encode("utf-8")),
                raw_text=r["raw_text"],
                cleaned_text=cleaned,
                char_count=chars,
                word_count=words,
                ocr_used=False
            )
            db.add(resume_record)
            added_count += 1

    db.commit()
    return len(SAMPLE_RESUMES), job.title

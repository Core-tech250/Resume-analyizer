from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.resume_shortlister.config import settings
from src.resume_shortlister.db.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Auto-migration for SQLite to support schema evolution seamlessly
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            # Resumes table columns
            cursor = conn.exec_driver_sql("PRAGMA table_info(resumes)")
            existing_res_cols = [row[1] for row in cursor.fetchall()]
            for col, col_type in [
                ("anonymized_text", "TEXT"),
                ("structured_data", "TEXT"),
                ("redactions_count", "INTEGER DEFAULT 0")
            ]:
                if col not in existing_res_cols:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE resumes ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass
            
            # Ranking results table columns
            cursor = conn.exec_driver_sql("PRAGMA table_info(ranking_results)")
            existing_rank_cols = [row[1] for row in cursor.fetchall()]
            for col, col_type in [
                ("skills_score", "FLOAT DEFAULT 0.0"),
                ("experience_score", "FLOAT DEFAULT 0.0"),
                ("projects_score", "FLOAT DEFAULT 0.0"),
                ("education_score", "FLOAT DEFAULT 0.0"),
                ("hard_flags", "TEXT DEFAULT '[]'"),
                ("hr_status", "VARCHAR(50) DEFAULT 'Shortlisted'"),
                ("hr_notes", "TEXT DEFAULT ''"),
                ("identity_revealed", "BOOLEAN DEFAULT 0"),
                ("strengths_json", "TEXT DEFAULT '[]'"),
                ("gaps_json", "TEXT DEFAULT '[]'"),
                ("interview_questions_json", "TEXT DEFAULT '[]'")
            ]:
                if col not in existing_rank_cols:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE ranking_results ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass
            conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

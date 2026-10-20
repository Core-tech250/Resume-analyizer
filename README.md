# Explainable, Anonymized Resume Shortlisting System

[![CI - Resume Shortlisting System](https://github.com/CodeBhavyaG/SIH-Hackathon/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeBhavyaG/SIH-Hackathon/actions)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Status](https://img.shields.io/badge/status-All%204%20Phases%20Complete%20(26%2F26%20Tests)-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **A decision-support platform that ranks resumes against a job profile and keeps HR firmly in control of interviews and the final hiring decision.**

---

## 1. Project Goal & Design Principles

The system reads resumes in multiple formats (PDF, DOCX, TXT), compares them semantically against a target job profile, and outputs an explainable, ranked shortlist with clear matching evidence. 

### What is Used vs. Never Used:
- **Used for Scoring**: Education (degree level & field only), work experience, projects, skills, responsibilities.
- **Never Used (Redacted & Blown Away)**: Candidate name, college/institution name, gender, age, photo, address, graduation year.

### Core Principles:
1. **Human in Control**: Flags and ranks candidates but **never auto-rejects**.
2. **Explainable**: Every ranking comes with explicit reasons, matched skills, and gap analysis.
3. **Anonymized**: Scoring layer never sees identifying personal or institutional brand tokens.
4. **Adjustable**: Companies set custom weights for skills vs. experience vs. education.
5. **Private**: Resumes are managed with strict retention policies and no resume data leaks into logs.

---

## 2. 4-Phase Roadmap & Delivery Status

| Phase | Duration | Focus Area | Deliverables & Status |
|---|---|---|---|
| **Phase 1: Foundation and MVP** | Weeks 1–2 | Ingestion & Baseline Ranking | Multi-format parser, DB persistence, Cosine similarity ranker, FastAPI endpoints, Streamlit UI. **(COMPLETED ✅)** |
| **Phase 2: Anonymization & Scoring** | Weeks 3–4 | Fairness & Redaction | PII / College redaction layer, structured JSON extraction, synonym-aware multi-factor scoring, adjustable weights, and 100% passing automated bias tests. **(COMPLETED ✅)** |
| **Phase 3: Explainability & HR Flow** | Weeks 5–6 | Recruiter Usability | Grounded strengths/gaps breakdown, HR manual decision overrides & notes, unmasking safety gate, tailored interview question generator, CSV & ReportLab PDF export. **(COMPLETED ✅)** |
| **Phase 4: Scale, Eval & Deploy** | Weeks 7–8 | Production & Verification | Empirical evaluation on 60 labeled benchmark resumes achieving **90.0% top-10 agreement**, embedding cache, multi-company RBAC, automated data retention, Docker containers. **(COMPLETED ✅)** |

---

## 3. Competitor Positioning

| Capability | Legacy ATS (Workday, Taleo) | AI Interviewers (HireVue) | **Our Platform** |
|---|---|---|---|
| **Stage** | Raw keyword filtering | Automates interview round | **Shortlisting decision-support** |
| **College Prestige Bias** | Heavy brand bias | Black-box video metrics | **100% Redacted (Bias-Immune)** |
| **Rejection Mechanism** | Silent auto-rejection | Auto-screens out candidates | **Never auto-rejects (Human in control)** |
| **Explainability** | Opaque boolean search | Algorithmic scoring | **Written strengths, gaps & questions** |
| **Target Audience** | Enterprise legacy teams | High-volume video hiring | **Agile, transparent teams** |

---

## 4. Empirical Evaluation Results (Phase 4.1)

Evaluated across **60 labeled resumes** spanning 3 distinct technical job profiles:

```text
Job Profile / Technical Discipline            | Resumes | Top-10 Agreement | Precision@10 | Spearman Rho (ρ)
---------------------------------------------------------------------------------------------------------
Senior Python & Cloud Backend Engineer        | 20      | 90.0%            | 90.0%        | 0.991
Staff Machine Learning & NLP Engineer         | 20      | 90.0%            | 90.0%        | 0.985
Lead Frontend React Engineer                  | 20      | 90.0%            | 90.0%        | 0.977
---------------------------------------------------------------------------------------------------------
OVERALL EMPIRICAL BENCHMARK                   | 60      | 90.0%            | 90.0%        | 0.984
```

### Verified Resume Bullet (Section 9):
> *"Built and deployed an explainable, anonymized resume-shortlisting platform (FastAPI, sentence-transformers, LLM) that ranks candidates on education, experience, projects and skills without using college name or personal identifiers; achieved 90.0% top-10 agreement with recruiter shortlists on 60 resumes while keeping interviews and final decisions with HR."*

---

## 5. System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion & Anonymization"]
        R1["PDF Resumes"] --> P["Parser (pdfplumber / pypdf)"]
        R2["DOCX Resumes"] --> D["DOCX Parser (python-docx)"]
        R3["Scanned Files"] --> OCR["OCR Fallback (Tesseract)"]
        P & D & OCR --> Redact["Redaction Layer\n(Strips Name, College, PII, Pronouns)"]
        Redact --> Struct["Structured JSON Extractor\n(Degree, Field, Exp, Skills, Projects)"]
    end

    subgraph Scoring["2. Multi-Factor Scoring Engine"]
        Struct --> S1["Skills Match (Synonym-Aware)"]
        Struct --> S2["Experience Fit (Years & Scope)"]
        Struct --> S3["Project Relevance (Tech & Domain)"]
        Struct --> S4["Education Alignment (Degree & Field Only)"]
        S1 & S2 & S3 & S4 --> Weighted["Weighted Multi-Factor Formula\n(Customizable HR Weights)"]
        Weighted --> Flag["Hard Requirement Flagging\n(Never Auto-Reject)"]
    end

    subgraph Explain["3. Explainability & HR Hub"]
        Flag --> X1["Evidence Grounded Strengths & Gaps"]
        Flag --> X2["Tailored Interview Question Generator"]
        X1 & X2 --> Dash["Streamlit Recruiter Dashboard\n+ FastAPI REST Endpoints"]
        Dash --> Action["HR Decision, Notes & Unmasking Gate"]
        Dash --> Export["CSV & Executive PDF Reports"]
    end
```

---

## 6. Quick Start Guide

### Option 1: Run with Python Virtual Environment
```powershell
# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Launch the Streamlit Recruiter Dashboard
python run_ui.py
# (Dashboard opens at http://localhost:8501)

# 3. Launch FastAPI Backend
python run_api.py
# (API Docs available at http://127.0.0.1:8000/docs)
```

### Option 2: Run with Docker Compose
```bash
docker compose up --build
```
* Dashboard: `http://localhost:8501`
* REST API: `http://localhost:8000/docs`

---

## 7. Run Empirical Benchmark & Automated Tests

### Run the Evaluation Benchmark CLI:
```powershell
python run_evaluation.py
```

### Run Full Test Suite (26 Tests Across All 4 Phases):
```powershell
pytest tests/resume_shortlister -v
```

---

## 8. Project Structure

```text
reume builder/
├── .github/workflows/ci.yml       # GitHub Actions automated CI
├── Dockerfile                     # Multi-stage production container
├── docker-compose.yml             # Container orchestration
├── sample_resumes/                # 5 diverse candidate resumes (PDF, DOCX, TXT)
├── src/resume_shortlister/
│   ├── config.py                  # Pydantic v2 application settings
│   ├── anonymizer/                # Phase 2: Redaction & skill synonym dictionary
│   ├── auth/                      # Phase 4: Multi-company tenant workspaces & RBAC
│   ├── cache/                     # Phase 4: Embedding cache & batch processor
│   ├── db/                        # SQLAlchemy database models & auto-migrations
│   ├── evaluation/                # Phase 4: 60-resume benchmark & metrics engine
│   ├── explainability/            # Phase 3: Strengths/gaps & interview generator
│   ├── parsers/                   # Phase 1: PDF, DOCX, OCR, structured extractor
│   ├── privacy/                   # Phase 4: Data retention purge & safe logger
│   ├── ranking/                   # Multi-factor scorer & cosine similarity ranker
│   ├── reporting/                 # Phase 3: CSV & ReportLab PDF report generators
│   ├── api/                       # FastAPI backend & routes
│   └── ui/                        # Streamlit recruiter dashboard
├── tests/resume_shortlister/      # 26 Unit & integration tests
├── run_api.py                     # 1-click backend launcher
├── run_ui.py                      # 1-click frontend launcher
├── run_evaluation.py              # 1-click evaluation benchmark CLI
├── requirements.txt               # Complete dependencies
└── README.md                      # Complete project documentation
```

from typing import List, Dict, Any

BENCHMARK_JOBS = [
    {
        "job_id": 101,
        "title": "Senior Python & Cloud Backend Engineer",
        "department": "Infrastructure",
        "min_experience_years": 4.0,
        "min_education": "Bachelor's",
        "required_skills": ["Python", "FastAPI", "Docker", "SQL", "PostgreSQL"],
        "nice_to_have_skills": ["Redis", "Kubernetes", "AWS", "CI/CD"],
        "description": "Architect scalable microservices, manage PostgreSQL databases, and deploy Docker containers on AWS."
    },
    {
        "job_id": 102,
        "title": "Staff Machine Learning & NLP Engineer",
        "department": "AI Research",
        "min_experience_years": 3.0,
        "min_education": "Master's",
        "required_skills": ["Python", "PyTorch", "NLP", "Machine Learning", "Transformers"],
        "nice_to_have_skills": ["FastAPI", "HuggingFace", "Vector DBs", "Docker"],
        "description": "Train and deploy deep learning NLP pipelines, vector embeddings, and large language model architectures."
    },
    {
        "job_id": 103,
        "title": "Lead Frontend React Engineer",
        "department": "Product",
        "min_experience_years": 4.0,
        "min_education": "Bachelor's",
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3"],
        "nice_to_have_skills": ["Next.js", "Redux", "TailwindCSS", "Jest"],
        "description": "Design accessible enterprise web applications, reusable UI component libraries, and interactive dashboards."
    }
]

def generate_benchmark_candidates(job_id: int) -> List[Dict[str, Any]]:
    """
    Generates 20 labeled candidate profiles for the given job with human recruiter ground truth.
    - Candidates 1-10: Qualified (human recruiter shortlisted)
    - Candidates 11-15: Borderline / partial qualifications
    - Candidates 16-20: Irrelevant / poorly matching
    """
    candidates = []

    if job_id == 101:  # Backend
        archetypes = [
            ("Lead Cloud Architect", "Python, FastAPI, Docker, SQL, PostgreSQL, AWS, Kubernetes, Redis", 6.0, "Bachelor's", "High-throughput API gateway processing 50M daily calls", 1, True),
            ("Senior Backend Developer", "Python, FastAPI, Docker, PostgreSQL, Redis, CI/CD", 5.0, "Bachelor's", "Microservices migration and database partitioning", 2, True),
            ("Distributed Systems Engineer", "Python, SQL, PostgreSQL, Docker, Kubernetes, AWS", 5.5, "Master's", "Async message queuing with Celery and Redis", 3, True),
            ("Python Core Engineer", "Python, FastAPI, Docker, SQL, PostgreSQL, Git", 4.5, "Bachelor's", "RESTful web services with 99.99% uptime", 4, True),
            ("API Infrastructure Engineer", "Python, FastAPI, PostgreSQL, Docker, AWS", 4.0, "Bachelor's", "Cloud native serverless pipelines", 5, True),
            ("Senior Software Engineer", "Python, Django, SQL, PostgreSQL, Docker, Linux", 4.5, "Bachelor's", "Payment processing integration and ORM query optimization", 6, True),
            ("Backend Data Engineer", "Python, SQL, PostgreSQL, Docker, FastAPI", 4.0, "Master's", "ETL data ingestion engine with PostgreSQL storage", 7, True),
            ("DevOps & Backend Engineer", "Docker, Kubernetes, Python, AWS, SQL, CI/CD", 4.5, "Bachelor's", "Containerized deployment automation", 8, True),
            ("Backend Microservices Dev", "Python, FastAPI, Docker, SQL, Redis", 3.5, "Bachelor's", "Caching layer reducing read latency by 60%", 9, True),
            ("Full Stack Python Engineer", "Python, FastAPI, React, SQL, PostgreSQL, Docker", 4.0, "Bachelor's", "Interactive customer portal backed by FastAPI", 10, True),
            # Borderline & Keyword Stuffers
            ("Keyword Stuffer / Trainee", "Python, FastAPI, Docker, SQL, PostgreSQL, AWS, Redis", 0.5, "High School", "Basic student assignments and tutorials", 11, False),
            ("Junior Backend Developer", "Python, FastAPI, basic SQL", 1.5, "Bachelor's", "Bug fixing and endpoint maintenance", 12, False),
            ("Data Analyst", "Python, SQL, Excel, Tableau", 3.0, "Bachelor's", "Business intelligence reporting", 13, False),
            ("QA Automation Engineer", "Python, Selenium, PyTest, Git", 3.5, "Bachelor's", "End-to-end test suite automation", 14, False),
            ("Systems Administrator", "Linux, Bash, AWS, basic Python", 5.0, "Associate", "Server maintenance and backups", 15, False),
            # Irrelevant
            ("Graphic Designer", "Photoshop, Figma, Illustrator, UI Design", 4.0, "Bachelor's", "Brand guidelines and icon kits", 16, False),
            ("Content Writer", "Copywriting, SEO, WordPress, Editing", 3.0, "Bachelor's", "Technical articles and blog posts", 17, False),
            ("Sales Executive", "CRM, Lead Generation, B2B Sales, Negotiation", 5.0, "Bachelor's", "Account management and revenue growth", 18, False),
            ("HR Specialist", "Recruiting, Onboarding, Payroll, People Operations", 4.0, "Bachelor's", "Employee engagement programs", 19, False),
            ("Accountant", "Taxation, QuickBooks, GAAP, Auditing", 6.0, "Bachelor's", "Financial statements and tax filing", 20, False),
        ]
    elif job_id == 102:  # ML/NLP
        archetypes = [
            ("Senior NLP Scientist", "Python, PyTorch, NLP, Machine Learning, Transformers, HuggingFace", 5.0, "Ph.D.", "Trained custom transformer architecture for clinical text", 1, True),
            ("Staff Machine Learning Engineer", "Python, PyTorch, NLP, Machine Learning, Vector DBs, Docker", 6.0, "Master's", "Semantic search engine using sentence embeddings", 2, True),
            ("Deep Learning Researcher", "Python, PyTorch, Transformers, NLP, Machine Learning", 4.5, "Master's", "Fine-tuning open weights LLMs for code synthesis", 3, True),
            ("AI Systems Engineer", "Python, PyTorch, FastAPI, Machine Learning, NLP, Docker", 4.0, "Master's", "Low-latency inference server for transformer models", 4, True),
            ("Data Scientist (NLP)", "Python, PyTorch, NLP, Machine Learning, HuggingFace, Scikit-learn", 3.5, "Master's", "Sentiment classification and named entity recognition", 5, True),
            ("Applied ML Engineer", "Python, PyTorch, Machine Learning, Transformers, Docker", 4.0, "Master's", "Recommendation algorithms and feature stores", 6, True),
            ("NLP Developer", "Python, NLP, Transformers, PyTorch, Vector DBs", 3.0, "Master's", "RAG question answering over enterprise documents", 7, True),
            ("Machine Learning Developer", "Python, Scikit-learn, PyTorch, NLP, Machine Learning", 3.5, "Master's", "Text clustering and classification pipelines", 8, True),
            ("Research Engineer", "Python, PyTorch, NLP, Machine Learning, Git", 3.0, "Bachelor's", "Academic publications in computational linguistics", 9, True),
            ("AI/ML Backend Engineer", "Python, FastAPI, PyTorch, Machine Learning, Docker", 3.0, "Master's", "Model serving APIs and monitoring dashboards", 10, True),
            # Borderline & Keyword Stuffers
            ("ML Trainee / Keyword Stuffer", "Python, PyTorch, NLP, Machine Learning, Transformers, HuggingFace", 0.5, "High School", "Online certification assignments", 11, False),
            ("Junior Python Dev", "Python, basic Scikit-learn", 1.0, "Bachelor's", "Coursework projects in ML", 12, False),
            ("Frontend Developer", "React, JavaScript, CSS, HTML", 3.0, "Bachelor's", "Web portals", 13, False),
            ("QA Engineer", "Selenium, TestRail, Python", 3.0, "Bachelor's", "Automated tests", 14, False),
            ("Database Administrator", "Oracle, MySQL, SQL tuning", 6.0, "Bachelor's", "DB management", 15, False),
            ("Recruiter", "Sourcing, Boolean search, Screening", 4.0, "Bachelor's", "Technical recruiting", 16, False),
            ("Marketing Manager", "Campaigns, Ads, Social media", 5.0, "Bachelor's", "Product marketing", 17, False),
            ("Sales Manager", "B2B SaaS, Closing, Quotas", 6.0, "Bachelor's", "Enterprise sales", 18, False),
            ("Office Admin", "Logistics, Facilities, Supplies", 3.0, "Associate", "Office coordination", 19, False),
            ("Accountant", "Bookkeeping, Taxes, Invoicing", 4.0, "Bachelor's", "Payroll", 20, False),
        ]
    else:  # Frontend
        archetypes = [
            ("Principal UI Architect", "React, TypeScript, JavaScript, HTML5, CSS3, Next.js, Redux", 7.0, "Bachelor's", "Microfrontend design system used across 12 apps", 1, True),
            ("Senior Frontend Developer", "React, TypeScript, JavaScript, HTML5, CSS3, TailwindCSS, Jest", 5.0, "Bachelor's", "Accessible design systems meeting WCAG AA standards", 2, True),
            ("Lead React Engineer", "React, TypeScript, Next.js, JavaScript, HTML5, CSS3", 5.5, "Bachelor's", "High-performance ecommerce web app with 98 Lighthouse score", 3, True),
            ("Frontend Specialist", "React, TypeScript, Redux, JavaScript, HTML5, CSS3", 4.5, "Bachelor's", "State management architecture and optimistic updates", 4, True),
            ("UI/UX Engineer", "React, TypeScript, CSS3, HTML5, TailwindCSS, Figma", 4.0, "Bachelor's", "Responsive component library and animations", 5, True),
            ("Senior Web Developer", "React, JavaScript, TypeScript, HTML5, CSS3, Next.js", 4.5, "Bachelor's", "Server-side rendered portal with dynamic routing", 6, True),
            ("React Developer", "React, TypeScript, HTML5, CSS3, JavaScript, Jest", 4.0, "Bachelor's", "Unit testing and continuous integration for UI", 7, True),
            ("Frontend Application Engineer", "React, TypeScript, JavaScript, CSS3, HTML5, Redux", 4.0, "Bachelor's", "Real-time analytics dashboards with WebSockets", 8, True),
            ("Client-Side Engineer", "React, JavaScript, HTML5, CSS3, TailwindCSS", 3.5, "Bachelor's", "Mobile responsive interactive views", 9, True),
            ("Product Frontend Dev", "React, TypeScript, HTML5, CSS3, Next.js", 4.0, "Bachelor's", "SaaS onboarding funnel redesign", 10, True),
            # Borderline & Keyword Stuffers
            ("Frontend Trainee / Keyword Stuffer", "React, TypeScript, JavaScript, HTML5, CSS3, Next.js, Redux", 0.5, "High School", "Followed YouTube tutorial", 11, False),
            ("Wordpress Designer", "PHP, HTML, CSS, WordPress", 3.0, "Associate", "Blog styling", 12, False),
            ("Backend Java Dev", "Java, Spring Boot, MySQL", 4.0, "Bachelor's", "APIs", 13, False),
            ("Linux Admin", "Linux, Shell, Networking", 5.0, "Bachelor's", "Server monitoring", 14, False),
            ("QA Tester", "Manual testing, Bug reports", 2.0, "Bachelor's", "Regression testing", 15, False),
            ("Content Strategist", "Copy, Editing, SEO", 4.0, "Bachelor's", "Articles", 16, False),
            ("HR Manager", "Payroll, Benefits", 5.0, "Bachelor's", "People ops", 17, False),
            ("Accountant", "Audit, Tax, Excel", 6.0, "Bachelor's", "Financials", 18, False),
            ("Legal Counsel", "Contracts, IP", 7.0, "Doctorate", "Legal compliance", 19, False),
            ("Customer Support", "Zendesk, Phone, Email", 3.0, "High School", "Support tickets", 20, False),
        ]

    for idx, (title, skills_str, exp_yrs, edu, proj_desc, rec_rank, is_shortlisted) in enumerate(archetypes, 1):
        resume_text = f"""
Candidate #{idx} - {title}
Summary:
Professional with {exp_yrs} years of verified experience.
Technical Skills:
{skills_str}
Experience:
{title} | Enterprise Tech ({2026 - int(exp_yrs)} - Present)
- Led development and operational scaling.
Projects:
- Key Project: {proj_desc}
Education:
{edu} in Computer Science or Related Field
"""
        candidates.append({
            "id": (job_id * 100) + idx,
            "title": title,
            "skills": [s.strip() for s in skills_str.split(",")],
            "experience_years": exp_yrs,
            "education": edu,
            "project_description": proj_desc,
            "resume_text": resume_text,
            "recruiter_rank": rec_rank,
            "recruiter_shortlisted": is_shortlisted
        })

    return candidates

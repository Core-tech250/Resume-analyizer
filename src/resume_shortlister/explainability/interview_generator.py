from typing import List, Dict, Any
from src.resume_shortlister.parsers.structured_extractor import StructuredResume
from src.resume_shortlister.ranking.multi_factor_scorer import CandidateMultiFactorScore

def generate_interview_questions(
    structured: StructuredResume,
    score: CandidateMultiFactorScore,
    job_title: str
) -> List[Dict[str, str]]:
    """
    Generates intelligent, tailored interview questions for HR and technical interviewers:
    - Gap-probe questions (addressing missing required skills & experience deficits)
    - Project-depth questions (probing real project execution & architecture)
    - Competency & system design questions
    """
    questions: List[Dict[str, str]] = []

    # 1. Questions targeting identified skill gaps
    if score.missing_required_skills:
        for missing_skill in score.missing_required_skills[:3]:
            questions.append({
                "category": "Skill Gap Verification",
                "target": missing_skill,
                "question": (
                    f"Our role requires '{missing_skill}', which is not prominent on your resume. "
                    f"Have you worked with '{missing_skill}' in any personal projects or previous environments? "
                    f"How quickly can you become productive with it?"
                )
            })

    # 2. Questions targeting experience gaps if flagged
    if score.hard_requirement_flags:
        questions.append({
            "category": "Experience & Growth Acceleration",
            "target": "Experience Level",
            "question": (
                f"This position is scoped for a {job_title}. Can you share an example of a project where you "
                f"took ownership of an ambiguous, high-impact engineering challenge beyond your formal experience level?"
            )
        })

    # 3. Project deep-dive questions
    if structured.projects:
        for proj in structured.projects[:2]:
            title = proj.get("title", "your technical project")
            questions.append({
                "category": "Project Architecture & Scale",
                "target": title[:40],
                "question": (
                    f"In your project '{title[:50]}': What was the single biggest architectural challenge or performance "
                    f"bottleneck you encountered, and what specific trade-offs did you make to resolve it?"
                )
            })
            questions.append({
                "category": "Production Readiness",
                "target": title[:40],
                "question": (
                    f"For '{title[:50]}': How did you ensure test coverage, reliability, and error monitoring? "
                    f"If you had to redesign it for 10x traffic today, what would you change?"
                )
            })

    # 4. Core strengths verification questions
    if score.matched_required_skills:
        top_skill = score.matched_required_skills[0]
        questions.append({
            "category": "Technical Depth",
            "target": top_skill,
            "question": (
                f"You have demonstrated proficiency in '{top_skill}'. "
                f"Can you walk us through the most complex problem you have solved using '{top_skill}', "
                f"and how you optimized for performance and maintainability?"
            )
        })

    # Fallback if few questions generated
    if len(questions) < 3:
        questions.append({
            "category": "System Design & Methodology",
            "target": "General Fit",
            "question": "Can you describe your ideal development workflow from receiving requirements to CI/CD and deployment?"
        })

    return questions

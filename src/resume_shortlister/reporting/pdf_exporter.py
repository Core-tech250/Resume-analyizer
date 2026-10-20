import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_shortlist_pdf_report(
    job_info: Dict[str, Any],
    candidates: List[Dict[str, Any]]
) -> bytes:
    """
    Generates an executive, professional PDF Recruiter Shortlisting Report.
    Includes job specification, shortlist statistics, candidate score breakdowns,
    strengths, gaps, and suggested interview questions.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'BoldDark',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#166534')
    )

    story = []

    # Title & Header
    story.append(Paragraph("Explainable Resume Shortlisting Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M UTC')} • Decision-Support Summary for HR", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=0, spaceAfter=12))

    # Job Profile Section
    story.append(Paragraph("1. Target Job Profile Specification", h2_style))
    job_table_data = [
        [Paragraph("Role Title:", bold_style), Paragraph(str(job_info.get("title", "N/A")), body_style)],
        [Paragraph("Department:", bold_style), Paragraph(str(job_info.get("department", "General")), body_style)],
        [Paragraph("Min Experience:", bold_style), Paragraph(f"{job_info.get('min_experience_years', 0.0)} years", body_style)],
        [Paragraph("Education Required:", bold_style), Paragraph(str(job_info.get("min_education", "Bachelor's")), body_style)],
        [Paragraph("Required Skills:", bold_style), Paragraph(", ".join(job_info.get("required_skills", [])), body_style)],
        [Paragraph("Preferred Skills:", bold_style), Paragraph(", ".join(job_info.get("nice_to_have_skills", [])), body_style)],
    ]
    t_job = Table(job_table_data, colWidths=[120, 420])
    t_job.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_job)
    story.append(Spacer(1, 14))

    # Shortlist Overview Table
    story.append(Paragraph(f"2. Ranked Candidates Summary ({len(candidates)} Candidates)", h2_style))
    summary_data = [
        [
            Paragraph("Rank", bold_style),
            Paragraph("Candidate ID", bold_style),
            Paragraph("Score", bold_style),
            Paragraph("Skills", bold_style),
            Paragraph("Exp", bold_style),
            Paragraph("Projects", bold_style),
            Paragraph("Edu", bold_style),
            Paragraph("HR Status", bold_style)
        ]
    ]

    for c in candidates:
        summary_data.append([
            Paragraph(f"#{c.get('rank', 1)}", bold_style),
            Paragraph(c.get("candidate_id", ""), body_style),
            Paragraph(f"<b>{c.get('percentage_score', 0):.1f}%</b>", badge_style),
            Paragraph(f"{c.get('skills_score', 0):.0f}%", body_style),
            Paragraph(f"{c.get('experience_score', 0):.0f}%", body_style),
            Paragraph(f"{c.get('projects_score', 0):.0f}%", body_style),
            Paragraph(f"{c.get('education_score', 0):.0f}%", body_style),
            Paragraph(c.get("hr_status", "Shortlisted"), bold_style)
        ])

    t_summary = Table(summary_data, colWidths=[40, 90, 60, 50, 50, 55, 50, 145])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 16))

    # Candidate Deep Dives
    story.append(Paragraph("3. Candidate Evidence, Gaps & Interview Questions", h2_style))

    for c in candidates:
        cand_flowables = []
        rank_header = (
            f"<b>#{c.get('rank', 1)}: {c.get('candidate_id', '')}</b> "
            f"— Final Score: <b>{c.get('percentage_score', 0):.1f}%</b> "
            f"| Status: <i>{c.get('hr_status', 'Shortlisted')}</i>"
        )
        cand_flowables.append(Paragraph(rank_header, bold_style))
        cand_flowables.append(Spacer(1, 4))

        # Strengths
        strengths = c.get("strengths", [])
        if strengths:
            s_text = "<b>Key Strengths:</b><br/>• " + "<br/>• ".join(strengths[:3])
            cand_flowables.append(Paragraph(s_text, body_style))
            cand_flowables.append(Spacer(1, 4))

        # Gaps
        gaps = c.get("gaps", [])
        if gaps:
            g_text = "<b>Identified Gaps:</b><br/>• " + "<br/>• ".join(gaps[:2])
            cand_flowables.append(Paragraph(g_text, body_style))
            cand_flowables.append(Spacer(1, 4))

        # Questions
        questions = c.get("interview_questions", [])
        if questions:
            q_text = "<b>Recommended Interview Questions:</b><br/>"
            for q_item in questions[:2]:
                q_text += f"<i>[{q_item.get('category', 'Interview')}]:</i> {q_item.get('question', '')}<br/>"
            cand_flowables.append(Paragraph(q_text, body_style))
            cand_flowables.append(Spacer(1, 4))

        # Recruiter Notes if any
        notes = c.get("hr_notes", "")
        if notes:
            cand_flowables.append(Paragraph(f"<b>Recruiter Evaluation Notes:</b> <i>{notes}</i>", body_style))
            cand_flowables.append(Spacer(1, 4))

        cand_flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=8))
        story.append(KeepTogether(cand_flowables))

    # Sign-off box
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. HR Authorization & Review Sign-Off", h2_style))
    sign_table_data = [
        [Paragraph("Reviewed By (HR Lead): _______________________", body_style), Paragraph("Date: _______________", body_style)],
        [Paragraph("Final Hiring Decision: [  ] Approved for Interview    [  ] On Hold    [  ] Rejected", body_style), Paragraph("Signature: _______________", body_style)]
    ]
    t_sign = Table(sign_table_data, colWidths=[350, 190])
    t_sign.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sign)

    doc.build(story)
    return buffer.getvalue()

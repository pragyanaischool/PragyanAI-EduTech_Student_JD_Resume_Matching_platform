import json
import re
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings


def get_llm(model: str = settings.DEFAULT_LLM_MODEL, temperature: float = 0.1) -> ChatGroq:
    """Instantiate a ChatGroq client."""
    return ChatGroq(
        model=model,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature
    )


def extract_clean_json(text: str) -> Dict[str, Any]:
    """Strips Markdown fences and safely loads JSON from LLM responses."""
    cleaned = text.strip()
    cleaned = re.sub(r'^```json\s*', '', cleaned)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {}


def build_markdown_resume(raw_text: str, github: str = "", linkedin: str = "") -> str:
    """Converts raw unstructured candidate notes into an ATS-friendly Markdown resume."""
    llm = get_llm()
    prompt = f"""
Convert the following unstructured CV/profile notes into an executive, ATS-optimized Markdown resume.
Ensure strong action verbs, quantifiable achievements, clear structure, and correct contact information.

Incorporated Social Profiles:
- GitHub: {github if github else 'N/A'}
- LinkedIn: {linkedin if linkedin else 'N/A'}

Raw Information:
{raw_text}

Required Format:
# [Candidate Full Name]
**Email | Phone | Location | [GitHub] | [LinkedIn]**

## Executive Summary
[A compelling 3-sentence summary highlighting core competency and years of experience]

## Technical Skills
- **Languages:** ...
- **Frameworks & Libraries:** ...
- **Cloud & Databases:** ...
- **Tools & Methodologies:** ...

## Professional Experience
### [Job Title] | [Company Name] | [Dates]
- Bullet point with action verb and quantifiable impact
- Bullet point with action verb and quantifiable impact

## Key Projects
### [Project Name] | [Tech Stack Used]
- Bullet point explaining architectural contribution and results

## Education & Certifications
- Degree, Major — University (Year)
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert executive ATS resume architect."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip()


def refine_resume_section(section_name: str, content: str) -> str:
    """Refines an individual resume section with active verbs and zero grammatical errors."""
    llm = get_llm()
    prompt = f"""
Refine this resume section: '{section_name}'.
Content to improve:
{content}

Tasks:
1. Eliminate weak phrasing (e.g., 'worked on', 'helped with') in favor of high-impact leadership verbs (e.g., 'Architected', 'Spearheaded', 'Optimized', 'Engineered').
2. Fix all spelling and grammatical errors.
3. Structure bullet points cleanly in Markdown.

Return ONLY the refined Markdown text:
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert ATS copywriter."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip()


def match_cv_to_jd(cv_text: str, jd_text: str) -> Dict[str, Any]:
    """Performs full gap analysis, SWOT evaluation, and ATS match scoring."""
    llm = get_llm()
    prompt = f"""
Analyze the candidate's Resume against the active Job Description.

Candidate Resume:
{cv_text}

Job Description:
{jd_text}

Return strict JSON with this exact schema:
{{
    "ats_score": 85.0,
    "swot": {{
        "strengths": ["Strength 1...", "Strength 2..."],
        "weaknesses": ["Weakness 1...", "Weakness 2..."],
        "opportunities": ["Opportunity 1...", "Opportunity 2..."],
        "threats": ["Threat 1...", "Threat 2..."]
    }},
    "missing_keywords": ["keyword1", "keyword2", "keyword3"],
    "section_gaps": [
        {{"section": "Technical Skills", "status": "Strong / Missing Key Items", "feedback": "Detailed feedback..."}},
        {{"section": "Experience & Seniority", "status": "Aligned / Underqualified", "feedback": "Detailed feedback..."}},
        {{"section": "Project Depth", "status": "Verified / Lacks Scale", "feedback": "Detailed feedback..."}}
    ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an ATS compliance auditor and executive technical recruiter."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)


def optimize_ats_resume(cv_text: str, jd_text: str, missing_keywords: List[str]) -> str:
    """Rewrites the Markdown resume to organically incorporate missing technical keywords."""
    llm = get_llm()
    prompt = f"""
Rewrite this candidate's Markdown resume to organically integrate these missing ATS keywords: {missing_keywords}.
Align the project achievements and skill taxonomies with the target Job Description while preserving complete truthfulness.

Original Resume:
{cv_text}

Target Job Description:
{jd_text}

Return ONLY the complete, optimized Markdown resume:
"""
    res = llm.invoke([
        SystemMessage(content="You are a specialized ATS optimization and keyword alignment strategist."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip()


def generate_cover_letter(cv_text: str, jd_text: str) -> str:
    """Generates a high-converting, tailored cover letter matching candidate achievements to JD pain points."""
    llm = get_llm()
    prompt = f"""
Write a compelling, professional, high-converting Cover Letter matching the candidate's exact achievements to this Job Description.

Candidate Resume:
{cv_text}

Target Job Description:
{jd_text}

Structure:
- Date & Recipient Details
- Engaging Opening Statement (Hook + Role Alignment)
- 3 Bulleted Proof Points tying measurable past accomplishments to the company's stated requirements
- Confident Closing and Call to Action
"""
    res = llm.invoke([
        SystemMessage(content="You are an executive career strategist and talent acquisition director."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip()


def create_interview_questions(jd_text: str) -> Dict[str, List[str]]:
    """Generates 6 role-specific questions across HR, practical skill, and system architecture categories."""
    llm = get_llm()
    prompt = f"""
Generate 6 targeted interview questions for the following Job Description:
- 2 HR / Behavioral questions (Culture, leadership, conflict resolution)
- 2 Skill / Practical scenario questions (Hands-on problem solving)
- 2 Technical Architecture Deep Dive questions (System design, concurrency, scale)

Job Description:
{jd_text}

Return strict JSON:
{{
    "hr": ["Q1", "Q2"],
    "skill": ["Q3", "Q4"],
    "tech": ["Q5", "Q6"]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a VP of Engineering and Lead Technical Interviewer."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)


def evaluate_interview_answer(question: str, answer: str, jd_text: str) -> Dict[str, str]:
    """Grades a candidate's interview response with critique, scoring, and a model STAR answer."""
    llm = get_llm()
    prompt = f"""
Evaluate this candidate's interview response:

Question Asked: {question}
Candidate's Response: {answer}
Job Context: {jd_text}

Evaluate thoroughly and return strict JSON:
{{
    "score": "8.5/10",
    "critique": "Actionable feedback on candidate's technical precision, communication style, and missed nuances.",
    "star_answer": "A perfect model STAR response (Situation, Task, Action, Result) demonstrating mastery."
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a strict technical interview evaluator and executive coach."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)


def generate_learning_roadmap(missing_skills: List[str], jd_text: str) -> Dict[str, Any]:
    """Constructs a 4-week project-based upskilling plan for missing competencies."""
    llm = get_llm()
    prompt = f"""
Create a 4-week structured, project-driven upskilling roadmap to bridge these missing skills: {missing_skills}.
Job Context: {jd_text}

Return strict JSON:
{{
    "focus_summary": "Primary competence and architectural domain focus",
    "weekly_schedule": [
        {{"week": "Week 1", "topic": "Fundamentals & Core Stack", "project": "Hands-on project deliverable...", "deliverable": "GitHub Repo / Demo"}},
        {{"week": "Week 2", "topic": "System Integration", "project": "Hands-on project deliverable...", "deliverable": "GitHub Repo / Demo"}},
        {{"week": "Week 3", "topic": "Advanced Architecture & Scaling", "project": "Hands-on project deliverable...", "deliverable": "Benchmark Suite"}},
        {{"week": "Week 4", "topic": "Production Hardening & Deployment", "project": "Hands-on project deliverable...", "deliverable": "Deployed App / Article"}}
    ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a corporate technical curriculum architect and engineering mentor."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)


def parse_and_structure_jd(raw_text: str) -> Dict[str, Any]:
    """Parses raw JD text into a structured JSON schema."""
    llm = get_llm(model=settings.FAST_LLM_MODEL)
    prompt = f"""
Extract structured recruitment criteria from this raw Job Description:
{raw_text}

Return strict JSON:
{{
    "title": "Role Title",
    "department": "Department / Team",
    "experience_years_min": 4.0,
    "primary_skills": ["Skill1", "Skill2", "Skill3"],
    "secondary_skills": ["Skill4", "Skill5"],
    "location_type": "Remote / Onsite / Hybrid",
    "expected_ctc_range": "Salary band if specified or Market Standard",
    "summary": "2-sentence executive summary of the position"
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a structured data extractor for corporate recruitment systems."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)


def evaluate_pre_screening(
    current_ctc: str,
    expected_ctc: str,
    notice_period: int,
    buyout: bool,
    current_loc: str,
    job_loc: str,
    relocate: bool,
    skill_notes: str
) -> Dict[str, Any]:
    """Validates pre-screening parameters for candidate logistics feasibility."""
    llm = get_llm(model=settings.FAST_LLM_MODEL)
    prompt = f"""
Evaluate if this candidate passes baseline pre-screening criteria:
- Current CTC: {current_ctc} | Expected CTC: {expected_ctc}
- Notice Period: {notice_period} Days | Buyout Feasible: {buyout}
- Current Location: {current_loc} | Job Location: {job_loc} | Willing to Relocate: {relocate}
- Key Skill Experience Notes: {skill_notes}

Rules:
- Notice period > 60 days without buyout is high risk.
- Location mismatch with no relocation is disqualifying unless remote.

Return strict JSON:
{{
    "is_qualified": true,
    "status": "Passed Pre-Screening / Flagged / Disqualified",
    "risk_flags": ["List of any logistical or compensation risks..."],
    "summary": "Concise summary evaluation for the recruiter"
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an automated talent acquisition pre-screening validator."),
        HumanMessage(content=prompt)
    ])
    return extract_clean_json(res.content)

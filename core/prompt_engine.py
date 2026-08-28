import os
import re
import json
from typing import Dict, Any, List, Optional
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings


# ==============================================================================
# 0. LLM Client Initialization & Secret Fallback Resolver
# ==============================================================================
def get_groq_api_key() -> str:
    """
    Safely retrieves the Groq Cloud API Key with fallback precedence:
    1. settings.GROQ_API_KEY
    2. st.secrets["GROQ_API_KEY"]
    3. os.environ["GROQ_API_KEY"]
    """
    if getattr(settings, "GROQ_API_KEY", None):
        return str(settings.GROQ_API_KEY).strip()

    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass

    return os.getenv("GROQ_API_KEY", "").strip()


def get_llm(model: Optional[str] = None, temperature: float = 0.1) -> ChatGroq:
    """
    Instantiates and returns a configured ChatGroq client.
    """
    api_key = get_groq_api_key()
    selected_model = model or getattr(settings, "DEFAULT_LLM_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        st.error(
            "⚠️ **Groq API Key Not Found!**\n\n"
            "Please configure `GROQ_API_KEY = 'gsk_...'` inside **Streamlit Cloud Settings -> Secrets** or your local `.env` file."
        )
        st.stop()

    return ChatGroq(
        model=selected_model,
        groq_api_key=api_key,
        temperature=temperature
    )


# ==============================================================================
# 1. build_markdown_resume
# ==============================================================================
def build_markdown_resume(raw_text: str, github_url: str = "", linkedin_url: str = "") -> str:
    """
    Transforms unstructured notes, parsed documents, and social links
    into an ATS-compliant, publication-ready Markdown resume.
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are an Executive ATS Resume Architect and Technical Copywriter.

Transform the following raw resume/profile notes into an ATS-optimized, high-impact Markdown resume.

Guidelines:
1. Use standard Markdown structure (# for Candidate Name, ## for Sections, ### for Roles/Projects).
2. Incorporate candidate contact metadata cleanly at the top including GitHub ({github_url}) and LinkedIn ({linkedin_url}) if provided.
3. Organize into clear sections:
   - ## Executive Summary (3-4 impactful sentences with years of experience, core domains, high-level impact)
   - ## Technical Skills (Categorized bullets: Languages, AI/Multi-Agent, Databases/Vectors, Cloud/DevOps, Tools)
   - ## Professional Experience (Google X-Y-Z formula: Accomplished [X], as measured by [Y], by doing [Z], with high-impact action verbs and quantified metrics)
   - ## Key Projects (Title format: `### [Project Name] | [Tech Stack]`, implementation details, measurable impact)
   - ## Education & Certifications (Degree, Institution, Year, GPA/Honors, Accredited Certs)
4. Do NOT hallucinate entirely fabricated employers, but elevate weak phrasing into authoritative technical achievements.
5. Return ONLY clean Markdown text without enclosing markdown code fences (no ```markdown).

Raw Input Profile:
\"\"\"{raw_text}\"\"\"
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert executive ATS resume architect."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip().replace("```markdown", "").replace("```", "").strip()


# ==============================================================================
# 2. extract_resume_sections
# ==============================================================================
def extract_resume_sections(markdown_text: str) -> Dict[str, str]:
    """
    Parses a Markdown resume and splits it into standard structural sections
    using regex pattern-matching.
    """
    sections = {
        "Executive Summary": "",
        "Technical Skills": "",
        "Professional Experience": "",
        "Key Projects": "",
        "Education & Certifications": "",
        "Other Details": ""
    }

    if not markdown_text or not markdown_text.strip():
        return sections

    patterns = {
        "Executive Summary": r"##\s*(?:Executive\s+Summary|Summary|Profile|About\s+Me)\s*\n(.*?)(?=\n##|\Z)",
        "Technical Skills": r"##\s*(?:Technical\s+Skills|Skills|Core\s+Competencies|Tech\s+Stack)\s*\n(.*?)(?=\n##|\Z)",
        "Professional Experience": r"##\s*(?:Professional\s+Experience|Experience|Work\s+History|Employment)\s*\n(.*?)(?=\n##|\Z)",
        "Key Projects": r"##\s*(?:Key\s+Projects|Projects|Selected\s+Projects)\s*\n(.*?)(?=\n##|\Z)",
        "Education & Certifications": r"##\s*(?:Education(?:\s*&\s*Certifications)?|Certifications|Academic\s+Background)\s*\n(.*?)(?=\n##|\Z)"
    }

    for section_name, pattern in patterns.items():
        match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[section_name] = match.group(1).strip()

    header_match = re.search(r"^(.*?)(?=\n##|\Z)", markdown_text, re.DOTALL)
    if header_match and header_match.group(1).strip():
        sections["Other Details"] = header_match.group(1).strip()

    return sections


# ==============================================================================
# 3. update_resume_section
# ==============================================================================
def update_resume_section(full_markdown: str, section_name: str, new_content: str) -> str:
    """
    Replaces an existing section's content in the full Markdown document,
    or appends it if the section did not previously exist.
    """
    patterns = {
        "Executive Summary": r"(##\s*(?:Executive\s+Summary|Summary|Profile|About\s+Me)\s*\n)(.*?)(?=\n##|\Z)",
        "Technical Skills": r"(##\s*(?:Technical\s+Skills|Skills|Core\s+Competencies|Tech\s+Stack)\s*\n)(.*?)(?=\n##|\Z)",
        "Professional Experience": r"(##\s*(?:Professional\s+Experience|Experience|Work\s+History|Employment)\s*\n)(.*?)(?=\n##|\Z)",
        "Key Projects": r"(##\s*(?:Key\s+Projects|Projects|Selected\s+Projects)\s*\n)(.*?)(?=\n##|\Z)",
        "Education & Certifications": r"(##\s*(?:Education(?:\s*&\s*Certifications)?|Certifications|Academic\s+Background)\s*\n)(.*?)(?=\n##|\Z)"
    }

    pattern = patterns.get(section_name)
    if pattern and re.search(pattern, full_markdown, re.DOTALL | re.IGNORECASE):
        return re.sub(
            pattern,
            rf"\g<1>{new_content.strip()}\n\n",
            full_markdown,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()
    else:
        return f"{full_markdown.strip()}\n\n## {section_name}\n{new_content.strip()}\n"


# ==============================================================================
# 4. refine_resume_section
# ==============================================================================
def refine_resume_section(section_name: str, content: str) -> str:
    """
    Refines a single resume section with active verbs, quantified results,
    and strict ATS-friendly Markdown formatting.
    """
    llm = get_llm(temperature=0.2)

    section_rules = {
        "Executive Summary": (
            "- Craft a punchy 3-4 sentence narrative highlighting total years of experience, core tech domains, and high-level architectural impact.\n"
            "- Eliminate passive phrases like 'Responsible for' or 'Looking to'."
        ),
        "Technical Skills": (
            "- Structure competencies into categorized bullet points (e.g., Languages, Frameworks, Vector DBs, Cloud & DevOps).\n"
            "- Ensure exact capitalization of modern frameworks (e.g., LangGraph, FastAPI, PyTorch, ChromaDB, Groq)."
        ),
        "Professional Experience": (
            "- Start every bullet point with a high-impact action verb (e.g., 'Architected', 'Spearheaded', 'Optimized', 'Scaled').\n"
            "- Incorporate Google X-Y-Z formula: Accomplished [X], as measured by [Y], by doing [Z].\n"
            "- Highlight quantifiable metrics (%, ms latency, $ saved, throughput)."
        ),
        "Key Projects": (
            "- Title each project with `### [Project Name] | [Tech Stack]`.\n"
            "- Detail the architectural problem, core implementation, and measurable results."
        ),
        "Education & Certifications": (
            "- Clean format: Degree, Specialization — Institution (Year), followed by accredited certifications."
        )
    }

    specific_guidance = section_rules.get(section_name, "- Use active voice and professional formatting.")

    prompt = f"""
You are an Executive ATS Resume Architect and Technical Copywriter.

Target Section: {section_name}
Specific Transformation Guidelines:
{specific_guidance}

Raw Draft / Existing Content:
\"\"\"{content}\"\"\"

Task:
1. Fix all grammar, phrasing, and awkward syntax.
2. Upgrade weak expressions into authoritative technical statements with action verbs and metrics.
3. Return ONLY the refined Markdown content without markdown outer fences, introductory notes, or meta explanations.
"""
    res = llm.invoke([
        SystemMessage(content="You are a professional ATS resume copywriting engine."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip().replace("```markdown", "").replace("```", "").strip()


# ==============================================================================
# 5. match_cv_to_jd & run_swot_analysis
# ==============================================================================
def match_cv_to_jd(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Conducts an in-depth SWOT gap analysis between a candidate's resume and a target JD.
    Returns a structured dictionary containing score, breakdown, and categorical SWOT lists.
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are an elite Technical Recruiter and Engineering Hiring Committee Lead.

Perform a thorough SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis and calculate a compatibility match score (0-100) between the candidate's resume and the job description.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Description:
\"\"\"{jd_text}\"\"\"

Return ONLY a valid JSON object matching this exact structure:
{{
  "match_score": 85.5,
  "summary": "Concise 2-sentence executive hiring verdict.",
  "strengths": [
    "Specific technical alignment 1 with project evidence",
    "Specific technical alignment 2"
  ],
  "weaknesses": [
    "Identified skill gap or missing qualification 1",
    "Identified skill gap 2"
  ],
  "opportunities": [
    "High-value growth area or adjacent competency candidate can leverage",
    "Strategic value add"
  ],
  "threats": [
    "Hiring risk, unaddressed prerequisite, or compensation/seniority mismatch"
  ],
  "missing_keywords": [
    "Keyword1",
    "Keyword2",
    "Framework3"
  ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a strict technical hiring evaluator. You must return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip()
    if cleaned_json.startswith("```json"):
        cleaned_json = cleaned_json[7:]
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json[3:]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json[:-3]
    cleaned_json = cleaned_json.strip()

    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "match_score": 50.0,
            "summary": "Automated evaluation completed with parsing fallback.",
            "strengths": ["Demonstrates baseline technical background."],
            "weaknesses": ["Detailed alignment requires manual verification."],
            "opportunities": ["Potential for on-the-job skill acquisition."],
            "threats": ["Skill overlap requires technical deep-dive."],
            "missing_keywords": ["FastAPI", "Docker", "PostgreSQL"]
        }


# Direct alias mapping
run_swot_analysis = match_cv_to_jd
match_jd_to_cv = match_cv_to_jd
evaluate_candidate_fit = match_cv_to_jd


# ==============================================================================
# 6. optimize_ats_keywords & optimize_ats_resume
# ==============================================================================
def optimize_ats_keywords(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Identifies high-priority missing keywords and provides natural, contextual
    bullet point recommendations for candidate incorporation.
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are an ATS Optimization Specialist.

Analyze the candidate resume against the target job description to identify missing keywords and craft natural bullet points that integrate them truthfully.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Job Description:
\"\"\"{jd_text}\"\"\"

Return ONLY a valid JSON object with this schema:
{{
  "ats_score_estimate": 78,
  "critical_missing_keywords": ["Tool1", "Framework2", "Methodology3"],
  "recommended_bullet_insertions": [
    {{
      "target_section": "Professional Experience",
      "suggested_bullet": "Architected distributed caching using Redis and Celery, reducing API latency by 35%."
    }}
  ],
  "keyword_density_advice": "Specific 2-sentence guidance on terminology density."
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an ATS keyword optimization engine. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "ats_score_estimate": 70,
            "critical_missing_keywords": ["Docker", "Kubernetes", "CI/CD"],
            "recommended_bullet_insertions": [],
            "keyword_density_advice": "Align terminology with the target job description."
        }


# Direct alias mapping to resolve optimize_ats_resume import
optimize_ats_resume = optimize_ats_keywords


# ==============================================================================
# 7. generate_cover_letter
# ==============================================================================
def generate_cover_letter(resume_text: str, jd_text: str, company_name: str = "Hiring Team") -> str:
    """
    Synthesizes a compelling, tailored cover letter aligning candidate achievements with the JD.
    """
    llm = get_llm(temperature=0.3)

    prompt = f"""
You are an Executive Career Coach. Write a tailored, persuasive, and authentic 3-paragraph cover letter for the following candidate applying to {company_name}.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Description:
\"\"\"{jd_text}\"\"\"

Structure:
1. Hook & Introduction (Role targeted, enthusiasm, high-level value proposition)
2. Evidence & Core Impact (Concrete achievements directly matching top requirements in JD)
3. Closing & Call to Action (Culture fit, mutual value, confident call to discuss)

Return ONLY the cover letter in clean Markdown.
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert executive career strategist."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip().replace("```markdown", "").replace("```", "").strip()


# ==============================================================================
# 8. generate_upskill_roadmap
# ==============================================================================
def generate_upskill_roadmap(missing_skills: List[str], target_role: str) -> List[Dict[str, Any]]:
    """
    Generates an actionable 4-week project-based upskilling roadmap
    addressing identified skill gaps.
    """
    llm = get_llm(temperature=0.2)

    prompt = f"""
You are a Principal Engineering Mentor and Curriculum Director.

Design a rigorous 4-Week Upskilling Roadmap for an engineer targeting the role of '{target_role}', focusing on closing these specific skill gaps: {', '.join(missing_skills)}.

Return ONLY a valid JSON list of 4 objects (one for each week):
[
  {{
    "week": 1,
    "title": "Week 1: Core Theoretical Foundations & Setup",
    "focus_skill": "{missing_skills[0] if missing_skills else 'Core Framework'}",
    "learning_objectives": ["Objective 1", "Objective 2"],
    "hands_on_project": "Build a functional mini-service demonstrating X.",
    "search_queries": ["Search term 1 documentation", "Best tutorial for X"]
  }},
  {{
    "week": 2,
    "title": "Week 2: Advanced Architecture & Integration",
    "focus_skill": "{missing_skills[1] if len(missing_skills) > 1 else 'System Architecture'}",
    "learning_objectives": ["Objective 1", "Objective 2"],
    "hands_on_project": "Integrate asynchronous worker queues and caching.",
    "search_queries": ["Advanced system design tutorial", "Best practices guide"]
  }},
  {{
    "week": 3,
    "title": "Week 3: Testing, Benchmarking & Optimization",
    "focus_skill": "{missing_skills[2] if len(missing_skills) > 2 else 'Performance Tuning'}",
    "learning_objectives": ["Objective 1", "Objective 2"],
    "hands_on_project": "Benchmark throughput under simulated high-load scenarios.",
    "search_queries": ["Performance profiling tutorial", "Load testing guide"]
  }},
  {{
    "week": 4,
    "title": "Week 4: Production Deployment & CI/CD",
    "focus_skill": "{missing_skills[3] if len(missing_skills) > 3 else 'Cloud & Containerization'}",
    "learning_objectives": ["Objective 1", "Objective 2"],
    "hands_on_project": "Containerize solution with Docker and automate CI/CD pipeline.",
    "search_queries": ["Docker production deployment guide", "GitHub Actions CI CD"]
  }}
]
"""
    res = llm.invoke([
        SystemMessage(content="You are a senior technical curriculum architect. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return [
            {
                "week": 1,
                "title": "Week 1: Core Fundamentals",
                "focus_skill": missing_skills[0] if missing_skills else "Target Framework",
                "learning_objectives": ["Study architecture blueprints", "Review production documentation"],
                "hands_on_project": "Implement reference proof-of-concept repository.",
                "search_queries": ["Framework getting started guide"]
            }
        ]


# ==============================================================================
# 9. generate_interview_questions
# ==============================================================================
def generate_interview_questions(jd_text: str, resume_text: str, round_type: str = "Technical Deep Dive") -> List[str]:
    """
    Generates 5 tailored, probing interview questions based on candidate CV and target JD.
    """
    llm = get_llm(temperature=0.3)

    prompt = f"""
You are a Senior Engineering Hiring Manager conducting a {round_type} interview.

Target Job Description:
\"\"\"{jd_text}\"\"\"

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Generate exactly 5 probing, scenario-driven interview questions assessing the candidate's claims, technical depth, and architectural problem-solving ability.

Return ONLY a valid JSON array of 5 strings:
[
  "Question 1...",
  "Question 2...",
  "Question 3...",
  "Question 4...",
  "Question 5..."
]
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert technical interviewer. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return [
            "Can you walk me through the architecture of the most complex system you designed in your recent role?",
            "How do you approach latency vs. accuracy trade-offs when designing retrieval pipelines?",
            "Describe a production incident or bug you resolved under tight time constraints.",
            "How do you design database schema indexes and query execution plans for high-throughput microservices?",
            "What strategies do you use to evaluate and benchmark LLM application outputs?"
        ]


# ==============================================================================
# 10. evaluate_interview_response
# ==============================================================================
def evaluate_interview_response(question: str, candidate_answer: str, jd_text: str) -> Dict[str, Any]:
    """
    Evaluates a candidate's verbal or written mock interview response,
    providing score breakdown and feedback.
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are an Expert Technical Interview Assessor.

Interview Question:
\"{question}\"

Candidate's Answer:
\"{candidate_answer}\"

Context Job Description:
\"{jd_text}\"

Evaluate the response across Technical Correctness, Communication Clarity, Depth, and Relevance.

Return ONLY a valid JSON object:
{{
  "score": 85,
  "verdict": "Strong Answer / Needs Improvement / Exceptional",
  "strengths": ["Point 1", "Point 2"],
  "areas_for_improvement": ["Point 1", "Point 2"],
  "ideal_response_summary": "Concise 2-sentence summary of what a senior-level answer should emphasize."
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an interview grading engine. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "score": 75,
            "verdict": "Solid Response",
            "strengths": ["Addressed core premise directly."],
            "areas_for_improvement": ["Incorporate more quantified metrics and architectural edge cases."],
            "ideal_response_summary": "Focus on trade-offs, scalability constraints, and concrete benchmarks."
        }


# ==============================================================================
# 11. screen_candidate_logistics & RAG Helper Functions
# ==============================================================================
def screen_candidate_logistics(prescreen_inputs: Dict[str, Any], jd_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates practical logistics (notice period, compensation expectations,
    relocation/visa feasibility) against employer constraints.
    """
    llm = get_llm(model=getattr(settings, "FAST_LLM_MODEL", "llama-3.1-8b-instant"), temperature=0.0)

    prompt = f"""
You are an HR Logistics Pre-Screening Agent.

Candidate Provided Logistics:
{json.dumps(prescreen_inputs, indent=2)}

Employer Role Constraints:
{json.dumps(jd_requirements, indent=2)}

Evaluate feasibility (Pass/Flag/Fail) and provide a concise justification.

Return ONLY a valid JSON object:
{{
  "status": "PASS",
  "confidence_score": 95,
  "flags": [],
  "summary": "Candidate notice period and salary expectations are fully within budget parameters."
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an automated logistics screening engine. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])

    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "status": "PASS",
            "confidence_score": 80,
            "flags": [],
            "summary": "Logistics meet standard recruitment requirements."
        }


def answer_rag_query(query: str, context_documents: List[str]) -> str:
    """
    Answers a grounded talent intelligence or candidate question using retrieved context documents.
    """
    llm = get_llm(temperature=0.1)
    context_str = "\n\n---\n\n".join(context_documents) if context_documents else "No specific documents retrieved."

    prompt = f"""
You are an Enterprise RAG Talent Intelligence Assistant.

Context Documents:
\"\"\"{context_str}\"\"\"

User Query:
\"{query}\"

Instructions:
1. Answer the query accurately using ONLY the facts present in the Context Documents.
2. If the context does not contain sufficient details, state that clearly without guessing.
3. Use bullet points and clear Markdown structure.
"""
    res = llm.invoke([
        SystemMessage(content="You are a grounded RAG factual question answering engine."),
        HumanMessage(content=prompt)
    ])
    return res.content.strip()
# ==============================================================================
# Multi-JD Analysis, Section-Wise Matching & ATS Auto-Tailoring
# ==============================================================================

def analyze_section_wise_match(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Evaluates alignment per resume section (Summary, Skills, Experience, Projects, Education)
    and provides section-specific scores, alignments, and suggested improvements.
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are a Principal Technical Recruiter and Engineering Assessor.

Analyze this candidate resume against the target Job Description on an overall and section-by-section basis.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Description:
\"\"\"{jd_text}\"\"\"

Return ONLY a valid JSON object matching this schema:
{{
  "overall_score": 82,
  "overall_verdict": "2-sentence executive summary of the candidate's alignment.",
  "section_breakdowns": {{
    "Executive Summary": {{
      "score": 85,
      "status": "Strong Match",
      "alignment": "Directly highlights relevant domain and senior background.",
      "gaps": "Lacks specific mention of target cloud ecosystem."
    }},
    "Technical Skills": {{
      "score": 80,
      "status": "Good Match",
      "alignment": "Core programming languages and frameworks are present.",
      "gaps": "Missing orchestration and vector caching tools."
    }},
    "Professional Experience": {{
      "score": 84,
      "status": "Strong Match",
      "alignment": "Proven track record in high-concurrency systems.",
      "gaps": "Metrics on latency and cost optimization could be clearer."
    }},
    "Key Projects": {{
      "score": 78,
      "status": "Moderate Match",
      "alignment": "Architecture is relevant to target microservices.",
      "gaps": "Missing production scale indicators."
    }},
    "Education & Certifications": {{
      "score": 90,
      "status": "Full Match",
      "alignment": "Relevant degree and certifications.",
      "gaps": "None."
    }}
  }}
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert recruitment analyst. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])
    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "overall_score": 75,
            "overall_verdict": "Candidate matches primary technical qualifications with minor gap areas.",
            "section_breakdowns": {}
        }


def auto_tailor_cv_for_jd(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Auto-aligns the resume for target JD ATS matching, highlighting proposed modifications
    and remaining major skill gaps with actionable workout recommendations.
    """
    llm = get_llm(temperature=0.2)

    prompt = f"""
You are an Executive ATS Optimization Architect.

Tailor the candidate's master resume to maximize ATS match score against the target JD while preserving truthfulness.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Description:
\"\"\"{jd_text}\"\"\"

Return ONLY a valid JSON object matching this exact schema:
{{
  "projected_ats_score": 93,
  "tailored_resume_markdown": "Full ATS-optimized resume in pristine Markdown format (# Name, ## Sections, ### Projects)",
  "proposed_changes": [
    {{
      "section": "Professional Experience",
      "original_phrase": "Worked on API performance",
      "modified_phrase": "Engineered distributed caching using Redis, decreasing p99 latency by 42%",
      "rationale": "Incorporates JD keyword 'Redis' with quantifiable metrics"
    }}
  ],
  "residual_missing_skills": [
    {{
      "skill": "Kubernetes Multi-Cluster Orchestration",
      "severity": "High",
      "gap_reason": "JD requires production cluster administration which is absent from CV.",
      "quick_workout": "Deploy a 3-node Kind/K3s local cluster with Helm charts and Prometheus metrics."
    }}
  ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert ATS optimization engine. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])
    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "projected_ats_score": 85,
            "tailored_resume_markdown": resume_text,
            "proposed_changes": [],
            "residual_missing_skills": []
        }


def analyze_multi_jd_skill_gap(resume_text: str, jds_data: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Evaluates resume against multiple target JDs to identify industry-wide common skill gaps
    and create an aggregate 8-week strategic upskilling blueprint.
    """
    llm = get_llm(temperature=0.1)

    jds_summary = "\n\n".join([f"=== JD ID: {j['id']} | Title: {j['title']} ===\n{j['content'][:1200]}" for j in jds_data])

    prompt = f"""
You are a Principal Engineering Dean and Career Strategist.

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Descriptions ({len(jds_data)} Positions):
{jds_summary}

Analyze the collective skill requirements across these JDs against the candidate's CV.

Return ONLY a valid JSON object matching this schema:
{{
  "market_readiness_score": 78,
  "core_competencies_matched": ["Python", "FastAPI", "PostgreSQL"],
  "high_frequency_missing_skills": [
    {{
      "skill_name": "Distributed Tracing (OpenTelemetry)",
      "jd_frequency_pct": 80,
      "market_demand": "Critical",
      "difficulty": "Moderate"
    }},
    {{
      "skill_name": "vLLM / TensorRT-LLM Serving",
      "jd_frequency_pct": 60,
      "market_demand": "High",
      "difficulty": "Advanced"
    }}
  ],
  "eight_week_upskill_curriculum": [
    {{
      "phase": "Weeks 1-2: Observability & Production Monitoring",
      "skills": ["OpenTelemetry", "Prometheus", "Grafana"],
      "deliverable_project": "Build an instrumented FastAPI service exporting distributed traces to Jaeger.",
      "recommended_search_term": "OpenTelemetry FastAPI Jaeger tutorial"
    }},
    {{
      "phase": "Weeks 3-4: High-Throughput Model Serving",
      "skills": ["vLLM", "Triton Inference Server"],
      "deliverable_project": "Deploy quantized Llama-3 model using vLLM engine with streaming endpoints.",
      "recommended_search_term": "vLLM production deployment guide"
    }},
    {{
      "phase": "Weeks 5-6: Advanced Agentic Workflow Graphs",
      "skills": ["LangGraph", "Human-in-the-loop State Machines"],
      "deliverable_project": "Construct a multi-agent self-correcting code generation pipeline.",
      "recommended_search_term": "LangGraph state persistence tutorial"
    }},
    {{
      "phase": "Weeks 7-8: End-to-End Capstone & System Benchmarking",
      "skills": ["Locust load testing", "Docker Compose", "CI/CD"],
      "deliverable_project": "Publish a benchmarked open-source repository showcasing 10,000+ RPS resilience.",
      "recommended_search_term": "FastAPI load testing locust benchmark"
    }}
  ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a principal technical curriculum architect. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])
    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "market_readiness_score": 75,
            "core_competencies_matched": ["Python", "SQL"],
            "high_frequency_missing_skills": [],
            "eight_week_upskill_curriculum": []
        }
# ==============================================================================
# Comprehensive Multi-Track Mock Drive & Multilingual Assessment Engines
# ==============================================================================

def generate_multi_track_questions(
    round_track: str,
    difficulty: str,
    jd_text: str,
    resume_text: str,
    language: str = "English",
    count: int = 5
) -> List[Dict[str, Any]]:
    """
    Generates structured scenario, technical, or cognitive questions across 6 distinct tracks:
    1. HR & Behavioral Fit (STAR method)
    2. Core CS & Software Engineering (OS, DBMS, Networks, OOP, System Design)
    3. Project Architecture Deep-Dive (Resume projects & technologies)
    4. Internship & Work Experience (Trade-offs, debugging, production metrics)
    5. Aptitude, Logical & Verbal Reasoning
    6. Data Structures & Algorithms (DSA scenarios, complexities, edge cases)
    """
    llm = get_llm(temperature=0.3)

    track_directives = {
        "HR & Behavioral Fit": "Focus on culture fit, conflict resolution, leadership, deadline pressure, and STAR (Situation, Task, Action, Result) scenarios.",
        "Core CS & Software Engineering": "Probe computer science foundations: Operating Systems (concurrency, paging), DBMS (indexing, ACID, transactions), Computer Networks (TCP/IP, HTTP/3, DNS), OOP, and System Architecture.",
        "Project Architecture Deep-Dive": "Extract concrete systems and architectures claimed on the resume. Challenge technical choices, scale limits, and data bottlenecks.",
        "Internship & Work Experience": "Probe past engineering deliverables, real-world bug fixes, incident response, team collaboration, and quantifiable production impact.",
        "Aptitude & Verbal Reasoning": "Generate scenario-based logical deduction, analytical aptitude, quantitative estimation, or verbal precision challenges.",
        "Data Structures & Algorithms": "Present algorithmic design problems, time/space complexity optimization, data structure selection (Trees, Graphs, DP, Heaps), and edge conditions."
    }

    directive = track_directives.get(round_track, "Evaluate candidate competencies thoroughly.")

    prompt = f"""
You are a Principal Engineering Assessor and Talent Evaluation Director.

Track: {round_track}
Difficulty Tier: {difficulty} (Adjust technical depth and scenario complexity accordingly)
Target Language: {language}

Track Objectives:
{directive}

Candidate Resume:
\"\"\"{resume_text}\"\"\"

Target Job Description:
\"\"\"{jd_text}\"\"\"

Task:
Generate exactly {count} probing questions in {language}.
Return ONLY a valid JSON list of objects matching this schema:
[
  {{
    "id": 1,
    "question": "Question text here in {language}...",
    "focus_competency": "Specific skill or concept evaluated",
    "difficulty": "{difficulty}",
    "evaluation_criteria": "Key indicators of a senior vs. junior answer"
  }}
]
"""
    res = llm.invoke([
        SystemMessage(content="You are an expert technical interviewer and placement drive assessor. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])
    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned_json)
        return data if isinstance(data, list) else []
    except Exception:
        return [
            {
                "id": 1,
                "question": f"Explain the architectural trade-offs in your recent project and how you addressed scalability bottlenecks ({difficulty}).",
                "focus_competency": "System Design",
                "difficulty": difficulty,
                "evaluation_criteria": "Demonstrates clear understanding of trade-offs, caching, and database indexing."
            }
        ]


def evaluate_candidate_assessment_response(
    question: str,
    user_response: str,
    track: str,
    difficulty: str,
    jd_text: str,
    resume_text: str,
    language: str = "English"
) -> Dict[str, Any]:
    """
    Evaluates candidate text or transcribed audio answer, providing:
    - Score (0-100)
    - Structural Strengths & Identified Weaknesses
    - Senior-Level Ideal Answer
    - Specific Skill Gaps diagnosed from this answer
    - Target Google Search queries for instant prep resources
    """
    llm = get_llm(temperature=0.1)

    prompt = f"""
You are a Principal Engineering Assessor. Grade the candidate's response rigorously.

Question Track: {track} ({difficulty})
Assessment Language: {language}

Interview Question:
\"{question}\"

Candidate Response:
\"{user_response}\"

Context Job Description:
\"{jd_text}\"

Candidate Resume Reference:
\"{resume_text}\"

Evaluate on:
1. Technical Precision & Correctness
2. Depth & Architectural Trade-offs
3. Communication Clarity & Structure (e.g. STAR method for behavioral)

Return ONLY a valid JSON object matching this schema:
{{
  "score": 82,
  "verdict": "Exceptional / Strong / Needs Improvement / Critical Gap",
  "strengths": [
    "Specific strong point with rationale"
  ],
  "areas_for_improvement": [
    "Specific missing technical element or weak justification"
  ],
  "ideal_senior_response": "Full, authoritative, exemplary answer in {language} that demonstrates senior engineering competency.",
  "better_phrased_candidate_answer": "Rewritten version of the candidate's actual answer making it crisper, metric-backed, and impactful.",
  "diagnosed_skill_gaps": [
    "Specific missing framework, concept, or tool"
  ],
  "recommended_study_topics": [
    "Target study topic 1",
    "Target study topic 2"
  ],
  "recommended_search_queries": [
    "Search query 1 tutorial documentation",
    "Search query 2 best practices"
  ]
}}
"""
    res = llm.invoke([
        SystemMessage(content="You are a strict technical hiring assessor. Return valid JSON only."),
        HumanMessage(content=prompt)
    ])
    cleaned_json = res.content.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_json)
    except Exception:
        return {
            "score": 75,
            "verdict": "Solid Response",
            "strengths": ["Directly addressed the question prompt."],
            "areas_for_improvement": ["Include quantified benchmarks and failure modes."],
            "ideal_senior_response": "A senior engineer structures this by first stating architectural constraints, followed by trade-off analysis and metric verification.",
            "better_phrased_candidate_answer": user_response,
            "diagnosed_skill_gaps": ["Detailed system profiling"],
            "recommended_study_topics": ["High-throughput API tuning"],
            "recommended_search_queries": ["System architecture design patterns"]
        }

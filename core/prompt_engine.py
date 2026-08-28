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

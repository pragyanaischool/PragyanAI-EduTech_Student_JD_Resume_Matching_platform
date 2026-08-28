"""
Core business logic, parsers, prompt engines, and document utilities.
"""

from core.parsers import (
    parse_pdf,
    parse_docx,
    parse_url,
    extract_text_auto
)

from core.pdf_builder import generate_pdf_report

from core.prompt_engine import (
    get_llm,
    get_groq_api_key,
    build_markdown_resume,
    extract_resume_sections,
    update_resume_section,
    refine_resume_section,
    run_swot_analysis,
    match_cv_to_jd,
    match_jd_to_cv,
    optimize_ats_keywords,
    optimize_ats_resume,
    generate_cover_letter,
    generate_upskill_roadmap,
    generate_interview_questions,
    evaluate_interview_response,
    screen_candidate_logistics,
    answer_rag_query
)

__all__ = [
    "parse_pdf",
    "parse_docx",
    "parse_url",
    "extract_text_auto",
    "generate_pdf_report",
    "get_llm",
    "get_groq_api_key",
    "build_markdown_resume",
    "extract_resume_sections",
    "update_resume_section",
    "refine_resume_section",
    "run_swot_analysis",
    "match_cv_to_jd",
    "match_jd_to_cv",
    "optimize_ats_keywords",
    "optimize_ats_resume",
    "generate_cover_letter",
    "generate_upskill_roadmap",
    "generate_interview_questions",
    "evaluate_interview_response",
    "screen_candidate_logistics",
    "answer_rag_query",
]

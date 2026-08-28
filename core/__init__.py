"""Core processing engines, agent chains, parsers, RAG, and document tools."""

from core.audio_engine import generate_tts_audio, transcribe_audio
from core.parsers import (
    parse_pdf,
    parse_docx,
    parse_pptx,
    parse_url,
    parse_zip,
    extract_text_auto
)
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import (
    build_markdown_resume,
    match_cv_to_jd,
    optimize_ats_resume,
    generate_cover_letter,
    create_interview_questions,
    evaluate_interview_answer,
    generate_learning_roadmap,
    refine_resume_section,
    parse_and_structure_jd,
    evaluate_pre_screening
)
from core.rag_engine import rag_agent
from core.sample_data import SAMPLE_JDS, SAMPLE_RESUMES
from core.search_tools import fetch_web_certifications, fetch_youtube_lectures

__all__ = [
    "generate_tts_audio",
    "transcribe_audio",
    "parse_pdf",
    "parse_docx",
    "parse_pptx",
    "parse_url",
    "parse_zip",
    "extract_text_auto",
    "generate_pdf_report",
    "build_markdown_resume",
    "match_cv_to_jd",
    "optimize_ats_resume",
    "generate_cover_letter",
    "create_interview_questions",
    "evaluate_interview_answer",
    "generate_learning_roadmap",
    "refine_resume_section",
    "parse_and_structure_jd",
    "evaluate_pre_screening",
    "rag_agent",
    "SAMPLE_JDS",
    "SAMPLE_RESUMES",
    "fetch_web_certifications",
    "fetch_youtube_lectures",
]

"""
Core business logic, parsers, prompt engines, document utilities, audio engines, and search tools.
"""

from core.parsers import (
    parse_pdf,
    parse_docx,
    parse_url,
    extract_text_auto
)

from core.pdf_builder import (
    generate_pdf_report
)

from core.prompt_engine import (
    get_llm,
    get_groq_api_key,
    build_markdown_resume,
    extract_resume_sections,
    update_resume_section,
    refine_resume_section,
    match_cv_to_jd,
    match_jd_to_cv,
    evaluate_candidate_fit,
    run_swot_analysis,
    analyze_section_wise_match,
    auto_tailor_cv_for_jd,
    analyze_multi_jd_skill_gap,
    optimize_ats_keywords,
    optimize_ats_resume,
    generate_cover_letter,
    generate_upskill_roadmap,
    generate_interview_questions,
    generate_enterprise_job_description,
    evaluate_interview_response,
    screen_candidate_logistics,
    answer_rag_query
    
)

from core.audio_engine import (
    get_groq_client,
    text_to_speech_audio,
    generate_tts_audio,
    synthesize_speech,
    transcribe_audio_whisper,
    transcribe_audio,
    transcribe_voice
)

from core.search_tools import (
    search_ddgs_web,
    search_youtube_videos
)

__all__ = [
    # Parsers
    "parse_pdf",
    "parse_docx",
    "parse_url",
    "extract_text_auto",
    
    # PDF Builder
    "generate_pdf_report",
    
    # Prompt Engine & LLM Workflows
    "get_llm",
    "get_groq_api_key",
    "build_markdown_resume",
    "extract_resume_sections",
    "update_resume_section",
    "refine_resume_section",
    "match_cv_to_jd",
    "match_jd_to_cv",
    "evaluate_candidate_fit",
    "run_swot_analysis",
    "analyze_section_wise_match",
    "auto_tailor_cv_for_jd",
    "analyze_multi_jd_skill_gap",
    "optimize_ats_keywords",
    "optimize_ats_resume",
    "generate_cover_letter",
    "generate_upskill_roadmap",
    "generate_interview_questions",
    "generate_enterprise_job_description",
    "evaluate_interview_response",
    "screen_candidate_logistics",
    "answer_rag_query",
    
    # Audio Engine
    "get_groq_client",
    "text_to_speech_audio",
    "generate_tts_audio",
    "synthesize_speech",
    "transcribe_audio_whisper",
    "transcribe_audio",
    "transcribe_voice",
    
    # Search Tools
    "search_ddgs_web",
    "search_youtube_videos",
]


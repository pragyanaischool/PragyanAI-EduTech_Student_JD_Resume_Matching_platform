import pytest
from unittest.mock import patch, MagicMock
from core.rag_engine import RAGContextEngine


# ---------------------------------------------------------------------------
# Test Fixtures & Dummy Data
# ---------------------------------------------------------------------------

@pytest.fixture
def rag_engine_instance():
    """Initializes a clean RAGContextEngine instance."""
    return RAGContextEngine()


@pytest.fixture
def sample_resume_text():
    return """
Aarav Sharma | Bengaluru, India | aarav.sharma@domain.com
Executive Summary: Lead AI Engineer with 6.5 years of experience in LangChain, LangGraph, and Groq inference.
Technical Skills: Python, LangGraph, ChromaDB, FAISS, PyTorch, SQL, Docker.
Experience:
Senior Staff AI Specialist — Cognition Labs (2022 - Present)
- Engineered an autonomous recruiting agent using LangGraph and Groq, reducing initial screening turnaround times by 78%.
- Scaled local vector retrieval using FAISS and ChromaDB over 500,000+ technical profiles.
Education:
B.Tech in Computer Science, IIT Madras (2015 - 2019)
"""


@pytest.fixture
def sample_jd_text():
    return """
Job Title: Lead Generative AI Systems Engineer
Department: Autonomous Agent Systems
Experience Required: 5-8 Years | Compensation: $130,000 - $160,000
Core Requirements:
- Architect and deploy production multi-agent systems using LangChain and LangGraph.
- Optimize high-throughput LLM inferencing pipelines using Groq Cloud.
- Design low-latency semantic retrieval architectures integrating ChromaDB and FAISS.
"""


# ---------------------------------------------------------------------------
# Unit Tests: Chunking & Transient Vector Store
# ---------------------------------------------------------------------------

def test_transient_vectorstore_creation(rag_engine_instance, sample_resume_text):
    """Test text chunking and indexing in transient in-memory FAISS."""
    vstore = rag_engine_instance.build_transient_vectorstore(sample_resume_text, metadata_tag="test_resume")
    assert vstore is not None

    # Perform nearest neighbor search on the in-memory vector store
    results = vstore.similarity_search("LangGraph and Groq screening", k=2)
    assert len(results) > 0
    assert "LangGraph" in results[0].page_content
    assert results[0].metadata["source"] == "test_resume"


def test_transient_vectorstore_empty_input(rag_engine_instance):
    """Test vector store construction with empty string input."""
    vstore = rag_engine_instance.build_transient_vectorstore("", metadata_tag="empty")
    assert vstore is not None
    results = vstore.similarity_search("query", k=1)
    assert len(results) == 1
    assert results[0].page_content == "Empty document context."


# ---------------------------------------------------------------------------
# Unit Tests: RAG Queries & Grounding with Mocked Groq LLM
# ---------------------------------------------------------------------------

def test_query_context_empty_documents(rag_engine_instance):
    """Test RAG query when no primary or secondary context is supplied."""
    output = rag_engine_instance.query_context(
        query="What are the candidate's skills?",
        primary_context="",
        secondary_context="",
        context_type="resume_qa"
    )
    assert "No context documents provided" in output["answer"]
    assert output["sources"] == []


@patch("core.rag_engine.ChatGroq.invoke")
def test_query_context_resume_qa(mock_llm_invoke, rag_engine_instance, sample_resume_text):
    """Test resume Q&A mode retrieves relevant chunks and calls the LLM."""
    mock_response = MagicMock()
    mock_response.content = "Aarav Sharma has 6.5 years of experience specializing in LangGraph, Groq, and FAISS."
    mock_llm_invoke.return_value = mock_response

    output = rag_engine_instance.query_context(
        query="How many years of experience does the candidate have in AI?",
        primary_context=sample_resume_text,
        context_type="resume_qa",
        top_k=2
    )

    assert output["answer"] == mock_response.content
    assert len(output["sources"]) > 0
    assert any("Aarav Sharma" in src for src in output["sources"])
    mock_llm_invoke.assert_called_once()


@patch("core.rag_engine.ChatGroq.invoke")
def test_query_context_comparative_mode(mock_llm_invoke, rag_engine_instance, sample_resume_text, sample_jd_text):
    """Test comparative mode combines resume and JD context chunks."""
    mock_response = MagicMock()
    mock_response.content = "Match Score: 95%. The candidate satisfies all core requirements (LangGraph, Groq, FAISS)."
    mock_llm_invoke.return_value = mock_response

    output = rag_engine_instance.query_context(
        query="Compare the candidate's vector search background with the JD expectations.",
        primary_context=sample_resume_text,
        secondary_context=sample_jd_text,
        context_type="comparative",
        top_k=4
    )

    assert output["answer"] == mock_response.content
    assert len(output["sources"]) == 4

    # Verify that the LLM payload contains grounding passages from both documents
    call_args = mock_llm_invoke.call_args[0][0]
    human_message = call_args[1].content
    assert "Grounding Context Passages:" in human_message
    assert "Compare the candidate's vector search background" in human_message


@patch("core.rag_engine.ChatGroq.invoke")
def test_query_context_interview_copilot(mock_llm_invoke, rag_engine_instance, sample_resume_text, sample_jd_text):
    """Test interview copilot mode generates targeted questions."""
    mock_response = MagicMock()
    mock_response.content = """
1. Explain how you handled cyclical state transitions in your LangGraph screening bot.
2. How did you optimize memory usage when scaling FAISS to 500k profile vectors?
"""
    mock_llm_invoke.return_value = mock_response

    output = rag_engine_instance.query_context(
        query="Generate 2 technical interview questions probing the candidate's claims.",
        primary_context=sample_resume_text,
        secondary_context=sample_jd_text,
        context_type="interview_copilot",
        top_k=3
    )

    assert "LangGraph" in output["answer"]
    assert "FAISS" in output["answer"]
    assert len(output["sources"]) > 0

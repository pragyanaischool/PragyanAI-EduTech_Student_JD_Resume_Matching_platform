import streamlit as st
from typing import List, Dict, Any
from config.settings import settings
from database.sql_models import Resume, JobDescription, User
from database.sql_db import SessionLocal
from database.chroma_db import chroma
from core.prompt_engine import get_llm, answer_rag_query
from langchain_core.messages import SystemMessage, HumanMessage

# ==============================================================================
# Page Setup & Multi-Tenant Authorization Guard
# ==============================================================================
st.set_page_config(
    page_title="RAG Talent Intelligence Chat",
    layout="wide",
    page_icon="💬"
)

if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the RAG Talent Intelligence Assistant.")
    st.stop()

current_user = st.session_state.auth_user
user_role = current_user.get("role", "candidate")
user_email = current_user.get("email", "")

# Initialize Chat History
if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = [
        {
            "role": "assistant",
            "content": f"Hello {current_user.get('full_name') or user_email}! I am your grounded **RAG Talent Intelligence Assistant**. How can I help you query candidates, compare skills, or analyze job requirements today?",
            "sources": []
        }
    ]

# ==============================================================================
# Sidebar Scope Configuration & Knowledge Base Stats
# ==============================================================================
st.sidebar.markdown("### 🔍 RAG Retrieval Configuration")

# Context Collection Scope
if user_role in ["admin", "company"]:
    retrieval_scope = st.sidebar.radio(
        "Search Knowledge Base Scope:",
        ["All (Resumes + JDs)", "Candidate Resumes Only", "Job Descriptions Only"],
        index=0
    )
else:
    # Candidate view defaults to their domain
    retrieval_scope = st.sidebar.radio(
        "Search Knowledge Base Scope:",
        ["All (Resumes + JDs)", "Job Descriptions Only", "My Resume Profile"],
        index=0
    )

top_k = st.sidebar.slider("Top Relevant Chunks (Top-K):", min_value=1, max_value=8, value=4)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Indexed Knowledge Stats")

session = SessionLocal()
try:
    total_db_resumes = session.query(Resume).count()
    total_db_jds = session.query(JobDescription).count()
    st.sidebar.metric("Indexed Resumes", total_db_resumes)
    st.sidebar.metric("Indexed Job Descriptions", total_db_jds)
finally:
    session.close()

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state.rag_messages = [
        {
            "role": "assistant",
            "content": "Conversation history cleared. What talent intelligence query would you like to execute?",
            "sources": []
        }
    ]
    st.rerun()

# ==============================================================================
# Main Interface Header
# ==============================================================================
st.title("💬 Grounded RAG Talent Intelligence Chat")
st.caption(f"Authenticated Role: **{user_role.upper()}** | Model: **{getattr(settings, 'DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile')}** + **ChromaDB Vector Store**")

# Prompt suggestions for quick evaluation
st.markdown("**Quick Query Starters:**")
col_p1, col_p2, col_p3 = st.columns(3)

suggested_prompt = None
if user_role in ["admin", "company"]:
    if col_p1.button("🔍 Find Top LangGraph & Groq Engineers", use_container_width=True):
        suggested_prompt = "Which candidates have proven experience with LangGraph, Groq, and Vector DBMS? Summarize their top achievements."
    if col_p2.button("📊 Compare FastAPI Backend Candidates", use_container_width=True):
        suggested_prompt = "Compare candidates with FastAPI and PostgreSQL background in terms of latency optimization and testing."
    if col_p3.button("❓ Technical Interview Questions for JD #1", use_container_width=True):
        suggested_prompt = "Generate 4 probing interview questions for our Lead Generative AI Engineer job description based on candidate experience."
else:
    if col_p1.button("🎯 High-Paying Skills in Open JDs", use_container_width=True):
        suggested_prompt = "What are the most demanding technical requirements and frameworks across the indexed Job Descriptions?"
    if col_p2.button("💡 Compare My Fit vs. Lead AI Role", use_container_width=True):
        suggested_prompt = "How does Aarav Sharma's resume align with the Lead Generative AI Engineer role requirements?"
    if col_p3.button("🛠️ Cloud & MLOps Skill Gaps", use_container_width=True):
        suggested_prompt = "What specific Kubernetes and Triton Inference skills are required in Staff MLOps roles?"

# ==============================================================================
# Helper Function: Multi-Collection RAG Context Retrieval
# ==============================================================================
def retrieve_grounded_context(query_str: str, scope: str, k: int) -> List[Dict[str, Any]]:
    """
    Queries ChromaDB collections (resumes and/or JDs) and returns formatted chunk documents.
    """
    retrieved_chunks = []

    # 1. Query Resumes
    if scope in ["All (Resumes + JDs)", "Candidate Resumes Only", "My Resume Profile"]:
        try:
            resume_results = chroma.query_resumes(query_str, n_results=k)
            docs = resume_results.get("documents", [[]])[0]
            metas = resume_results.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metas):
                retrieved_chunks.append({
                    "content": doc,
                    "source": f"Resume: {meta.get('filename') or meta.get('candidate_name', 'Candidate Doc')}",
                    "type": "Resume",
                    "meta": meta
                })
        except Exception:
            pass

    # 2. Query JDs
    if scope in ["All (Resumes + JDs)", "Job Descriptions Only"]:
        try:
            jd_results = chroma.query_jds(query_str, n_results=k)
            docs = jd_results.get("documents", [[]])[0]
            metas = jd_results.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metas):
                retrieved_chunks.append({
                    "content": doc,
                    "source": f"Job Spec: {meta.get('title', 'Target Role')}",
                    "type": "Job Description",
                    "meta": meta
                })
        except Exception:
            pass

    # Sort or slice to top-k
    return retrieved_chunks[:k]


# ==============================================================================
# Render Chat History
# ==============================================================================
for msg in st.session_state.rag_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📚 Verified Context Sources ({len(msg['sources'])} chunks)"):
                for idx, src in enumerate(msg["sources"], start=1):
                    st.markdown(f"**Source #{idx}: `{src.get('source')}`**")
                    st.caption(src.get("content", "")[:350] + "...")

# ==============================================================================
# User Input Processing Loop
# ==============================================================================
chat_input_val = st.chat_input("Ask any candidate qualification, JD comparison, or skill evaluation question...")
active_prompt = suggested_prompt or chat_input_val

if active_prompt:
    # 1. Render User Message
    st.session_state.rag_messages.append({"role": "user", "content": active_prompt, "sources": []})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    # 2. Retrieve Grounded Context from Vector Store
    with st.chat_message("assistant"):
        with st.spinner("Searching ChromaDB semantic vector embeddings & synthesizing response..."):
            retrieved_sources = retrieve_grounded_context(active_prompt, retrieval_scope, top_k)
            context_blocks = [s["content"] for s in retrieved_sources]

            # 3. Synthesize Grounded RAG Answer via Groq
            if not context_blocks:
                # Direct LLM fallback if vector store has no indexed documents
                llm = get_llm(temperature=0.2)
                fallback_resp = llm.invoke([
                    SystemMessage(content="You are a helpful recruitment and talent intelligence assistant."),
                    HumanMessage(content=active_prompt)
                ]).content.strip()
                answer_text = fallback_resp
            else:
                answer_text = answer_rag_query(active_prompt, context_blocks)

            # Render response
            st.markdown(answer_text)

            if retrieved_sources:
                with st.expander(f"📚 Verified Context Sources ({len(retrieved_sources)} chunks)"):
                    for idx, src in enumerate(retrieved_sources, start=1):
                        st.markdown(f"**Source #{idx}: `{src.get('source')}`**")
                        st.caption(src.get("content", "")[:350] + "...")

    # 4. Append Assistant Response to Session History
    st.session_state.rag_messages.append({
        "role": "assistant",
        "content": answer_text,
        "sources": retrieved_sources
    })
    

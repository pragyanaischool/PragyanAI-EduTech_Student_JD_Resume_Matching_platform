import streamlit as st
import json
import pandas as pd
from database.sql_db import sql_db
from database.sql_models import JobDescription, Resume
from core.rag_engine import rag_agent
from core.sample_data import SAMPLE_JDS, SAMPLE_RESUMES

st.set_page_config(page_title="RAG Talent Intelligence Chat", layout="wide", page_icon="💬")

# Session Authorization Guard
if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the RAG Talent Chat.")
    st.stop()

# Initialize Chat Memory per mode
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {
        "resume_qa": [],
        "jd_qa": [],
        "comparative": [],
        "interview_copilot": []
    }

session = sql_db.get_session()

# Fetch Dynamic Records from SQL with Sample Data Fallbacks
db_jds = session.query(JobDescription).all()
db_resumes = session.query(Resume).all()

jd_options = {jd.title: jd.content for jd in db_jds} if db_jds else {j["title"]: j["content"] for j in SAMPLE_JDS}
resume_options = {r.filename: r.raw_content for r in db_resumes} if db_resumes else {r["filename"]: r["raw_content"] for r in SAMPLE_RESUMES}

st.title("RAG Talent Intelligence & Interactive Chat")
st.caption("Interact directly with candidate resumes, job descriptions, and deep SWOT diagnostics using grounded LangChain RAG & Groq inference.")

# ----------------- SIDEBAR CONTEXT CONTROLS -----------------
with st.sidebar:
    st.header("Chat Context Configuration")
    
    chat_mode = st.selectbox(
        "Select Conversational Mode:",
        [
            ("resume_qa", "1. Query Candidate Resume"),
            ("jd_qa", "2. Explore Job Requirements"),
            ("comparative", "3. Resume vs. JD Fit Analysis"),
            ("interview_copilot", "4. AI Interviewer Copilot")
        ],
        format_func=lambda x: x[1]
    )[0]
    
    st.divider()
    
    selected_resume_key = None
    selected_jd_key = None
    
    if chat_mode in ["resume_qa", "comparative", "interview_copilot"]:
        selected_resume_key = st.selectbox("Select Candidate Resume:", list(resume_options.keys()))
        
    if chat_mode in ["jd_qa", "comparative", "interview_copilot"]:
        selected_jd_key = st.selectbox("Select Job Description:", list(jd_options.keys()))
        
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.chat_history[chat_mode] = []
        st.rerun()

# ----------------- MAIN INTERFACE -----------------
active_resume_text = resume_options.get(selected_resume_key, "") if selected_resume_key else ""
active_jd_text = jd_options.get(selected_jd_key, "") if selected_jd_key else ""

# Document Viewer Drawers
with st.expander("Inspect Active Context Documents"):
    c1, c2 = st.columns(2)
    with c1:
        if active_resume_text:
            st.markdown(f"**Candidate Document (`{selected_resume_key}`):**")
            st.text_area("Resume Content", value=active_resume_text, height=200, disabled=True)
        else:
            st.info("No candidate document selected.")
    with c2:
        if active_jd_text:
            st.markdown(f"**Job Description (`{selected_jd_key}`):**")
            st.text_area("JD Content", value=active_jd_text, height=200, disabled=True)
        else:
            st.info("No JD document selected.")

st.divider()

# Suggested Starter Prompts
preset_prompts = {
    "resume_qa": [
        "What are this candidate's core architectural accomplishments?",
        "Has the candidate worked with LangGraph or Groq in production?",
        "Summarize the candidate's experience with local vector search databases."
    ],
    "jd_qa": [
        "What are the non-negotiable technical requirements for this role?",
        "What is the expected compensation and seniority band?",
        "List all vector databases and ML deployment tools mentioned."
    ],
    "comparative": [
        "Does the candidate satisfy the 5+ years requirement in GenAI?",
        "Perform a comprehensive gap analysis between this resume and the JD.",
        "Highlight the candidate's top 3 weaknesses relative to this position."
    ],
    "interview_copilot": [
        "Generate 3 difficult technical scenario questions probing the candidate's LangGraph claims.",
        "What follow-up questions should we ask regarding their FAISS optimization project?",
        "Design a 15-minute system design prompt tailored to this candidate."
    ]
}

st.markdown("##### Suggested Quick Queries:")
col_p1, col_p2, col_p3 = st.columns(3)
selected_prompt = None

if col_p1.button(preset_prompts[chat_mode][0], use_container_width=True):
    selected_prompt = preset_prompts[chat_mode][0]
if col_p2.button(preset_prompts[chat_mode][1], use_container_width=True):
    selected_prompt = preset_prompts[chat_mode][1]
if col_p3.button(preset_prompts[chat_mode][2], use_container_width=True):
    selected_prompt = preset_prompts[chat_mode][2]

# Display Existing Chat Messages
for msg in st.session_state.chat_history[chat_mode]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("Retrieved Context Chunks (Grounding Evidence)"):
                for idx, src in enumerate(msg["sources"]):
                    st.markdown(f"**Chunk {idx+1}:**\n> {src.strip()}")

# Capture User Query
user_query = st.chat_input("Ask a grounded question about the selected context...")
if selected_prompt:
    user_query = selected_prompt

if user_query:
    # 1. Render User Message
    st.session_state.chat_history[chat_mode].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Execute RAG Retrieval & Inference
    with st.chat_message("assistant"):
        with st.spinner("Retrieving semantic passages and inferencing via Groq..."):
            rag_output = rag_agent.query_context(
                query=user_query,
                primary_context=active_resume_text if chat_mode != "jd_qa" else active_jd_text,
                secondary_context=active_jd_text if chat_mode in ["comparative", "interview_copilot"] else "",
                context_type=chat_mode,
                top_k=4
            )
            
            answer_text = rag_output["answer"]
            sources = rag_output["sources"]
            
            st.markdown(answer_text)
            if sources:
                with st.expander("Retrieved Context Chunks (Grounding Evidence)"):
                    for idx, src in enumerate(sources):
                        st.markdown(f"**Chunk {idx+1}:**\n> {src.strip()}")

    # 3. Save to History
    st.session_state.chat_history[chat_mode].append({
        "role": "assistant",
        "content": answer_text,
        "sources": sources
    })

session.close()

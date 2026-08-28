from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings


class RAGContextEngine:
    """
    Retrieval-Augmented Generation engine supporting transient, multi-context 
    grounding across resumes, JDs, comparative evaluations, and interview scenarios.
    """

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
        self.llm = ChatGroq(
            model=settings.DEFAULT_LLM_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.1
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def build_transient_vectorstore(self, text: str, metadata_tag: str = "doc") -> FAISS:
        """Splits raw text into overlapping chunks and indexes into a memory-resident FAISS vector store."""
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            chunks = ["Empty document context."]
        metadatas = [{"source": metadata_tag, "chunk_id": i} for i in range(len(chunks))]
        return FAISS.from_texts(texts=chunks, embedding=self.embeddings, metadatas=metadatas)

    def query_context(
        self,
        query: str,
        primary_context: str,
        secondary_context: str = "",
        context_type: str = "general",
        top_k: int = settings.RAG_TOP_K
    ) -> Dict[str, Any]:
        """
        Retrieves top-k semantically relevant chunks from primary/secondary documents 
        and generates a grounded answer with cited context passages.
        """
        combined_text = f"{primary_context}\n\n{secondary_context}".strip()
        if not combined_text:
            return {
                "answer": "No context documents provided. Please select or upload a resume or job description.",
                "sources": []
            }

        # Build in-memory FAISS index
        vstore = self.build_transient_vectorstore(combined_text, metadata_tag=context_type)
        retrieved_docs = vstore.similarity_search(query, k=top_k)
        retrieved_passages = "\n---\n".join([f"[Passage {i+1}]: {doc.page_content}" for i, doc in enumerate(retrieved_docs)])

        system_prompts = {
            "resume_qa": (
                "You are an expert Technical Recruiter and Career Auditor. Answer the query strictly "
                "using the provided resume passages. If information is absent, state clearly that it is not documented. "
                "Do not hallucinate facts."
            ),
            "jd_qa": (
                "You are a Lead Hiring Manager. Explain the job expectations, seniority requirements, "
                "and architectural responsibilities based strictly on the provided Job Description passages."
            ),
            "comparative": (
                "You are an executive Talent Acquisition Strategist. Compare the candidate's verified skills against "
                "the job requirements. Cite exact matches, discrepancies, and critical gaps."
            ),
            "interview_copilot": (
                "You are an AI Technical Interviewer Copilot. Based on the candidate's resume and job context, "
                "generate challenging follow-up questions, architecture scenarios, and grading criteria."
            )
        }

        selected_prompt = system_prompts.get(context_type, system_prompts["resume_qa"])

        prompt_payload = f"""
Grounding Context Passages:
{retrieved_passages}

Candidate / JD Query:
{query}

Provide a direct, grounded, highly structured response:
"""

        response = self.llm.invoke([
            SystemMessage(content=selected_prompt),
            HumanMessage(content=prompt_payload)
        ])

        return {
            "answer": response.content.strip(),
            "sources": [doc.page_content for doc in retrieved_docs]
        }


# Global singleton instance
rag_agent = RAGContextEngine()

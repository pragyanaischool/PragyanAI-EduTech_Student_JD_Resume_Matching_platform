import os
from pathlib import Path
import streamlit as st
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_api_key() -> str:
    """Reads GROQ_API_KEY from st.secrets, environment, or .env."""
    # 1. Check Streamlit secrets first
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass

    # 2. Check standard environment variables
    return os.getenv("GROQ_API_KEY", "").strip()


class AppSettings(BaseSettings):
    """Application-wide settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Groq API Key dynamically loaded from st.secrets
    GROQ_API_KEY: str = Field(default_factory=get_api_key)

    DEFAULT_LLM_MODEL: str = "openai/gpt-oss-120b"
    FAST_LLM_MODEL: str = "openai/gpt-oss-20b"
    WHISPER_MODEL: str = "whisper-large-v3-turbo"

    DATABASE_URL: str = "sqlite:///recruitment_platform.db"
    CHROMA_PERSIST_DIR: str = "./chroma_store"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 80
    RAG_TOP_K: int = 4


settings = AppSettings()

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-wide settings and environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # LLM Inference (Groq Cloud API)
    GROQ_API_KEY: str = Field(
        default="",
        description="Groq Cloud API Key for ultra-low latency LLM and Whisper inference"
    )
    DEFAULT_LLM_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Primary LLM used for parsing, SWOT analysis, and roadmaps"
    )
    FAST_LLM_MODEL: str = Field(
        default="llama-3.1-8b-instant",
        description="Lightweight LLM for quick classifications and pre-screening"
    )
    WHISPER_MODEL: str = Field(
        default="whisper-large-v3-turbo",
        description="Groq Whisper model for audio mock interview transcription"
    )

    # Relational Database (SQLAlchemy Engine)
    # Default is a local zero-setup SQLite file. 
    # For PostgreSQL: "postgresql+psycopg2://user:password@localhost:5432/recruitment_db"
    DATABASE_URL: str = Field(
        default="sqlite:///recruitment_platform.db",
        description="SQLAlchemy database connection URI (SQLite or PostgreSQL)"
    )

    # Vector Database & Embeddings
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_store",
        description="Directory path for local persistent ChromaDB vector store"
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model for dense semantic embeddings"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        description="Dimension size of the selected embedding model"
    )

    # RAG Search & Chunking Strategy
    RAG_CHUNK_SIZE: int = Field(
        default=500,
        description="Character chunk size for recursive text splitting"
    )
    RAG_CHUNK_OVERLAP: int = Field(
        default=80,
        description="Character chunk overlap for text splitting"
    )
    RAG_TOP_K: int = Field(
        default=4,
        description="Default number of nearest neighbor context chunks to retrieve"
    )

    # Application Behavior & Security
    APP_SECRET_KEY: str = Field(
        default="super-secret-pragyan-ai-key-2026",
        description="Secret key for signing and hashing"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Application logging verbosity (DEBUG, INFO, WARNING, ERROR)"
    )


# Instantiate global settings singleton
settings = AppSettings()

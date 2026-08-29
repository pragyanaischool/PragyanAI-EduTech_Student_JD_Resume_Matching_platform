import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional


class ChromaVectorStore:
    """
    Manages vector storage and similarity retrieval for Resumes and Job Descriptions.
    Supports persistent disk storage and in-memory fallback.
    """

    def __init__(self, persist_dir: str = "./data/chroma_db"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)

        try:
            # Persistent Local Client
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
        except Exception:
            # Fallback to Ephemeral In-Memory Client if disk permissions fail
            self.client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

        # Initialize Collections
        self._init_collections()

    def _init_collections(self):
        """Initializes collections and binds aliases to prevent attribute mismatch errors."""
        try:
            self._resumes = self.client.get_or_create_collection(
                name="resumes_collection",
                metadata={"hnsw:space": "cosine"}
            )
            self._jds = self.client.get_or_create_collection(
                name="jds_collection",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            self._resumes = self.client.create_collection(
                name="resumes_collection",
                metadata={"hnsw:space": "cosine"}
            )
            self._jds = self.client.create_collection(
                name="jds_collection",
                metadata={"hnsw:space": "cosine"}
            )

        # Aliases for cross-file compatibility
        self.resumes_collection = self._resumes
        self.resume_collection = self._resumes
        self.jds_collection = self._jds
        self.jd_collection = self._jds
        self.jobs_collection = self._jds

    # ==========================================================================
    # Job Description Vector Operations
    # ==========================================================================
    def upsert_jd(
        self,
        doc_id: Optional[str] = None,
        text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Upserts job description text and metadata into ChromaDB vector store.
        Accepts doc_id, jd_id, or id.
        """
        final_id = doc_id or kwargs.get("jd_id") or kwargs.get("id") or "jd_unknown"
        if not metadata:
            metadata = {}

        if not text or not text.strip():
            return

        # Sanitize metadata to primitive types (strings, ints, floats, bools)
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[str(k)] = v
            elif v is None:
                clean_metadata[str(k)] = ""
            else:
                clean_metadata[str(k)] = str(v)

        target_collection = getattr(self, "jds_collection", None) or getattr(self, "jd_collection", None)
        if target_collection is None:
            self._init_collections()
            target_collection = self.jds_collection

        target_collection.upsert(
            ids=[str(final_id)],
            documents=[text.strip()],
            metadatas=[clean_metadata]
        )

    def query_jds(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries indexed job descriptions by semantic similarity."""
        if not query_text or not query_text.strip():
            return []

        target_collection = getattr(self, "jds_collection", None) or getattr(self, "jd_collection", None)
        if target_collection is None:
            self._init_collections()
            target_collection = self.jds_collection

        try:
            results = target_collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            parsed = []
            if results and results.get("ids") and results["ids"][0]:
                for idx in range(len(results["ids"][0])):
                    parsed.append({
                        "id": results["ids"][0][idx],
                        "document": results["documents"][0][idx] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][idx] if results.get("metadatas") else {},
                        "distance": results["distances"][0][idx] if results.get("distances") else None
                    })
            return parsed
        except Exception:
            return []

    # ==========================================================================
    # Resume Vector Operations
    # ==========================================================================
    def upsert_resume(
        self,
        doc_id: Optional[str] = None,
        text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Upserts candidate resume text and metadata into ChromaDB vector store.
        Accepts doc_id, resume_id, or id.
        """
        final_id = doc_id or kwargs.get("resume_id") or kwargs.get("id") or "resume_unknown"
        if not metadata:
            metadata = {}

        if not text or not text.strip():
            return

        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[str(k)] = v
            elif v is None:
                clean_metadata[str(k)] = ""
            else:
                clean_metadata[str(k)] = str(v)

        target_collection = getattr(self, "resumes_collection", None) or getattr(self, "resume_collection", None)
        if target_collection is None:
            self._init_collections()
            target_collection = self.resumes_collection

        target_collection.upsert(
            ids=[str(final_id)],
            documents=[text.strip()],
            metadatas=[clean_metadata]
        )

    def query_resumes(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries indexed candidate resumes by semantic similarity."""
        if not query_text or not query_text.strip():
            return []

        target_collection = getattr(self, "resumes_collection", None) or getattr(self, "resume_collection", None)
        if target_collection is None:
            self._init_collections()
            target_collection = self.resumes_collection

        try:
            results = target_collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            parsed = []
            if results and results.get("ids") and results["ids"][0]:
                for idx in range(len(results["ids"][0])):
                    parsed.append({
                        "id": results["ids"][0][idx],
                        "document": results["documents"][0][idx] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][idx] if results.get("metadatas") else {},
                        "distance": results["distances"][0][idx] if results.get("distances") else None
                    })
            return parsed
        except Exception:
            return []


# Global Singleton Instance
chroma = ChromaVectorStore()

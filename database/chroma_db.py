import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from config.settings import settings


class ChromaVectorStore:
    """Persistent local vector database leveraging ChromaDB and HuggingFace SentenceTransformers."""

    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        
        self.resumes_col = self.client.get_or_create_collection(
            name="resumes_collection",
            embedding_function=self.embedding_fn
        )
        
        self.jds_col = self.client.get_or_create_collection(
            name="jds_collection",
            embedding_function=self.embedding_fn
        )

    def upsert_resume(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Indexes or updates a candidate resume embedding with associated metadata."""
        if not text.strip():
            return
        # Ensure metadata values are valid JSON primitives for Chroma
        clean_metadata = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in metadata.items()}
        self.resumes_col.upsert(
            ids=[str(doc_id)],
            documents=[text],
            metadatas=[clean_metadata]
        )

    def upsert_jd(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Indexes or updates a job description embedding."""
        if not text.strip():
            return
        clean_metadata = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in metadata.items()}
        self.jds_col.upsert(
            ids=[str(doc_id)],
            documents=[text],
            metadatas=[clean_metadata]
        )

    def query_resumes(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries resumes by semantic similarity."""
        if not query_text.strip():
            return []
        
        count = self.resumes_col.count()
        if count == 0:
            return []
            
        limit = min(n_results, count)
        results = self.resumes_col.query(
            query_texts=[query_text],
            n_results=limit
        )
        
        formatted = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                })
        return formatted

    def query_jds(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries job descriptions by semantic similarity."""
        if not query_text.strip():
            return []
        
        count = self.jds_col.count()
        if count == 0:
            return []
            
        limit = min(n_results, count)
        results = self.jds_col.query(
            query_texts=[query_text],
            n_results=limit
        )
        
        formatted = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                })
        return formatted

    def clear_all(self):
        """Wipes all vector collections."""
        self.client.delete_collection("resumes_collection")
        self.client.delete_collection("jds_collection")
        self.resumes_col = self.client.get_or_create_collection("resumes_collection", embedding_function=self.embedding_fn)
        self.jds_col = self.client.get_or_create_collection("jds_collection", embedding_function=self.embedding_fn)


# Global vector store instance
chroma = ChromaVectorStore()

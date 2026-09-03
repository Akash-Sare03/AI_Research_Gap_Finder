from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import os
from pathlib import Path
from ..core.config import Config
from ..core.embeddings import EmbeddingService

class ChromaStore:
    """Vector database for storing document chunks using Chroma DB."""
    
    def __init__(self):
        self.persist_dir = Config.VECTOR_DB_PATH
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        self.collection_name = "research_papers"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add or upsert chunks in the vector store."""
        ids = [chunk["id"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        return ids
    
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        chunks = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                chunks.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        
        return chunks
    
    def search_with_filter(self, query_embedding: List[float], 
                          filter_dict: Dict[str, Any], 
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Search with metadata filtering."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"]
        )
        
        chunks = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                chunks.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        
        return chunks
    
    def delete_paper(self, paper_id: str, user_id: Optional[str] = None):
        """Delete all chunks from a paper, optionally scoped to user_id."""
        try:
            if user_id and user_id != "guest":
                self.collection.delete(
                    where={"$and": [{"paper_id": paper_id}, {"user_id": user_id}]}
                )
            else:
                self.collection.delete(
                    where={"paper_id": paper_id}
                )
        except Exception:
            try:
                self.collection.delete(
                    where={"paper_id": paper_id}
                )
            except Exception as e:
                print(f"Notice deleting paper {paper_id}: {e}")
    
    def get_paper_ids(self) -> List[str]:
        """Get all paper IDs in the store."""
        try:
            results = self.collection.get(
                include=["metadatas"]
            )
            paper_ids = set()
            if results and results.get("metadatas"):
                for metadata in results["metadatas"]:
                    if metadata and "paper_id" in metadata:
                        paper_ids.add(metadata["paper_id"])
            return list(paper_ids)
        except Exception:
            return []
    
    def get_all_papers_metadata(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get distinct papers with full metadata and chunk counts scoped strictly to user_id."""
        try:
            results = self.collection.get(
                include=["metadatas"]
            )
            papers_map = {}
            if results and results.get("metadatas"):
                for metadata in results["metadatas"]:
                    if not metadata or "paper_id" not in metadata:
                        continue
                    
                    paper_user = metadata.get("user_id")
                    p_user_clean = (paper_user or "").strip().lower()
                    u_clean = (user_id or "").strip().lower()
                    
                    # STRICT USER WORKSPACE ISOLATION:
                    if user_id and user_id != "guest":
                        # Logged in user: ONLY see papers uploaded by this exact user
                        if p_user_clean != u_clean:
                            continue
                    else:
                        # Guest mode: ONLY see papers uploaded as guest or public sample papers
                        if p_user_clean and p_user_clean not in ["guest", "global", "default_user", ""]:
                            continue
                    
                    pid = metadata["paper_id"]
                    if pid not in papers_map:
                        papers_map[pid] = {
                            "paper_id": pid,
                            "file_name": metadata.get("file_name", f"{pid}.pdf"),
                            "title": metadata.get("title") or pid,
                            "authors": metadata.get("authors", ""),
                            "year": metadata.get("year", ""),
                            "total_pages": metadata.get("total_pages", 1),
                            "file_hash": metadata.get("file_hash", ""),
                            "chunk_count": 0,
                            "user_id": paper_user or "global",
                            "indexed_at": metadata.get("indexed_at", "")
                        }
                    papers_map[pid]["chunk_count"] += 1
            return list(papers_map.values())
        except Exception as e:
            print(f"Error getting papers metadata: {e}")
            return []

    def get_all_papers(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for get_all_papers_metadata."""
        return self.get_all_papers_metadata(user_id=user_id)

    def find_paper_by_hash(self, file_hash: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find if a paper with the given SHA-256 hash exists in the collection for this user."""
        if not file_hash:
            return None
        try:
            results = self.collection.get(
                where={"file_hash": file_hash},
                include=["metadatas"]
            )
            if results and results.get("ids") and len(results["ids"]) > 0:
                for meta in results["metadatas"]:
                    paper_user = meta.get("user_id")
                    p_user_clean = (paper_user or "").strip().lower()
                    u_clean = (user_id or "").strip().lower()
                    if user_id and user_id != "guest":
                        if p_user_clean == u_clean:
                            return {
                                "paper_id": meta.get("paper_id"),
                                "file_name": meta.get("file_name"),
                                "title": meta.get("title"),
                                "file_hash": file_hash,
                                "chunk_count": len(results["ids"]),
                                "user_id": paper_user
                            }
                    else:
                        if p_user_clean in ["guest", "global", "default_user", ""]:
                            return {
                                "paper_id": meta.get("paper_id"),
                                "file_name": meta.get("file_name"),
                                "title": meta.get("title"),
                                "file_hash": file_hash,
                                "chunk_count": len(results["ids"]),
                                "user_id": paper_user
                            }
        except Exception:
            pass
        return None
    
    def count_chunks(self) -> int:
        """Get total number of chunks."""
        try:
            return self.collection.count()
        except Exception:
            return 0
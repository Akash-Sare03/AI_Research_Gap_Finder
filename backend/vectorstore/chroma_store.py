from typing import List, Dict, Any, Optional
import os
import json
import sqlite3
from pathlib import Path
from ..core.config import Config


class LightweightCollection:
    """Emulates ChromaDB Collection interface for serverless / zero-C++ environments."""
    def __init__(self, store):
        self.store = store

    def get(self, where: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, include: Optional[List[str]] = None):
        return self.store._collection_get(where=where, limit=limit, include=include)

    def count(self) -> int:
        return self.store.count_chunks()

    def delete(self, where: Optional[Dict[str, Any]] = None):
        return self.store._collection_delete(where=where)

    def upsert(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
        chunks = []
        for i in range(len(ids)):
            chunks.append({
                "id": ids[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i],
                "text": documents[i]
            })
        return self.store.add_chunks(chunks)

    def query(self, query_embeddings: List[List[float]], n_results: int = 10, where: Optional[Dict[str, Any]] = None, include: Optional[List[str]] = None):
        q_emb = query_embeddings[0] if query_embeddings else []
        if where:
            chunks = self.store.search_with_filter(q_emb, where, top_k=n_results)
        else:
            chunks = self.store.search(q_emb, top_k=n_results)
        return {
            "ids": [[c["id"] for c in chunks]],
            "documents": [[c["text"] for c in chunks]],
            "metadatas": [[c["metadata"] for c in chunks]],
            "distances": [[c["distance"] for c in chunks]]
        }


class LightweightVectorStore:
    """Pure-Python SQLite vector store designed for serverless environments (e.g. Vercel).
    Requires zero C++ compilation and zero heavy dependencies."""
    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.db_path = os.path.join(self.persist_dir, "lightweight_store.db")
        self._init_db()
        self.collection = LightweightCollection(self)

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    paper_id TEXT,
                    user_id TEXT,
                    file_hash TEXT,
                    document TEXT,
                    metadata_json TEXT,
                    embedding_json TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_paper ON chunks(paper_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON chunks(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON chunks(file_hash)")

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        ids = []
        with self._get_conn() as conn:
            for ch in chunks:
                cid = ch["id"]
                meta = ch.get("metadata", {})
                pid = meta.get("paper_id", "")
                uid = meta.get("user_id", "guest")
                fhash = meta.get("file_hash", "")
                doc = ch.get("text", "")
                emb = ch.get("embedding", [])
                conn.execute(
                    "INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (cid, pid, uid, fhash, doc, json.dumps(meta), json.dumps(emb))
                )
                ids.append(cid)
        return ids

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        return self.search_with_filter(query_embedding, filter_dict=None, top_k=top_k)

    def search_with_filter(self, query_embedding: List[float], filter_dict: Optional[Dict[str, Any]] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if filter_dict and "paper_id" in filter_dict:
                cur.execute("SELECT id, document, metadata_json, embedding_json FROM chunks WHERE paper_id = ?", (filter_dict["paper_id"],))
            else:
                cur.execute("SELECT id, document, metadata_json, embedding_json FROM chunks")
            rows = cur.fetchall()

        scored = []
        for row in rows:
            cid, doc, meta_str, emb_str = row
            try:
                emb = json.loads(emb_str)
                dot = sum(a * b for a, b in zip(query_embedding, emb))
                dist = max(0.0, 1.0 - dot)
            except Exception:
                dist = 1.0

            scored.append({
                "id": cid,
                "text": doc,
                "metadata": json.loads(meta_str) if meta_str else {},
                "distance": dist
            })

        scored.sort(key=lambda x: x["distance"])
        return scored[:top_k]

    def delete_paper(self, paper_id: str, user_id: Optional[str] = None):
        with self._get_conn() as conn:
            if user_id and user_id != "guest":
                conn.execute("DELETE FROM chunks WHERE paper_id = ? AND user_id = ?", (paper_id, user_id))
            else:
                conn.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))

    def get_paper_ids(self) -> List[str]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT paper_id FROM chunks WHERE paper_id IS NOT NULL AND paper_id != ''")
            return [r[0] for r in cur.fetchall()]

    def get_all_papers_metadata(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT metadata_json FROM chunks")
            rows = cur.fetchall()

        papers_map = {}
        for row in rows:
            if not row[0]:
                continue
            meta = json.loads(row[0])
            pid = meta.get("paper_id")
            if not pid:
                continue

            paper_user = meta.get("user_id")
            p_user_clean = (paper_user or "").strip().lower()
            u_clean = (user_id or "").strip().lower()

            if user_id and user_id != "guest":
                if p_user_clean != u_clean:
                    continue
            else:
                if p_user_clean and p_user_clean not in ["guest", "global", "default_user", ""]:
                    continue

            if pid not in papers_map:
                papers_map[pid] = {
                    "paper_id": pid,
                    "file_name": meta.get("file_name", f"{pid}.pdf"),
                    "title": meta.get("title") or pid,
                    "authors": meta.get("authors", ""),
                    "year": meta.get("year", ""),
                    "total_pages": meta.get("total_pages", 1),
                    "file_hash": meta.get("file_hash", ""),
                    "chunk_count": 0,
                    "user_id": paper_user or "global",
                    "indexed_at": meta.get("indexed_at", "")
                }
            papers_map[pid]["chunk_count"] += 1

        return list(papers_map.values())

    def get_all_papers(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.get_all_papers_metadata(user_id=user_id)

    def find_paper_by_hash(self, file_hash: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT metadata_json FROM chunks WHERE file_hash = ?", (file_hash,))
            rows = cur.fetchall()

        if rows:
            for row in rows:
                meta = json.loads(row[0])
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
                            "chunk_count": len(rows),
                            "user_id": paper_user
                        }
                else:
                    if p_user_clean in ["guest", "global", "default_user", ""]:
                        return {
                            "paper_id": meta.get("paper_id"),
                            "file_name": meta.get("file_name"),
                            "title": meta.get("title"),
                            "file_hash": file_hash,
                            "chunk_count": len(rows),
                            "user_id": paper_user
                        }
        return None

    def count_chunks(self) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM chunks")
            return cur.fetchone()[0]

    def _collection_get(self, where: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, include: Optional[List[str]] = None):
        sql = "SELECT id, document, metadata_json FROM chunks"
        params = []
        if where:
            clauses = []
            if "paper_id" in where:
                clauses.append("paper_id = ?")
                params.append(where["paper_id"])
            if "file_hash" in where:
                clauses.append("file_hash = ?")
                params.append(where["file_hash"])
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
        if limit:
            sql += f" LIMIT {int(limit)}"

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

        ids = [r[0] for r in rows]
        docs = [r[1] for r in rows]
        metas = [json.loads(r[2]) if r[2] else {} for r in rows]
        return {
            "ids": ids,
            "documents": docs,
            "metadatas": metas
        }

    def _collection_delete(self, where: Optional[Dict[str, Any]] = None):
        if not where:
            return
        sql = "DELETE FROM chunks"
        params = []
        clauses = []
        if "paper_id" in where:
            clauses.append("paper_id = ?")
            params.append(where["paper_id"])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
            with self._get_conn() as conn:
                conn.execute(sql, tuple(params))


class ChromaStore:
    """Vector database for storing document chunks using Chroma DB with automatic lightweight fallback."""
    
    def __init__(self):
        self.persist_dir = Config.VECTOR_DB_PATH
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._fallback = None
        self._is_lightweight = False

        try:
            import chromadb
            from chromadb.config import Settings
            # Initialize Chroma client
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            self.collection_name = "research_papers"
            self._ensure_collection()
        except Exception:
            # Fallback to pure-Python SQLite vector store on serverless/Vercel
            self._fallback = LightweightVectorStore(self.persist_dir)
            self.collection = self._fallback.collection
            self._is_lightweight = True
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        if self._is_lightweight:
            return self._fallback.add_chunks(chunks)
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
        if self._is_lightweight:
            return self._fallback.search(query_embedding, top_k=top_k)
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
        if self._is_lightweight:
            return self._fallback.search_with_filter(query_embedding, filter_dict=filter_dict, top_k=top_k)
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
        if self._is_lightweight:
            return self._fallback.delete_paper(paper_id, user_id=user_id)
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
        if self._is_lightweight:
            return self._fallback.get_paper_ids()
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
        if self._is_lightweight:
            return self._fallback.get_all_papers_metadata(user_id=user_id)
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
                    
                    if user_id and user_id != "guest":
                        if p_user_clean != u_clean:
                            continue
                    else:
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
        return self.get_all_papers_metadata(user_id=user_id)

    def find_paper_by_hash(self, file_hash: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self._is_lightweight:
            return self._fallback.find_paper_by_hash(file_hash, user_id=user_id)
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
        if self._is_lightweight:
            return self._fallback.count_chunks()
        try:
            return self.collection.count()
        except Exception:
            return 0

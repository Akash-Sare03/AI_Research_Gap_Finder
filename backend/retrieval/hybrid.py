from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import numpy as np
from ..core.embeddings import EmbeddingService
from ..vectorstore.chroma_store import ChromaStore
from ..core.config import Config

class HybridRetriever:
    """Hybrid retrieval combining semantic and keyword search."""
    
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vectorstore = ChromaStore()
        self.top_k = Config.TOP_K
        self.semantic_weight = Config.HYBRID_WEIGHT_SEMANTIC
        self.keyword_weight = Config.HYBRID_WEIGHT_KEYWORD
        
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve using hybrid search."""
        if top_k is None:
            top_k = self.top_k
        
        # Get more candidates than needed
        candidate_count = top_k * 3
        
        # Semantic search
        semantic_results = self._semantic_search(query, candidate_count)
        
        # Keyword search
        keyword_results = self._keyword_search(query, candidate_count)
        
        # Combine and rerank
        combined = self._combine_results(semantic_results, keyword_results)
        
        return combined[:top_k]
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search."""
        query_embedding = self.embedder.embed_text(query)
        results = self.vectorstore.search(query_embedding, top_k)
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform keyword search using BM25."""
        all_chunks = self._get_all_chunks()
        
        if not all_chunks:
            return []
        
        tokenized_chunks = [chunk["text"].split() for chunk in all_chunks]
        bm25 = BM25Okapi(tokenized_chunks)
        
        # Calculate BM25 scores
        scores = bm25.get_scores(query.split())
        scored_chunks = list(zip(all_chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return scored_chunks[:top_k]
    
    def _get_all_chunks(self) -> List[Dict[str, Any]]:
        """Get all chunks for keyword indexing."""
        results = self.vectorstore.collection.get()
        chunks = []
        if results["ids"] and len(results["ids"]) > 0:
            for i, doc_id in enumerate(results["ids"]):
                chunks.append({
                    "id": doc_id,
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
        return chunks
    
    def _combine_results(self, semantic_results: List[Dict[str, Any]], 
                        keyword_results: List) -> List[Dict[str, Any]]:
        """Combine semantic and keyword results."""
        # Normalize scores
        semantic_scores = self._normalize_scores([r.get("distance", 0) for r in semantic_results])
        
        # Process keyword results
        keyword_scores = []
        for r in keyword_results:
            if isinstance(r, tuple):
                keyword_scores.append(r[1])
            else:
                keyword_scores.append(0)
        keyword_scores = self._normalize_scores(keyword_scores)
        
        # Combine scores
        combined = []
        
        # Process semantic results
        for i, result in enumerate(semantic_results):
            if i < len(semantic_scores):
                score = self.semantic_weight * semantic_scores[i]
                combined.append({
                    **result,
                    "score": score,
                    "source": "semantic"
                })
        
        # Process keyword results
        for i, result in enumerate(keyword_results):
            if isinstance(result, tuple):
                chunk = result[0]
                if i < len(keyword_scores):
                    score = self.keyword_weight * keyword_scores[i]
                    combined.append({
                        **chunk,
                        "score": score,
                        "source": "keyword"
                    })
        
        # Sort by combined score
        combined.sort(key=lambda x: x["score"], reverse=True)
        
        # Deduplicate by ID
        seen = set()
        deduplicated = []
        for result in combined:
            if result["id"] not in seen:
                seen.add(result["id"])
                deduplicated.append(result)
        
        return deduplicated
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0] * len(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]
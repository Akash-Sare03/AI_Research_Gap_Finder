from typing import List, Dict, Any, Optional
from ..core.embeddings import EmbeddingService
from ..vectorstore.chroma_store import ChromaStore
from ..core.config import Config

class Retriever:
    """Retrieve relevant chunks from the vector store."""
    
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vectorstore = ChromaStore()
        self.top_k = Config.TOP_K
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query."""
        if top_k is None:
            top_k = self.top_k
        
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search vector store
        results = self.vectorstore.search(query_embedding, top_k)
        
        return results
    
    def retrieve_from_paper(self, query: str, paper_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve chunks from a specific paper."""
        query_embedding = self.embedder.embed_text(query)
        
        results = self.vectorstore.search_with_filter(
            query_embedding,
            {"paper_id": paper_id},
            top_k
        )
        
        return results
    
    def retrieve_multi_paper(self, query: str, top_k: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve chunks from multiple papers with diversity."""
        if top_k is None:
            top_k = self.top_k
        
        # Get all paper IDs
        paper_ids = self.vectorstore.get_paper_ids()
        
        # Get chunks per paper
        results_by_paper = {}
        remaining = top_k
        
        for paper_id in paper_ids:
            if remaining <= 0:
                break
            paper_results = self.retrieve_from_paper(query, paper_id, min(3, remaining))
            if paper_results:
                results_by_paper[paper_id] = paper_results
                remaining -= len(paper_results)
        
        return results_by_paper
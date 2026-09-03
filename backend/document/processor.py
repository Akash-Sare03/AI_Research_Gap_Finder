from typing import Dict, Any, List, Optional
import os
from pathlib import Path
from ..core.config import Config
from .loader import DocumentLoader
from .splitter import DocumentSplitter
from ..core.embeddings import EmbeddingService

class DocumentProcessor:
    """Process documents for indexing."""
    
    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = DocumentSplitter()
        self.embedder = EmbeddingService()
        
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process a single PDF."""
        paper = self.loader.load_pdf(file_path)
        chunks = self.splitter.split_document(paper)
        
        return {
            "paper": paper,
            "chunks": chunks
        }
    
    def prepare_for_indexing(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare chunks for vector indexing."""
        prepared = []
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings in batch
        embeddings = self.embedder.embed_texts(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            prepared.append({
                "id": chunk["chunk_id"],
                "text": chunk["content"],
                "embedding": embedding,
                "metadata": chunk["metadata"]
            })
        
        return prepared
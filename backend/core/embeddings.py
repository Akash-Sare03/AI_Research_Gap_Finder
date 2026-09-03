from typing import List
from ..core.config import Config

class EmbeddingService:
    """Service for generating embeddings using Hugging Face models."""
    
    def __init__(self):
        self.model_name = Config.EMBEDDING_MODEL
        self.dim = Config.EMBEDDING_DIM
        self._model = None
        
    @property
    def model(self):
        """Lazy load embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device='cpu')
            except Exception:
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    self._model = HuggingFaceEmbeddings(
                        model_name=self.model_name,
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                except Exception:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    self._model = HuggingFaceEmbeddings(
                        model_name=self.model_name,
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
        return self._model
        
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        m = self.model
        if hasattr(m, 'encode'):
            emb = m.encode(text, normalize_embeddings=True)
            return emb.tolist() if hasattr(emb, 'tolist') else list(emb)
        return m.embed_query(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        m = self.model
        if hasattr(m, 'encode'):
            embs = m.encode(texts, normalize_embeddings=True)
            return [e.tolist() if hasattr(e, 'tolist') else list(e) for e in embs]
        return m.embed_documents(texts)
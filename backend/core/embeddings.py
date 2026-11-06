from typing import List, Union
import os
import math
import hashlib
import re
from ..core.config import Config


class DeterministicEmbedder:
    """
    Ultra-lightweight pure-Python embedder for serverless environments (zero PyTorch / zero C++).
    Generates normalized 384-dimensional embeddings using subword n-gram hashing and term weighting.
    Ensures fast, deterministic cosine similarity matching without downloading heavy neural net wheels.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode(self, texts: Union[str, List[str]], normalize_embeddings: bool = True) -> Union[List[float], List[List[float]]]:
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else texts
        results = []

        for text in text_list:
            vec = [0.0] * self.dim
            tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', (text or "").lower())
            if not tokens:
                results.append(vec)
                continue

            for i, token in enumerate(tokens):
                # Unigram hashing
                h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % self.dim
                sign1 = 1.0 if (h1 % 2 == 0) else -1.0
                vec[h1] += sign1 * 1.0

                # Bigram hashing for phrase context
                if i < len(tokens) - 1:
                    bigram = f"{token}_{tokens[i+1]}"
                    h2 = int(hashlib.sha1(bigram.encode('utf-8')).hexdigest(), 16) % self.dim
                    sign2 = 1.0 if (h2 % 2 == 0) else -1.0
                    vec[h2] += sign2 * 1.5

            if normalize_embeddings:
                norm = math.sqrt(sum(x * x for x in vec))
                if norm > 1e-9:
                    vec = [x / norm for x in vec]
            results.append(vec)

        return results[0] if is_single else results

    def embed_query(self, text: str) -> List[float]:
        return self.encode(text, normalize_embeddings=True)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.encode(texts, normalize_embeddings=True)


class EmbeddingService:
    """Service for generating embeddings with seamless fallback for serverless hosting."""
    
    def __init__(self):
        self.model_name = Config.EMBEDDING_MODEL
        self.dim = Config.EMBEDDING_DIM
        self._model = None
        
    @property
    def model(self):
        """Lazy load embedding model with graceful serverless fallback."""
        if self._model is None:
            # 1. Try local SentenceTransformers (standard local / container host)
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device='cpu')
            except Exception:
                # 2. Try LangChain HuggingFace
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    self._model = HuggingFaceEmbeddings(
                        model_name=self.model_name,
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                except Exception:
                    # 3. Try LangChain Community HuggingFace
                    try:
                        from langchain_community.embeddings import HuggingFaceEmbeddings
                        self._model = HuggingFaceEmbeddings(
                            model_name=self.model_name,
                            model_kwargs={'device': 'cpu'},
                            encode_kwargs={'normalize_embeddings': True}
                        )
                    except Exception:
                        # 4. Ultra-lightweight deterministic embedder (Vercel serverless / zero-torch environment)
                        self._model = DeterministicEmbedder(dim=self.dim)
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

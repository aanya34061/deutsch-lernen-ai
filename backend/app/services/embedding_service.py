import math
import re
import hashlib
from typing import List, Optional
from app.services.ollama_service import OllamaService

VECTOR_DIMENSION = 1024

GERMAN_STOPWORDS = {
    "der", "die", "das", "ein", "eine", "einer", "einem", "einen", "eines",
    "ist", "sind", "war", "hat", "haben", "wird", "werden",
    "und", "oder", "aber", "auf", "in", "im", "dem", "den", "des", "mit",
    "von", "zu", "um", "für", "bei", "nach", "aus", "über", "unter", "vor"
}

class EmbeddingService:
    @staticmethod
    def _local_hash_embed(text: str, dim: int = VECTOR_DIMENSION) -> List[float]:
        """
        Pure-Python, zero-dependency, deterministic text-to-vector embedding.
        Uses stopword-discounted word tokens and 4-gram morphological features
        hashed into a 1024-dimensional space with L2 unit normalization.
        Provides clean cosine similarity separation for German compound words,
        vocabulary, and grammar questions.
        """
        if not text or not text.strip():
            return [0.0] * dim

        vec = [0.0] * dim
        normalized = text.lower().strip()
        tokens = re.findall(r'\b\w+\b', normalized)

        for token in tokens:
            is_stopword = token in GERMAN_STOPWORDS
            weight = 0.4 if is_stopword else 3.0
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[h % dim] += weight

            # 4-grams for German compound words and roots (non-stopwords only)
            if len(token) >= 4 and not is_stopword:
                for i in range(len(token) - 3):
                    ngram = token[i:i+4]
                    nh = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    vec[nh % dim] += 0.8

        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return [0.0] * dim
        return [round(x / norm, 6) for x in vec]

    @classmethod
    async def embed_texts(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a list of texts.
        Attempts Ollama neural embedding first; falls back cleanly to local vectorizer.
        """
        if not texts:
            return []

        # Try Ollama embeddings if running
        ollama_embeddings = await OllamaService.generate_embeddings(texts)
        if ollama_embeddings and len(ollama_embeddings) == len(texts):
            return ollama_embeddings

        # Fallback to local vectorizer
        return [cls._local_hash_embed(t) for t in texts]

    @classmethod
    async def embed_text(cls, text: str) -> List[float]:
        """Embed a single text string."""
        results = await cls.embed_texts([text])
        return results[0] if results else [0.0] * VECTOR_DIMENSION

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two float vectors."""
        if not vec_a or not vec_b:
            return 0.0
        min_len = min(len(vec_a), len(vec_b))
        if min_len == 0:
            return 0.0

        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for i in range(min_len):
            a = vec_a[i]
            b = vec_b[i]
            dot += a * b
            norm_a += a * a
            norm_b += b * b

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))

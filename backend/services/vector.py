import os
import uuid
import httpx
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings
from models.document_chunk import DocumentChunk

class VectorService:
    # Lazy-loaded singleton for local HuggingFace model to prevent loading on import
    _local_model = None

    @classmethod
    def _get_local_model(cls):
        """Loads and caches the local 384-dimensional SentenceTransformer model in memory."""
        if cls._local_model is None:
            from sentence_transformers import SentenceTransformer
            print("Loading local embedding model 'all-MiniLM-L6-v2' (approx. 90MB)...")
            cls._local_model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._local_model

    @staticmethod
    def chunk_text(text: str) -> List[str]:
        """
        Splits the raw document text into semantic chunks.
        Target size: 1000 characters with a 200 character overlap.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        return splitter.split_text(text)

    @classmethod
    async def generate_embeddings(cls, chunks: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of text chunks.
        Routes to the active provider (local, cohere, or openai).
        """
        if not chunks:
            return []

        provider = settings.EMBEDDING_PROVIDER.lower()

        # Strategy 1: Local Self-Hosted Model (HuggingFace CPU)
        if provider == "local":
            model = cls._get_local_model()
            embeddings = model.encode(chunks)
            # Convert NumPy arrays to standard float lists for SQLAlchemy
            return [vec.tolist() for vec in embeddings]

        # Strategy 2: Cohere Cloud API (384-dim light model)
        elif provider == "cohere":
            if not settings.COHERE_API_KEY:
                raise ValueError("COHERE_API_KEY is not configured in settings/env.")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/embed",
                    headers={
                        "Authorization": f"Bearer {settings.COHERE_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "texts": chunks,
                        "model": "embed-english-light-v3.0",
                        "input_type": "search_document",
                        "embedding_types": ["float"]
                    }
                )
                if response.status_code != 200:
                    raise Exception(f"Cohere embedding API failed: {response.text}")
                
                data = response.json()
                return data["embeddings"]["float"]

        # Strategy 3: OpenAI Cloud API (truncated to 384-dim)
        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured in settings/env.")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": chunks,
                        "model": "text-embedding-3-small",
                        "dimensions": 384
                    }
                )
                if response.status_code != 200:
                    raise Exception(f"OpenAI embedding API failed: {response.text}")
                
                data = response.json()
                return [item["embedding"] for item in data["data"]]

        else:
            raise ValueError(f"Unknown embedding provider configured: {settings.EMBEDDING_PROVIDER}")

    @staticmethod
    async def store_vectors_atomic(
        db: AsyncSession,
        doc_id: uuid.UUID,
        chunks: List[str],
        embeddings: List[List[float]]
    ) -> None:
        """
        Atomically saves all text chunks and their embedding vectors to the database.
        Runs inside the active database session transaction.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings length mismatch.")

        chunk_objs = []
        for index, (text, vector) in enumerate(zip(chunks, embeddings)):
            chunk_obj = DocumentChunk(
                document_id=doc_id,
                chunk_index=index,
                chunk_text=text,
                embedding=vector
            )
            chunk_objs.append(chunk_obj)
        
        db.add_all(chunk_objs)
        # Flush to trigger DB integrity checks and register records,
        # but don't commit here. Let the outer task commit when fully done.
        await db.flush()

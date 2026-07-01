import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import numpy as np

from core.config import settings
from services.vector import VectorService
from models.document import Document
from models.document_chunk import DocumentChunk

# Treat all tests in this file as async
pytestmark = pytest.mark.asyncio

async def test_text_chunking_logic():
    """
    Scenario 1: Verifies the text chunking splits a large string 
    correctly with overlap and keeps chunk lengths within limits.
    """
    sentence = "This is a sentence that will be repeated to build a large document. "
    large_text = sentence * 30  # Length around 2040 characters
    
    chunks = VectorService.chunk_text(large_text)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 1000

async def test_embedding_strategy_routing():
    """
    Scenario 2: Verifies that VectorService routes calls correctly
    based on the active EMBEDDING_PROVIDER config setting.
    """
    # 1. Test "local" Strategy
    with patch.object(settings, "EMBEDDING_PROVIDER", "local"):
        mock_model = MagicMock()
        # Return a mocked 384-dimensional numpy vector
        mock_model.encode.return_value = np.array([[0.5] * 384])
        with patch.object(VectorService, "_get_local_model", return_value=mock_model):
            res = await VectorService.generate_embeddings(["hello"])
            assert len(res) == 1
            assert len(res[0]) == 384
            assert res[0][0] == 0.5

    # 2. Test "cohere" Strategy
    with patch.object(settings, "EMBEDDING_PROVIDER", "cohere"), \
         patch.object(settings, "COHERE_API_KEY", "mock_cohere_key"):
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"embeddings": {"float": [[0.8] * 384]}})
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            res = await VectorService.generate_embeddings(["hello"])
            assert len(res) == 1
            assert len(res[0]) == 384
            assert res[0][0] == 0.8

    # 3. Test "openai" Strategy
    with patch.object(settings, "EMBEDDING_PROVIDER", "openai"), \
         patch.object(settings, "OPENAI_API_KEY", "mock_openai_key"):
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"data": [{"embedding": [0.9] * 384}]})
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            res = await VectorService.generate_embeddings(["hello"])
            assert len(res) == 1
            assert len(res[0]) == 384
            assert res[0][0] == 0.9

async def test_atomic_transaction_rollback(test_db_session):
    """
    Scenario 3: Verifies that if an error is triggered mid-way through vector saving,
    the entire transaction is rolled back and no partial chunks are committed.
    """
    import uuid
    from sqlalchemy import select
    from models.user import User

    # Create a user first to satisfy the foreign key constraint
    dev_user = User(email=f"test_{uuid.uuid4()}@example.com")
    test_db_session.add(dev_user)
    await test_db_session.commit()
    await test_db_session.refresh(dev_user)

    # Create and commit a document linked to that user
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, filename="rollback_test.pdf", user_id=dev_user.id)
    test_db_session.add(doc)
    await test_db_session.commit()

    # Trigger a ValueError in VectorService by forcing mismatched arrays (2 chunks vs 1 vector)
    try:
        await VectorService.store_vectors_atomic(
            test_db_session,
            doc_id,
            chunks=["chunk1", "chunk2"],
            embeddings=[[0.1] * 384]  # Mismatch triggers ValueError
        )
        await test_db_session.commit()
    except ValueError:
        await test_db_session.rollback()

    # Query to assert that NO chunks were saved in PostgreSQL
    result = await test_db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )
    saved_chunks = result.scalars().all()
    assert len(saved_chunks) == 0

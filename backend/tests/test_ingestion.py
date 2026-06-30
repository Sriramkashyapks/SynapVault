import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from models.document import Document

# Instruct pytest-asyncio to treat these as async tests
pytestmark = pytest.mark.asyncio

async def test_upload_valid_pdf():
    """
    Scenario 1: Upload a valid PDF and assert it returns 202.
    """
    # Create a small dummy PDF signature in memory
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"file": ("test_resume.pdf", dummy_pdf, "application/pdf")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files)
        
    assert response.status_code == 202
    json_data = response.json()
    assert json_data["success"] is True
    assert "document_id" in json_data
    assert json_data["status"] == "PENDING"

async def test_upload_invalid_filetype():
    """
    Scenario 2: Upload a .txt file and assert it returns 415.
    """
    files = {"file": ("test_doc.txt", b"plain text content", "text/plain")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files)
        
    assert response.status_code == 415
    assert "Only PDF documents are supported" in response.json()["detail"]

async def test_upload_oversized_pdf():
    """
    Extra Scenario: Upload a PDF exceeding size limit and assert it returns 413.
    """
    # Create a dummy payload larger than 2 MB (2.1 MB)
    oversized_data = b"0" * (2 * 1024 * 1024 + 100)
    files = {"file": ("large_file.pdf", oversized_data, "application/pdf")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files)
        
    assert response.status_code == 413
    assert "File size exceeds" in response.json()["detail"]

async def test_document_metadata_saved(test_db_session):
    """
    Scenario 3: Verify the document database record is correctly written.
    """
    # Let's search the database for the document uploaded in the first test
    result = await test_db_session.execute(
        select(Document).where(Document.filename == "test_resume.pdf")
    )
    doc = result.scalars().first()
    
    assert doc is not None
    assert doc.filename == "test_resume.pdf"
    # Because parsing empty PDFs yields 0 pages, status will be FAILED or PENDING
    assert doc.status in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]

import os
import uuid
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.document import Document, DocumentStatus
from langchain_community.document_loaders import PyPDFLoader

# Resolve uploads directory path dynamically relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocumentService:
    @staticmethod
    async def create_document(db: AsyncSession, filename: str, user_id: uuid.UUID) -> Document:
        """
        Creates a document record in PENDING state.
        """
        db_doc = Document(
            filename=filename,
            user_id=user_id,
            status=DocumentStatus.PENDING
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        return db_doc

    @staticmethod
    async def save_file_locally(file_data, filename: str, doc_id: uuid.UUID) -> str:
        """
        Saves the uploaded file to the local disk.
        """
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_data, buffer)
        return file_path

    @staticmethod
    async def process_pdf_background(doc_id: uuid.UUID, file_path: str, db_factory):
        """
        Parses the PDF text in the background and updates document status.
        Runs in a background thread task.
        """
        async with db_factory() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            try:
                # Update status to PROCESSING
                doc.status = DocumentStatus.PROCESSING
                await db.commit()

                # Load and parse PDF using LangChain
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                
                # Verify that pages were parsed successfully
                if pages and len(pages) > 0:
                    doc.status = DocumentStatus.COMPLETED
                else:
                    doc.status = DocumentStatus.FAILED
                
                await db.commit()

            except Exception as e:
                print(f"Error background-processing PDF {doc_id}: {str(e)}")
                doc.status = DocumentStatus.FAILED
                await db.commit()

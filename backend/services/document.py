import os
import uuid
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.document import Document, DocumentStatus
from langchain_community.document_loaders import PyPDFLoader

from services.vector import VectorService

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
        Parses the PDF text, splits it into semantic chunks, generates vector
        embeddings, and commits everything atomically inside a database transaction.
        """
        async with db_factory() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            try:
                # 1. Update status to PROCESSING
                doc.status = DocumentStatus.PROCESSING
                await db.commit()

                # 2. Parse PDF pages using LangChain
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                
                if pages and len(pages) > 0:
                    # 3. Extract and join full text
                    full_text = "\n".join([page.page_content for page in pages])
                    if not full_text.strip():
                        raise ValueError("PDF contains no extractable text content.")
                    
                    # 4. Chunk text into overlapping blocks
                    chunks = VectorService.chunk_text(full_text)
                    
                    # 5. Generate embeddings vectors (local HF or Cohere/OpenAI)
                    embeddings = await VectorService.generate_embeddings(chunks)
                    
                    # 6. Save chunks and vectors atomically to pgvector
                    await VectorService.store_vectors_atomic(db, doc_id, chunks, embeddings)
                    
                    # 7. Update status to COMPLETED and commit transaction
                    doc.status = DocumentStatus.COMPLETED
                    await db.commit()
                    print(f"Document {doc_id} successfully parsed, chunked, and vectorized.")
                else:
                    doc.status = DocumentStatus.FAILED
                    await db.commit()

            except Exception as e:
                print(f"Error background-processing PDF {doc_id}: {str(e)}")
                # Transactional Safety: Rollback any partially added database modifications
                await db.rollback()
                
                # Start a fresh transaction to record the FAILED state of the document
                await db.execute(
                    update(Document)
                    .where(Document.id == doc_id)
                    .values(status=DocumentStatus.FAILED)
                )
                await db.commit()

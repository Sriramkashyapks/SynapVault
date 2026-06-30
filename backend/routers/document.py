import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, AsyncSessionLocal
from core.config import settings
from services.document import DocumentService

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"]
)


async def get_dev_user_id(db: AsyncSession = Depends(get_db)) -> uuid.UUID:
    """
    Helper dependency to retrieve our default development user ID.
    """
    from sqlalchemy import select
    from models.user import User
    
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Development user has not been initialized. Please restart the backend."
        )
    return user.id

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_dev_user_id)
):
    """
    Uploads a PDF document (Max 2 MB), saves it locally,
    and processes the text content in a background thread.
    """
    # 1. Validate File Type (only application/pdf or .pdf extension)
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid file format. Only PDF documents are supported."
        )

    # 2. Validate File Size (<= 2 MB)
    file_size = file.size
    if file_size is None:
        # Fallback if file.size is not populated
        await file.seek(0)
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset cursor for the next read/write

    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File size exceeds the {settings.MAX_FILE_SIZE_MB} MB limit. (Your file size: {file_size / (1024*1024):.2f} MB)"
        )

    # 3. Create document record in database (PENDING status)
    doc = await DocumentService.create_document(db, file.filename, user_id)

    # 4. Save file to local uploads directory
    file_path = await DocumentService.save_file_locally(file.file, file.filename, doc.id)

    # 5. Offload PDF parsing to FastAPI BackgroundTasks to keep the server non-blocking
    # We pass the AsyncSessionLocal factory so the background task can create its own DB connection
    background_tasks.add_task(
        DocumentService.process_pdf_background,
        doc.id,
        file_path,
        AsyncSessionLocal
    )

    return {
        "success": True,
        "message": "Document uploaded successfully and queued for parsing.",
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status
    }

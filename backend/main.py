from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from core.database import get_db, AsyncSessionLocal
from models.user import User
from routers import document

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan events.
    Runs on startup to initialize default dev resources.
    """
    # Create a default admin user on startup if the database is empty
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            default_user = User(email="admin@synapvault.local")
            db.add(default_user)
            await db.commit()
            print("Default dev user 'admin@synapvault.local' initialized successfully.")
    
    yield  # Application runs

app = FastAPI(
    title="SynapVault API",
    description="Enterprise Knowledge Network & Security Vault Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(document.router)

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "ok",
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

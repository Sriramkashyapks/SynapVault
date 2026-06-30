from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.database import get_db

app = FastAPI(
    title="SynapVault API",
    description="Enterprise Knowledge Network & Security Vault Backend",
    version="1.0.0"
)

# Set up CORS middleware to allow our Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    Also verifies database connectivity by performing a simple query.
    """
    try:
        # Perform a quick SQL query to check if database is alive
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
 
import os
from dotenv import load_dotenv

# Load environment variables from the backend/.env file
load_dotenv()

class Settings:
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://synapuser:synappassword@localhost:5432/synapvault"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()

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

    # File Upload Configuration
    # Reads from .env (default: 2 MB limit if not specified)
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2"))
    
    @property
    def MAX_FILE_SIZE(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

settings = Settings()

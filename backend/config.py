import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "VegasAir"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vegasair")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # Backend
    ]

settings = Settings() 
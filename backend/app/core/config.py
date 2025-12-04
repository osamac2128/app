from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AISJ Connect API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "aisj_connect"
    
    SECRET_KEY: str = "your-secret-key-here" # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

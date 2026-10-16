import time
from fastapi import FastAPI, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from pydantic_settings import BaseSettings
from typing import List
import os

# Import from database
from database import (
    get_db, ensure_database_exists, create_tables, get_db_config
)
from routes import resume
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database configuration
db_config = get_db_config()

class Settings(BaseSettings):
    app_name: str = "Resume API"
    app_version: str = "1.0.0"
    
    # Use the database configuration from database.py
    postgres_user: str = db_config["user"]
    postgres_password: str = db_config["password"]
    postgres_host: str = db_config["host"]
    postgres_port: str = db_config["port"]
    postgres_db: str = db_config["name"]
    
    # Include API keys and email credentials from .env
    mistral_api_key: str = ""
    # openai_api_key: str = ""
    gemini_api_key: str = ""
    pinecone_api_key:str
    index_name:str
    pinecone_environment: str = ""


    
    cors_origins: List[str] = ["http://localhost:3000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        # Alternatively, use this to ignore extra fields:
        # extra = "ignore" 

settings = Settings()

app = FastAPI(
    title=settings.app_name,
    description="API for Resume Extraction and Comparision",
    version=settings.app_version,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow any origin for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"] # Allow all hosts on Vercel
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database error occurred", "error": str(exc)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred", "error": str(exc)}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    try:
        
        # Ensure database exists
        ensure_database_exists(settings.postgres_db)
        
        # Create tables
        create_tables()
        
        print(f"Application {settings.app_name} v{settings.app_version} started")
        print(f"Connected to database: {settings.postgres_host}/{settings.postgres_db}")
    except Exception as e:
        print(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    print(f"Application {settings.app_name} shutting down")

app.include_router(resume.router, prefix="/api/v1", tags=["Resume"])

# Root endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to the {settings.app_name}",
        "version": settings.app_version,
    }

@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.app_version,
        "db_host": settings.postgres_host,
        "db_name": settings.postgres_db
    }

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create base class for declarative models
Base = declarative_base()

# Database connection details from environment variables
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

# Database URLs (sslmode=require is needed for Neon cloud PostgreSQL)
ADMIN_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres?sslmode=require"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

# Create engines
admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT", connect_args={"sslmode": "require"})
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_database_exists(db_name):
    """Check if database exists and create it if needed"""
    try:
        with admin_engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
            return True
    except OperationalError as e:
        print(f"Error connecting to PostgreSQL for {db_name}:", e)
        return False

def create_tables():
    """Create tables based on SQLAlchemy models"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Resume Table created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def get_db():
    """Dependency to get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get database configuration for external use
def get_db_config():
    return {
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST,
        "port": DB_PORT,
        "name": DB_NAME,
    }

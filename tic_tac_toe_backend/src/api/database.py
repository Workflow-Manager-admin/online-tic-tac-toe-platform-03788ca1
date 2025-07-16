import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from .models import Base

# Load environment variables from .env
load_dotenv()

# PUBLIC_INTERFACE
def get_database_url():
    """Get the database URL from environment variable or fallback to local SQLite file.

    Returns:
        str: The SQLAlchemy database URL.
    """
    db_url = os.getenv("SQLITE_DATABASE_URL")
    if db_url:
        return db_url
    # Default: store SQLite db in project root
    return "sqlite:///./tic_tac_toe.db"

SQLALCHEMY_DATABASE_URL = get_database_url()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db():
    """Yields a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def init_db():
    """Create all tables in the database. Call this at app startup."""
    Base.metadata.create_all(bind=engine)

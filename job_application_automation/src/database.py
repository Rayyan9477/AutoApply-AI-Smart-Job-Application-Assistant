"""
Database configuration and session management with error handling and retries.
"""
import os
from contextlib import contextmanager
from typing import Generator, Optional, Tuple, Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError

from .models import Base
from .database_errors import (
    handle_db_errors,
    with_retry,
    safe_commit,
    DatabaseError,
    ConnectionError
)

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/job_applications.db")
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "1800"))

# Create engine with connection pooling
engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup and error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

@handle_db_errors
def init_db() -> None:
    """Initialize database schema with error handling."""
    # Create database directory if using SQLite
    if DB_URL.startswith("sqlite"):
        os.makedirs(os.path.dirname(DB_URL.replace("sqlite:///", "")), exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

def get_engine():
    """Get SQLAlchemy engine."""
    return engine

@with_retry()
@handle_db_errors
def check_database_connection() -> Tuple[bool, Optional[str]]:
    """
    Check if database connection is working with retries.
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        # Try to connect and execute a simple query
        with get_db() as db:
            db.execute(text("SELECT 1"))
        return True, None
    except OperationalError as e:
        return False, f"Database connection error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error checking database: {str(e)}"

@with_retry()
@handle_db_errors
def get_database_stats() -> dict:
    """
    Get database statistics and health metrics with retries.
    
    Returns:
        Dictionary containing database statistics.
    """
    try:
        stats = {
            "connection_pool": {
                "size": engine.pool.size(),
                "checkedin": engine.pool.checkedin(),
                "overflow": engine.pool.overflow(),
                "checkedout": engine.pool.checkedout(),
            },
            "tables": {},
            "status": "healthy"
        }
        
        # Get table statistics
        with get_db() as db:
            for table in Base.metadata.sorted_tables:
                row_count = db.query(table).count()
                stats["tables"][table.name] = {
                    "row_count": row_count
                }
                
        return stats
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@with_retry()
def execute_with_retry(session: Session, query: Any, params: Optional[dict] = None) -> Any:
    """
    Execute a database query with retry logic.
    
    Args:
        session: SQLAlchemy session
        query: Query to execute
        params: Optional query parameters
        
    Returns:
        Query result
    """
    try:
        if params:
            result = session.execute(query, params)
        else:
            result = session.execute(query)
        return result
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Error executing query: {e}")
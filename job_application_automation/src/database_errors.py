"""
Database error handling and retry mechanisms.
"""
import logging
from typing import TypeVar, Callable, Any
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
    RetryError
)
from sqlalchemy.exc import (
    SQLAlchemyError,
    OperationalError,
    IntegrityError,
    DBAPIError
)

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for return type
T = TypeVar('T')

class DatabaseError(Exception):
    """Base class for database errors."""
    pass

class ConnectionError(DatabaseError):
    """Database connection error."""
    pass

class QueryError(DatabaseError):
    """Database query error."""
    pass

class IntegrityConstraintError(DatabaseError):
    """Database integrity constraint violation."""
    pass

def handle_db_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database errors and provide appropriate error messages.
    
    Args:
        func: Function to wrap.
        
    Returns:
        Wrapped function with error handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {e}")
            raise IntegrityConstraintError(f"Database integrity error: {e}")
        except OperationalError as e:
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise ConnectionError(f"Database connection error: {e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise QueryError(f"Database query error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise DatabaseError(f"Unexpected database error: {e}")
    return wrapper

def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry database operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.
        
    Returns:
        Wrapped function with retry logic.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type((OperationalError, DBAPIError)),
            before=before_log(logger, logging.DEBUG),
            after=after_log(logger, logging.DEBUG),
            reraise=True
        )
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except RetryError as e:
                logger.error(f"Max retry attempts ({max_attempts}) reached for {func.__name__}")
                if e.last_attempt.exception():
                    raise e.last_attempt.exception()
                raise DatabaseError("Max retry attempts reached")
        return wrapper
    return decorator

def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error should be retried.
    
    Args:
        exception: Exception to check.
        
    Returns:
        True if the error is retryable, False otherwise.
    """
    retryable_errors = (
        OperationalError,  # Connection errors, deadlocks, etc.
        DBAPIError,       # Low-level database API errors
    )
    
    # Check if exception is retryable
    if isinstance(exception, retryable_errors):
        # Check specific error messages that indicate retry-able conditions
        error_msg = str(exception).lower()
        retryable_messages = [
            "deadlock",
            "lock timeout",
            "lost connection",
            "connection reset",
            "operational error",
            "temporarily unavailable"
        ]
        return any(msg in error_msg for msg in retryable_messages)
    
    return False

def safe_commit(session: Any) -> None:
    """
    Safely commit database changes with retry logic.
    
    Args:
        session: SQLAlchemy session to commit.
    """
    @with_retry()
    def _commit():
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    try:
        _commit()
    except Exception as e:
        logger.error(f"Error committing transaction: {e}")
        raise
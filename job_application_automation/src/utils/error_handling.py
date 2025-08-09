"""
Error handling utilities for job application automation.
"""

import logging
import functools
import traceback
from typing import Callable, TypeVar, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)

# Type variable for return type
T = TypeVar('T')

# Set up logging
logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base class for application errors."""
    pass


class NetworkError(ApplicationError):
    """Network-related errors."""
    pass


class APIError(ApplicationError):
    """API-related errors."""
    pass


class ConfigurationError(ApplicationError):
    """Configuration-related errors."""
    pass


def with_error_handling(
    error_types: tuple = (Exception,),
    reraise: bool = True,
    log_level: int = logging.ERROR
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator to handle errors and provide appropriate error messages.
    
    Args:
        error_types: Tuple of error types to catch.
        reraise: Whether to reraise the error after handling.
        log_level: Logging level for error messages.
        
    Returns:
        Wrapped function with error handling.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}: {e}\n{traceback.format_exc()}"
                )
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retry_on: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.
        retry_on: Tuple of exception types to retry on.
        
    Returns:
        Wrapped function with retry logic.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_on),
            before=before_log(logger, logging.DEBUG),
            after=after_log(logger, logging.DEBUG),
            reraise=True
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)
        return wrapper
    return decorator

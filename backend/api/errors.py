"""Custom exceptions and error handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class ExplainerError(Exception):
    """Base exception for explainer errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SearchError(ExplainerError):
    """Error during search operations."""
    
    def __init__(self, message: str = "Search service unavailable"):
        super().__init__(message, status_code=503)


class LLMError(ExplainerError):
    """Error during LLM operations."""
    
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(message, status_code=503)


class ValidationError(ExplainerError):
    """Input validation error."""
    
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, status_code=400)


class RateLimitError(ExplainerError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the FastAPI app."""
    
    @app.exception_handler(ExplainerError)
    async def explainer_error_handler(request: Request, exc: ExplainerError):
        logger.error(f"ExplainerError: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "type": type(exc).__name__}
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "An unexpected error occurred", "type": "InternalError"}
        )


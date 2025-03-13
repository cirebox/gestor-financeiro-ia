# src/interfaces/api/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions.domain_exceptions import CategoryNotFoundException

async def category_not_found_exception_handler(request: Request, exc: CategoryNotFoundException):
    """Manipulador de exceção para CategoryNotFoundException."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )
"""Centralised exception handling for the API layer."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.models.common import ErrorResponse


def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    payload = ErrorResponse(
        error=exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__,
        message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        details=getattr(exc, "headers", None),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
        headers=getattr(exc, "headers", None),
    )


def _validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        error="ValidationError",
        message="Request validation failed.",
        details=exc.errors(),
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)

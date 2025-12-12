"""Centralised exception handling for the API layer."""

from collections.abc import Awaitable, Callable
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api.models.common import ErrorResponse, ValidationErrorResponse

ExceptionHandler = Callable[[Request, Exception], Response | Awaitable[Response]]


def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    detail_dict = detail if isinstance(detail, dict) else None
    detail_str = detail if isinstance(detail, str) else None

    if detail_dict is not None:
        error_code = detail_dict.get("code", exc.__class__.__name__)
        message = detail_dict.get("message", str(detail_dict))
    elif detail_str is not None:
        error_code = detail_str
        message = detail_str
    else:
        error_code = exc.__class__.__name__
        message = str(detail)

    payload = ErrorResponse(
        error=str(error_code),
        message=str(message),
        details=_extract_details(detail_dict),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
        headers=getattr(exc, "headers", None),
    )


def _validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ValidationErrorResponse(details=cast(list[dict[str, Any]], exc.errors()))
    return JSONResponse(status_code=422, content=payload.model_dump())


def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    # Defensive: never leak internal exception details by default.
    payload = ErrorResponse(
        error="InternalServerError",
        message="Internal server error.",
        details=None,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


def _extract_details(detail_dict: dict[str, Any] | None) -> Any | None:
    """Normalize HTTPException detail payloads into ErrorResponse.details."""

    if not detail_dict:
        return None
    details = detail_dict.get("details")
    if details is not None:
        return details
    # Treat details as "additional context" only; never echo the primary error fields
    # back into `details` when callers raise `detail={"code": ..., "message": ...}`.
    extras = {k: v for k, v in detail_dict.items() if k not in {"code", "message"}}
    return extras or None


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    http_handler = cast(ExceptionHandler, _http_exception_handler)
    validation_handler = cast(ExceptionHandler, _validation_exception_handler)
    unhandled_handler = cast(ExceptionHandler, _unhandled_exception_handler)

    app.add_exception_handler(HTTPException, http_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(Exception, unhandled_handler)

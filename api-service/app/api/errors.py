"""Centralised exception handling for the API layer."""

from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api.models.common import ErrorResponse

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
        details=getattr(exc, "headers", None),
    )
    body = payload.model_dump()
    if detail_dict is not None:
        body["detail"] = detail_dict
    else:
        body.setdefault("detail", payload.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
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

    http_handler = cast(ExceptionHandler, _http_exception_handler)
    validation_handler = cast(ExceptionHandler, _validation_exception_handler)

    app.add_exception_handler(HTTPException, http_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)

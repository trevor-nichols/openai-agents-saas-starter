import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import log_context, log_event


class LoggingMiddleware(BaseHTTPMiddleware):
    """Custom logging middleware for request and response logging."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else None

        with log_context(
            correlation_id=correlation_id,
            http_method=request.method,
            http_path=str(request.url),
            client_ip=client_ip,
        ):
            log_event(
                "http.request",
                method=request.method,
                path=str(request.url),
                client_ip=client_ip,
                user_agent=request.headers.get("user-agent"),
            )
            try:
                response = await call_next(request)
            except Exception as exc:  # pragma: no cover - bubbled to handlers
                duration_ms = round((time.perf_counter() - start_time) * 1000, 3)
                log_event(
                    "http.error",
                    level="error",
                    message=str(exc),
                    exc_info=exc,
                    duration_ms=duration_ms,
                )
                raise

            process_time = time.perf_counter() - start_time
            duration_ms = round(process_time * 1000, 3)

            log_event(
                "http.response",
                status_code=response.status_code,
                duration_ms=duration_ms,
                content_length=response.headers.get("content-length"),
                content_type=response.headers.get("content-type"),
            )

            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            return response

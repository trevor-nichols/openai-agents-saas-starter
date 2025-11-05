# File: app/middleware/logging.py
# Purpose: Logging middleware for anything-agents
# Dependencies: fastapi, starlette, logging
# Used by: main.py for request/response logging

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("anything-agents")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Custom logging middleware for request and response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.url} [ID: {correlation_id}]")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                f"Response: {response.status_code} [{correlation_id}] "
                f"({round(process_time, 4)}s)"
            )
            
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} [{correlation_id}] ({round(process_time, 4)}s)",
                exc_info=True
            )
            raise e 
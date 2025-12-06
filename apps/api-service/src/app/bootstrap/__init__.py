"""Bootstrap utilities for wiring application-wide dependencies."""

from .container import (
    ApplicationContainer,
    get_container,
    reset_container,
    set_container,
    shutdown_container,
    wire_conversation_query_service,
)

__all__ = [
    "ApplicationContainer",
    "get_container",
    "reset_container",
    "set_container",
    "shutdown_container",
    "wire_conversation_query_service",
]

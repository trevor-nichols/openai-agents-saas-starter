"""OpenAPI customization for a stable, truthful public contract.

FastAPI's generated OpenAPI is accurate for most JSON endpoints, but it cannot
infer some important contract details on its own (SSE streams, binary/RSS
responses, and raw-body webhook endpoints).

This module applies a small, auditable patch layer to the generated schema so
client generation stays correct and stable.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Return the application's OpenAPI schema with contract patches applied."""

    if app.openapi_schema is not None:
        return app.openapi_schema

    schema: dict[str, Any] = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    _patch_components(schema)
    _patch_common_error_responses(schema)
    _patch_validation_errors(schema)
    _patch_streaming_endpoints(schema)
    _patch_binary_downloads(schema)
    _patch_rss(schema)
    _patch_raw_body_endpoints(schema)

    app.openapi_schema = schema
    return schema


def _components(schema: dict[str, Any]) -> dict[str, Any]:
    return schema.setdefault("components", {})


def _schemas(schema: dict[str, Any]) -> dict[str, Any]:
    return _components(schema).setdefault("schemas", {})


def _paths(schema: dict[str, Any]) -> dict[str, Any]:
    return schema.setdefault("paths", {})


def _patch_components(schema: dict[str, Any]) -> None:
    # We inject these explicitly so we can reference them across operations.
    schemas = _schemas(schema)
    schemas.setdefault(
        "ErrorResponse",
        {
            "type": "object",
            "title": "ErrorResponse",
            "description": "Standard error response envelope.",
            "properties": {
                "success": {
                    "type": "boolean",
                    "default": False,
                    "description": "Operation success status flag.",
                },
                "error": {
                    "type": "string",
                    "description": "Short machine-readable error name.",
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error description.",
                },
                "details": {
                    "description": "Additional error context for debugging.",
                },
            },
            "required": ["success", "error", "message"],
        },
    )
    schemas.setdefault(
        "ValidationErrorResponse",
        {
            "type": "object",
            "title": "ValidationErrorResponse",
            "description": "Validation error envelope (RequestValidationError).",
            "properties": {
                "success": {
                    "type": "boolean",
                    "default": False,
                    "description": "Operation success status flag.",
                },
                "error": {
                    "type": "string",
                    "description": "Short machine-readable error name.",
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error description.",
                },
                "details": {
                    "type": "array",
                    "description": "Pydantic validation errors list.",
                    "items": {"type": "object"},
                },
            },
            "required": ["success", "error", "message", "details"],
        },
    )


def _patch_validation_errors(schema: dict[str, Any]) -> None:
    """Replace FastAPI's HTTPValidationError with our validation envelope."""

    paths = _paths(schema)
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            r422 = responses.get("422")
            if not isinstance(r422, dict):
                continue
            content = r422.get("content")
            if not isinstance(content, dict):
                continue
            app_json = content.get("application/json")
            if not isinstance(app_json, dict):
                continue

            app_json["schema"] = {"$ref": "#/components/schemas/ValidationErrorResponse"}

    # We no longer reference FastAPI's default validation error shapes in the public contract.
    schemas = _schemas(schema)
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)


def _patch_common_error_responses(schema: dict[str, Any]) -> None:
    """Ensure error responses use our unified error envelope.

    We intentionally include a shared baseline across operations so generated
    clients can depend on the error shape without per-route guesswork.
    """

    error_ref = {"$ref": "#/components/schemas/ErrorResponse"}
    baseline: dict[str, str] = {
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "409": "Conflict",
        "413": "Request Entity Too Large",
        "429": "Too Many Requests",
        "500": "Internal Server Error",
        "502": "Bad Gateway",
        "503": "Service Unavailable",
    }

    for path_item in _paths(schema).values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            responses = operation.setdefault("responses", {})
            if not isinstance(responses, dict):
                continue

            # Default response helps some generators model error unions even if
            # they ignore specific codes.
            responses.setdefault(
                "default",
                {
                    "description": "Error Response",
                    "content": {"application/json": {"schema": error_ref}},
                },
            )

            for status_code, description in baseline.items():
                if status_code in responses:
                    # Avoid overwriting any explicit, route-specific schemas.
                    continue
                responses[status_code] = {
                    "description": description,
                    "content": {"application/json": {"schema": error_ref}},
                }


def _patch_streaming_endpoints(schema: dict[str, Any]) -> None:
    """Declare SSE responses as text/event-stream with per-event JSON payload schema."""

    paths = _paths(schema)

    activity = paths.get("/api/v1/activity/stream")
    if isinstance(activity, dict) and isinstance(activity.get("get"), dict):
        _set_sse_response(
            activity["get"],
            description=(
                "Server-sent events stream of activity updates.\n\n"
                "SSE framing:\n"
                "- Heartbeats are emitted as comments: `:\\n\\n`\n"
                "- Events are emitted as: `data: <json>\\n\\n`\n\n"
                "The `<json>` payload is a single ActivityEventItem object."
            ),
            payload_schema_ref="#/components/schemas/ActivityEventItem",
        )

    billing = paths.get("/api/v1/billing/stream")
    if isinstance(billing, dict) and isinstance(billing.get("get"), dict):
        _set_sse_response(
            billing["get"],
            description=(
                "Server-sent events stream of billing events.\n\n"
                "SSE framing:\n"
                "- Heartbeats are emitted as comments: `: ping\\n\\n`\n"
                "- Events are emitted as: `data: <json>\\n\\n`\n\n"
                "The `<json>` payload is a single BillingEventResponse object."
            ),
            payload_schema_ref="#/components/schemas/BillingEventResponse",
        )


def _set_sse_response(
    operation: dict[str, Any],
    *,
    description: str,
    payload_schema_ref: str,
) -> None:
    responses = operation.setdefault("responses", {})
    r200 = responses.setdefault("200", {})
    r200["description"] = description
    r200["content"] = {
        "text/event-stream": {
            "schema": {"$ref": payload_schema_ref},
        }
    }


def _patch_binary_downloads(schema: dict[str, Any]) -> None:
    paths = _paths(schema)
    for path in (
        "/api/v1/openai/files/{file_id}/download",
        "/api/v1/openai/containers/{container_id}/files/{file_id}/download",
    ):
        item = paths.get(path)
        if not isinstance(item, dict) or not isinstance(item.get("get"), dict):
            continue
        operation = item["get"]
        responses = operation.setdefault("responses", {})
        r200 = responses.setdefault("200", {})
        r200["description"] = "Binary file download."
        r200.setdefault("headers", {})
        headers = r200["headers"]
        if isinstance(headers, dict):
            headers.setdefault(
                "Content-Disposition",
                {
                    "schema": {"type": "string"},
                    "description": "Attachment filename hint.",
                },
            )
            headers.setdefault(
                "Cache-Control",
                {
                    "schema": {"type": "string"},
                    "description": "Cache policy for downloads.",
                },
            )
        r200["content"] = {
            "application/octet-stream": {
                "schema": {"type": "string", "format": "binary"},
            }
        }


def _patch_rss(schema: dict[str, Any]) -> None:
    paths = _paths(schema)
    rss = paths.get("/api/v1/status/rss")
    if not isinstance(rss, dict) or not isinstance(rss.get("get"), dict):
        return
    operation = rss["get"]
    responses = operation.setdefault("responses", {})
    r200 = responses.setdefault("200", {})
    r200["description"] = "RSS feed (XML)."
    r200["content"] = {"application/rss+xml": {"schema": {"type": "string"}}}


def _patch_raw_body_endpoints(schema: dict[str, Any]) -> None:
    paths = _paths(schema)

    stripe = paths.get("/webhooks/stripe")
    if isinstance(stripe, dict) and isinstance(stripe.get("post"), dict):
        operation = stripe["post"]
        operation.setdefault("parameters", [])
        _ensure_header_param(
            operation["parameters"],
            name="stripe-signature",
            required=True,
            description="Stripe signature header used to verify the webhook payload.",
        )
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"type": "object", "additionalProperties": True},
                    "description": "Stripe event payload (shape varies by event type).",
                },
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                    "description": "Raw webhook bytes (useful for signature verification).",
                },
            },
        }

    logs = paths.get("/api/v1/logs")
    if isinstance(logs, dict) and isinstance(logs.get("post"), dict):
        operation = logs["post"]
        operation.setdefault("parameters", [])
        _ensure_header_param(
            operation["parameters"],
            name="x-log-signature",
            required=True,
            description="HMAC signature for the raw request body.",
        )
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/FrontendLogPayload"},
                }
            },
        }


def _ensure_header_param(
    parameters: list[Any],
    *,
    name: str,
    required: bool,
    description: str,
) -> None:
    for param in parameters:
        if isinstance(param, dict) and param.get("in") == "header" and param.get("name") == name:
            param["required"] = required
            param["description"] = description
            param.setdefault("schema", {"type": "string"})
            return

    parameters.append(
        {
            "in": "header",
            "name": name,
            "required": required,
            "description": description,
            "schema": {"type": "string"},
        }
    )


__all__ = ["build_openapi_schema"]

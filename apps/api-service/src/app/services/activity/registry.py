"""Registry of allowed activity event actions and metadata validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field


@dataclass(slots=True)
class ActivityEventDefinition:
    action: str
    allowed_metadata_keys: set[str] = field(default_factory=set)
    required_metadata_keys: set[str] = field(default_factory=set)

    def validate_metadata(self, metadata: Mapping[str, object] | None) -> None:
        if metadata is None:
            if self.required_metadata_keys:
                missing_keys_str = ", ".join(sorted(self.required_metadata_keys))
                raise ValueError(f"Metadata missing required keys: {missing_keys_str}")
            return

        extra_keys = set(metadata.keys()) - self.allowed_metadata_keys
        if extra_keys:
            overflow = ", ".join(sorted(extra_keys))
            raise ValueError(f"Metadata contains unsupported keys: {overflow}")

        missing: set[str] = self.required_metadata_keys - set(metadata.keys())
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Metadata missing required keys: {missing_list}")


def _def(
    action: str,
    *,
    allowed: Iterable[str] = (),
    required: Iterable[str] = (),
) -> ActivityEventDefinition:
    return ActivityEventDefinition(
        action=action,
        allowed_metadata_keys=set(allowed),
        required_metadata_keys=set(required),
    )


REGISTRY: dict[str, ActivityEventDefinition] = {
    # Auth lifecycle
    "auth.signup.success": _def("auth.signup.success", allowed=("user_id", "tenant_id")),
    "auth.signup.failure": _def("auth.signup.failure", allowed=("reason", "email")),
    "auth.login.success": _def(
        "auth.login.success",
        allowed=("user_id", "tenant_id", "method"),
        required=("user_id",),
    ),
    "auth.login.failure": _def("auth.login.failure", allowed=("reason", "email")),
    "auth.logout": _def("auth.logout", allowed=("user_id", "tenant_id")),
    "auth.password.changed": _def(
        "auth.password.changed", allowed=("user_id",), required=("user_id",)
    ),
    "auth.service_account.issued": _def(
        "auth.service_account.issued",
        allowed=("service_account", "scopes", "actor_id", "reason"),
        required=("service_account",),
    ),
    "auth.service_account.revoked": _def(
        "auth.service_account.revoked",
        allowed=("service_account", "reason"),
        required=("service_account",),
    ),
    # Conversations / agents
    "conversation.created": _def(
        "conversation.created",
        allowed=("conversation_id", "agent_entrypoint"),
        required=("conversation_id",),
    ),
    "conversation.cleared": _def(
        "conversation.cleared",
        allowed=("conversation_id",),
        required=("conversation_id",),
    ),
    "conversation.message": _def(
        "conversation.message",
        allowed=("conversation_id", "message_role"),
        required=("conversation_id",),
    ),
    "conversation.run.started": _def(
        "conversation.run.started",
        allowed=("conversation_id", "run_id", "agent"),
        required=("conversation_id",),
    ),
    "conversation.run.completed": _def(
        "conversation.run.completed",
        allowed=("conversation_id", "run_id", "agent", "reason"),
        required=("conversation_id",),
    ),
    # Workflows
    "workflow.run.started": _def(
        "workflow.run.started",
        allowed=("workflow_key", "run_id", "message"),
        required=("workflow_key", "run_id"),
    ),
    "workflow.run.completed": _def(
        "workflow.run.completed",
        allowed=("workflow_key", "run_id", "status"),
        required=("workflow_key", "run_id", "status"),
    ),
    "workflow.run.cancelled": _def(
        "workflow.run.cancelled",
        allowed=("workflow_key", "run_id", "reason"),
        required=("workflow_key", "run_id"),
    ),
    # Billing bridge
    "billing.subscription.updated": _def(
        "billing.subscription.updated",
        allowed=("subscription_id", "status", "plan_code"),
        required=("status",),
    ),
    "billing.invoice.paid": _def(
        "billing.invoice.paid",
        allowed=("invoice_id", "total", "reason"),
        required=("invoice_id",),
    ),
    "billing.invoice.failed": _def(
        "billing.invoice.failed",
        allowed=("invoice_id", "reason", "total"),
        required=("invoice_id",),
    ),
    # Storage / vector / containers
    "storage.file.uploaded": _def(
        "storage.file.uploaded",
        allowed=("object_id", "bucket"),
        required=("object_id",),
    ),
    "storage.file.deleted": _def(
        "storage.file.deleted",
        allowed=("object_id", "bucket"),
        required=("object_id",),
    ),
    "vector.file.synced": _def(
        "vector.file.synced",
        allowed=("vector_store_id", "file_id", "state"),
        required=("vector_store_id", "file_id", "state"),
    ),
    "container.lifecycle": _def(
        "container.lifecycle",
        allowed=("container_id", "event", "agent_key"),
        required=("container_id", "event"),
    ),
}


def validate_action(action: str, metadata: Mapping[str, object] | None) -> None:
    definition = REGISTRY.get(action)
    if not definition:
        raise ValueError(f"Unsupported activity action '{action}'")
    definition.validate_metadata(metadata)


__all__ = ["ActivityEventDefinition", "REGISTRY", "validate_action"]

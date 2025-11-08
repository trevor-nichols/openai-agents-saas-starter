"""Service account catalog loader and helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator


class ServiceAccountCatalogError(RuntimeError):
    """Base exception for service-account catalog issues."""


class ServiceAccountNotFoundError(ServiceAccountCatalogError):
    """Raised when the requested service account does not exist."""


class ServiceAccountDefinition(BaseModel):
    """Represents a single service-account entry from the catalog."""

    account: str = Field(pattern=r"^[a-z0-9\-]+$", min_length=3, max_length=64)
    description: str = Field(min_length=3)
    allowed_scopes: list[str] = Field(min_length=1)
    requires_tenant: bool = True
    default_ttl_minutes: int | None = Field(default=None, gt=0)
    max_ttl_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def _validate_ttl(self) -> ServiceAccountDefinition:
        if self.default_ttl_minutes and self.default_ttl_minutes > self.max_ttl_minutes:
            raise ValueError("default_ttl_minutes cannot exceed max_ttl_minutes.")
        return self


@dataclass(frozen=True)
class ServiceAccountRegistry:
    """Process-local registry for service accounts."""

    definitions: dict[str, ServiceAccountDefinition]

    def get(self, account: str) -> ServiceAccountDefinition:
        try:
            return self.definitions[account]
        except KeyError as exc:
            raise ServiceAccountNotFoundError(
                f"Service account '{account}' is not defined."
            ) from exc

    def accounts(self) -> Iterable[str]:
        return self.definitions.keys()


def _catalog_path(custom_path: Path | None = None) -> Path:
    if custom_path:
        return custom_path
    package = resources.files("app.core")
    return Path(package / "service_accounts.yaml")


def _load_raw_catalog(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ServiceAccountCatalogError(f"Service-account catalog not found at '{path}'.") from exc
    except yaml.YAMLError as exc:
        raise ServiceAccountCatalogError(
            f"Failed to parse service-account catalog at '{path}'."
        ) from exc

    if not isinstance(data, dict) or "service_accounts" not in data:
        raise ServiceAccountCatalogError("Catalog must contain a 'service_accounts' mapping.")
    return data


def load_service_account_registry(path: Path | None = None) -> ServiceAccountRegistry:
    """Load the service-account catalog and return a registry instance."""

    catalog_path = _catalog_path(path)
    raw = _load_raw_catalog(catalog_path)
    entries = raw.get("service_accounts", [])

    definitions: dict[str, ServiceAccountDefinition] = {}

    for entry in entries:
        try:
            definition = ServiceAccountDefinition.model_validate(entry)
        except ValidationError as exc:
            raise ServiceAccountCatalogError(f"Invalid service-account entry: {entry}") from exc

        if definition.account in definitions:
            raise ServiceAccountCatalogError(
                f"Duplicate service-account '{definition.account}' detected."
            )

        definitions[definition.account] = definition

    if not definitions:
        raise ServiceAccountCatalogError("Service-account catalog must contain at least one entry.")

    return ServiceAccountRegistry(definitions)


@lru_cache
def get_default_service_account_registry() -> ServiceAccountRegistry:
    """Shared cached registry using the default catalog path."""

    return load_service_account_registry()

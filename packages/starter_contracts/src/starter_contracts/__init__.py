"""Shared abstractions between the FastAPI app and the Agent Starter CLI."""

from .config import StarterSettingsProtocol, get_settings

__all__ = ["StarterSettingsProtocol", "get_settings"]

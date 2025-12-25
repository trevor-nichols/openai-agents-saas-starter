"""Core primitives shared across Starter Console layers."""

from .context import CLIContext, build_context, iter_env_files
from .exceptions import CLIError

__all__ = ["CLIContext", "CLIError", "build_context", "iter_env_files"]

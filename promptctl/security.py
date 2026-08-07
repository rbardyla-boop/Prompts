from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from .kernel import KernelError


class SecurityError(KernelError):
    """Raised when an action crosses an enforced security boundary."""


REDACTION = "[REDACTED]"


def resolve_workspace_path(workspace: Path, requested: str | Path) -> Path:
    """Resolve an untrusted relative path without allowing traversal or symlink escape."""
    workspace = workspace.resolve(strict=True)
    value = Path(requested)
    if value.is_absolute():
        raise SecurityError("absolute paths are forbidden")
    if any(part == ".." for part in value.parts):
        raise SecurityError("path traversal is forbidden")

    candidate = workspace / value
    parent = candidate.parent.resolve(strict=True)
    try:
        parent.relative_to(workspace)
    except ValueError as exc:
        raise SecurityError("path parent escapes workspace") from exc

    if candidate.exists() or candidate.is_symlink():
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(workspace)
        except ValueError as exc:
            raise SecurityError("symlink escape is forbidden") from exc
        return resolved

    return parent / candidate.name


def redact_text(text: str, secrets: Iterable[str]) -> str:
    result = text
    ordered = sorted({secret for secret in secrets if secret}, key=len, reverse=True)
    for secret in ordered:
        result = result.replace(secret, REDACTION)
    return result


def redact_value(value: Any, secrets: Iterable[str]) -> Any:
    secret_list = tuple(secret for secret in secrets if secret)
    if isinstance(value, str):
        return redact_text(value, secret_list)
    if isinstance(value, list):
        return [redact_value(item, secret_list) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item, secret_list) for item in value)
    if isinstance(value, dict):
        return {
            redact_text(str(key), secret_list): redact_value(item, secret_list)
            for key, item in value.items()
        }
    return value


def environment_secrets(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(value for name in names if (value := os.environ.get(name)))


def authorize_closed_action(action: str, allowed: Iterable[str], forbidden: Iterable[str]) -> None:
    allowed_set = set(allowed)
    forbidden_set = set(forbidden)
    if action in forbidden_set:
        raise SecurityError(f"forbidden action: {action}")
    if action not in allowed_set:
        raise SecurityError(f"unlisted action denied: {action}")

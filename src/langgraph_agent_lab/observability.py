"""Optional LangSmith tracing helpers."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

F = TypeVar("F", bound=Callable[..., object])
_ENV_LOADED = False
_PLACEHOLDER_VALUES = {"", "lsv2_pt_...", "PASTE_LANGSMITH_API_KEY_HERE"}


def load_env_file() -> None:
    """Load simple KEY=VALUE pairs from .env without printing secrets."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def _usable_api_key() -> bool:
    key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY") or ""
    return key.strip() not in _PLACEHOLDER_VALUES


def configure_langsmith() -> None:
    """Normalize LangSmith and legacy LangChain tracing environment variables."""
    load_env_file()

    pairs = [
        ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
        ("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT"),
    ]
    for langsmith_key, langchain_key in pairs:
        langsmith_value = os.getenv(langsmith_key)
        langchain_value = os.getenv(langchain_key)
        if langsmith_value and not langchain_value:
            os.environ[langchain_key] = langsmith_value
        elif langchain_value and not langsmith_value:
            os.environ[langsmith_key] = langchain_value

    tracing_requested = (
        os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        or os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    )
    tracing_enabled = tracing_requested and _usable_api_key()
    os.environ["LANGSMITH_TRACING"] = "true" if tracing_enabled else "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_enabled else "false"


def langsmith_project_name() -> str:
    """Return the configured project name without exposing API keys."""
    configure_langsmith()
    return os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "not configured"


try:
    from langsmith import traceable as _traceable
except Exception:

    def traceable(*_args: object, **_kwargs: object) -> Callable[[F], F]:
        """Fallback decorator used when langsmith is not installed."""

        def decorator(func: F) -> F:
            return func

        return decorator
else:
    traceable = _traceable

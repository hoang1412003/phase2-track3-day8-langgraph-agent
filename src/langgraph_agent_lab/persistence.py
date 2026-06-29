"""Checkpointer adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def build_checkpointer(kind: str = "memory", database_url: str | None = None) -> object | None:
    """Return a LangGraph checkpointer."""
    if kind == "none":
        return None
    if kind == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if kind == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_path = database_url or "outputs/langgraph_checkpoints.sqlite"
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return SqliteSaver(conn=conn)
    if kind == "postgres":
        raise NotImplementedError("Postgres checkpointer is optional and not enabled in this lab")
    raise ValueError(f"Unknown checkpointer kind: {kind}")

"""Routing functions for conditional edges."""

from __future__ import annotations

from .state import AgentState


def route_after_classify(state: AgentState) -> str:
    """Map classified workflow route to the next graph node."""
    route = str(state.get("route", "")).lower()
    return {
        "simple": "answer",
        "tool": "tool",
        "missing_info": "clarify",
        "risky": "risky_action",
    }.get(route, "answer")


def route_after_evaluate(state: AgentState) -> str:
    """Route failed tool results back into the retry loop."""
    return "retry" if state.get("evaluation_result") == "needs_retry" else "answer"


def route_after_retry(state: AgentState) -> str:
    """Retry while attempt is below max_attempts; otherwise dead-letter."""
    attempt = int(state.get("attempt", 0))
    max_attempts = int(state.get("max_attempts", 3))
    return "tool" if attempt < max_attempts else "dead_letter"


def route_after_approval(state: AgentState) -> str:
    """Approved or edited actions may use tools; rejected actions ask for clarification."""
    approval = state.get("approval") or {}
    return "tool" if bool(approval.get("approved")) else "clarify"

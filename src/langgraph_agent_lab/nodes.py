"""Node functions for the LangGraph workflow."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

from .llm import get_llm
from .observability import traceable
from .state import AgentState, ApprovalDecision, make_error, make_event

RouteName = Literal["simple", "tool", "missing_info", "risky"]


class ClassificationResult(BaseModel):
    route: RouteName = Field(description="Best route for the support request")
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Operational risk level"
    )
    rationale: str = Field(description="Short reason for the route")


def _safe_metadata(state: AgentState) -> dict[str, object]:
    approval = state.get("approval") or {}
    return {
        "scenario_id": state.get("scenario_id", "unknown"),
        "route": state.get("route", ""),
        "attempt": state.get("attempt", 0),
        "evaluation_result": state.get("evaluation_result", ""),
        "approval_action": approval.get("action") if isinstance(approval, dict) else None,
        "approval_approved": approval.get("approved") if isinstance(approval, dict) else None,
    }


def _audit(
    node: str,
    event_type: str,
    message: str,
    **metadata: object,
) -> dict[str, object]:
    return make_event(node, event_type, message, **metadata)


def _visited(node: str, event: dict[str, object]) -> dict[str, object]:
    return {
        "nodes_visited": [node],
        "events": [event],
        "audit_events": [event],
    }


def _message_content(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(part) for part in content)
    return str(content)


def _fallback_classify(query: str) -> ClassificationResult:
    text = query.lower()
    risky_terms = ["refund", "delete", "cancel", "send confirmation", "email"]
    error_terms = ["timeout", "failure", "failed", "crash", "system error", "cannot recover"]
    vague_terms = ["fix it", "help me", "can you fix"]

    if any(word in text for word in risky_terms):
        return ClassificationResult(
            route="risky",
            risk_level="high",
            rationale="Side-effecting action",
        )
    if any(word in text for word in ["lookup", "order", "status", "tracking", "search"]):
        return ClassificationResult(
            route="tool",
            risk_level="low",
            rationale="Needs lookup tool",
        )
    if any(word in text for word in error_terms):
        return ClassificationResult(
            route="tool",
            risk_level="medium",
            rationale="Needs diagnostic tool; errors are handled at runtime",
        )
    if len(text.split()) <= 4 or any(phrase in text for phrase in vague_terms):
        return ClassificationResult(
            route="missing_info",
            risk_level="low",
            rationale="Missing actionable details",
        )
    return ClassificationResult(
        route="simple",
        risk_level="low",
        rationale="General support question",
    )


def intake_node(state: AgentState) -> dict[str, object]:
    """Normalize raw query."""
    query = state.get("query", "").strip()
    event = _audit(
        "intake",
        "completed",
        "query normalized",
        query_preview=query[:80],
        **_safe_metadata(state),
    )
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        **_visited("intake", event),
    }


@traceable(name="classify_node", run_type="chain")
def classify_node(state: AgentState) -> dict[str, object]:
    """Classify the query into a route using LLM structured output."""
    query = state.get("query", "")
    prompt = f"""
You are routing a customer support ticket. Return exactly one route.

Route definitions and priority:
1. risky: side effects such as refund, delete, cancel, send email, account changes.
2. tool: lookup/search/order/tracking/status requests that need external data.
3. missing_info: vague or incomplete requests without enough context.
4. simple: general support questions answerable without tools.

Runtime failures are not routes. If a ticket mentions timeout, crash, failure,
or recovery diagnostics, choose tool so tool/evaluate/retry handles the error.

Classify this ticket:
{query}
""".strip()
    try:
        classifier = get_llm(temperature=0).with_structured_output(ClassificationResult)
        result = classifier.invoke(prompt)
    except Exception as exc:
        result = _fallback_classify(query)
        event = _audit(
            "classify",
            "completed_with_fallback",
            "LLM classification failed; used fallback classifier",
            route=result.route,
            error_type=type(exc).__name__,
            **_safe_metadata(state),
        )
        return {
            "route": result.route,
            "risk_level": result.risk_level,
            "errors": [
                make_error(
                    "llm_classification_error",
                    str(exc),
                    "classify",
                    retryable=True,
                )
            ],
            "messages": [f"classify:{result.route}:{result.rationale}"],
            **_visited("classify", event),
        }

    event = _audit(
        "classify",
        "completed",
        result.rationale,
        classified_route=result.route,
        risk_level=result.risk_level,
        **_safe_metadata(state),
    )
    return {
        "route": result.route,
        "risk_level": result.risk_level,
        "messages": [f"classify:{result.route}:{result.rationale}"],
        **_visited("classify", event),
    }


@traceable(name="tool_node", run_type="tool")
def tool_node(state: AgentState) -> dict[str, object]:
    """Execute a mock tool call with deterministic transient failures."""
    route = state.get("route", "")
    attempt = int(state.get("attempt", 0))
    query = state.get("query", "")

    runtime_error_terms = ["timeout", "failure", "failed", "crash", "cannot recover"]
    should_simulate_error = any(term in query.lower() for term in runtime_error_terms)

    if should_simulate_error and attempt < 2:
        result = f"ERROR transient support backend timeout on attempt {attempt}: {query}"
        event = _audit(
            "tool",
            "failed",
            "mock tool returned transient error",
            **_safe_metadata(state),
        )
        return {
            "tool_results": [result],
            "errors": [
                make_error("tool_timeout", result, "tool", retryable=True, attempt=attempt)
            ],
            **_visited("tool", event),
        }

    if route == "risky":
        approval = state.get("approval") or {}
        action = approval.get("edited_action") or state.get("proposed_action") or query
        result = f"SUCCESS approved action prepared for execution: {action}"
    elif route == "tool":
        result = "SUCCESS order lookup result: order is in progress. " f"Query: {query}"
    else:
        result = f"SUCCESS diagnostic lookup completed for query: {query}"

    event = _audit(
        "tool",
        "completed",
        "mock tool completed",
        **_safe_metadata(state),
    )
    return {"tool_results": [result], **_visited("tool", event)}


@traceable(name="evaluate_node", run_type="chain")
def evaluate_node(state: AgentState) -> dict[str, object]:
    """Evaluate latest tool result and decide whether retry is needed."""
    latest = (state.get("tool_results") or [""])[-1]
    evaluation = "needs_retry" if "ERROR" in latest.upper() else "success"
    event = _audit(
        "evaluate",
        "completed",
        f"tool evaluation: {evaluation}",
        next_evaluation_result=evaluation,
        **_safe_metadata(state),
    )
    return {
        "evaluation_result": evaluation,
        "messages": [f"evaluate:{evaluation}"],
        **_visited("evaluate", event),
    }


@traceable(name="answer_node", run_type="chain")
def answer_node(state: AgentState) -> dict[str, object]:
    """Generate a grounded final response using the configured LLM."""
    query = state.get("query", "")
    tool_results = state.get("tool_results", []) or []
    approval = state.get("approval")
    prompt = f"""
You are a concise customer support agent. Answer the user using only the available context.
Do not claim that an external action has been completed unless the context says SUCCESS.

User query: {query}
Route: {state.get("route", "")}
Approval decision: {approval}
Tool results: {tool_results}
""".strip()
    try:
        response = get_llm(temperature=0.2).invoke(prompt)
        final_answer = _message_content(response).strip()
    except Exception as exc:
        context = tool_results[-1] if tool_results else "No tool result was needed."
        final_answer = f"I reviewed your request. Context: {context}"
        event = _audit(
            "answer",
            "completed_with_fallback",
            "LLM answer failed; used grounded fallback",
            error_type=type(exc).__name__,
            **_safe_metadata(state),
        )
        return {
            "final_answer": final_answer,
            "errors": [
                make_error("llm_answer_error", str(exc), "answer", retryable=True)
            ],
            "messages": ["answer:fallback"],
            **_visited("answer", event),
        }

    event = _audit(
        "answer",
        "completed",
        "grounded response generated",
        **_safe_metadata(state),
    )
    return {
        "final_answer": final_answer,
        "messages": ["answer:llm"],
        **_visited("answer", event),
    }


def ask_clarification_node(state: AgentState) -> dict[str, object]:
    """Ask for missing information instead of hallucinating."""
    query = state.get("query", "")
    if state.get("approval") and not (state.get("approval") or {}).get("approved", False):
        question = (
            "The requested action was not approved. "
            "What safer alternative would you like me to help with?"
        )
    else:
        question = (
            "Could you share more details about what needs to be fixed or the "
            f"account/order involved? Original request: {query}"
        )
    event = _audit(
        "clarify",
        "completed",
        "clarification requested",
        **_safe_metadata(state),
    )
    return {
        "pending_question": question,
        "final_answer": question,
        "messages": ["clarify:pending_question"],
        **_visited("clarify", event),
    }


def risky_action_node(state: AgentState) -> dict[str, object]:
    """Prepare a risky action for approval before any tool runs."""
    query = state.get("query", "")
    proposed = f"Review and approve before executing this side-effecting request: {query}"
    event = _audit(
        "risky_action",
        "completed",
        "risky action prepared for approval",
        proposed_action_preview=proposed[:120],
        **_safe_metadata(state),
    )
    return {
        "proposed_action": proposed,
        "messages": ["risky_action:approval_required"],
        **_visited("risky_action", event),
    }


@traceable(name="approval_node", run_type="chain")
def approval_node(state: AgentState) -> dict[str, object]:
    """Human-in-the-loop approval step with mock approve/reject/edit support."""
    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() == "true":
        try:
            from langgraph.types import interrupt

            payload = interrupt(
                {
                    "proposed_action": state.get("proposed_action"),
                    "allowed_actions": ["approve", "reject", "edit"],
                }
            )
            if isinstance(payload, dict):
                action = str(payload.get("action", "approve")).lower()
                edited_action = payload.get("edited_action")
            else:
                action = "approve"
                edited_action = None
        except Exception:
            action = "approve"
            edited_action = None
    else:
        action = os.getenv("APPROVAL_ACTION", "approve").lower()
        edited_action = os.getenv("APPROVAL_EDITED_ACTION") or None

    if action not in {"approve", "reject", "edit"}:
        action = "approve"
    approved = action in {"approve", "edit"}
    decision = ApprovalDecision(
        approved=approved,
        reviewer="mock-reviewer",
        comment=f"Mock HITL decision: {action}",
        action=action,
        edited_action=edited_action if action == "edit" else None,
    ).model_dump()
    metadata = _safe_metadata(state)
    metadata.update({"approval_action": action, "approval_approved": approved})
    event = _audit(
        "approval",
        "completed",
        "approval decision recorded",
        **metadata,
    )
    return {
        "approval": decision,
        "messages": [f"approval:{action}"],
        **_visited("approval", event),
    }


@traceable(name="retry_or_fallback_node", run_type="chain")
def retry_or_fallback_node(state: AgentState) -> dict[str, object]:
    """Increment retry attempt and record the transient failure."""
    next_attempt = int(state.get("attempt", 0)) + 1
    message = f"Retry attempt {next_attempt} of {state.get('max_attempts', 3)}"
    event = _audit(
        "retry",
        "completed",
        message,
        next_attempt=next_attempt,
        **_safe_metadata(state),
    )
    return {
        "attempt": next_attempt,
        "errors": [
            make_error(
                "retry_scheduled",
                message,
                "retry",
                retryable=True,
                attempt=next_attempt,
            )
        ],
        "messages": [f"retry:{next_attempt}"],
        **_visited("retry", event),
    }


def dead_letter_node(state: AgentState) -> dict[str, object]:
    """Handle unresolvable failures after max retries are exceeded."""
    answer = (
        "The request could not be completed after the allowed retry attempts. "
        "I have moved it to escalation for manual support review."
    )
    event = _audit(
        "dead_letter",
        "completed",
        "max retries exceeded",
        **_safe_metadata(state),
    )
    return {
        "final_answer": answer,
        "errors": [
            make_error(
                "dead_letter",
                "Max retry attempts exceeded",
                "dead_letter",
                retryable=False,
                attempt=state.get("attempt", 0),
                max_attempts=state.get("max_attempts", 3),
            )
        ],
        "messages": ["dead_letter:escalated"],
        **_visited("dead_letter", event),
    }


def finalize_node(state: AgentState) -> dict[str, object]:
    """Emit a final audit event before END."""
    event = _audit(
        "finalize",
        "completed",
        "workflow finished",
        **_safe_metadata(state),
    )
    return {"messages": ["finalize:done"], **_visited("finalize", event)}

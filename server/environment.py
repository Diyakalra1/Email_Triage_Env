"""Inbox environment implementation."""

from __future__ import annotations

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

try:
    from ..models import InboxAction, InboxObservation, InboxState
    from .generator import generate_inbox
    from .graders import grade_task1, grade_task2, grade_task3
except ImportError:
    from models import InboxAction, InboxObservation, InboxState
    from server.generator import generate_inbox
    from server.graders import grade_task1, grade_task2, grade_task3


class InboxEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    MAX_STEPS: int = 25

    def __init__(self):
        self._state = InboxState(task_id="1", episode_id=str(uuid4()), step_count=0)
        self._inbox: list[dict[str, str]] = []
        self._history: list[dict[str, str]] = []
        self._done = False
        self._score = 0.0

    def _summary(self) -> list[dict[str, str]]:
        summary = []
        for e in self._inbox:
            snippet = e["body"][:80] + ("..." if len(e["body"]) > 80 else "")
            summary.append({"id": e["id"], "from_addr": e["from_addr"], "subject": e["subject"], "snippet": snippet})
        return summary

    def _find_email(self, email_id: str) -> dict[str, str] | None:
        for item in self._inbox:
            if item["id"] == email_id:
                return item
        return None

    def reset(self, seed: int = 0, task_id: str = "1", episode_id: str | None = None) -> InboxObservation:  # type: ignore[override]
        self._state = InboxState(task_id=task_id, episode_id=episode_id or str(uuid4()), step_count=0)
        self._inbox = generate_inbox(seed)
        self._history = []
        self._done = False
        self._score = 0.0
        return InboxObservation(
            inbox_summary=self._summary(),
            email_body=None,
            action_result="Environment reset complete.",
            step_count=0,
            budget_remaining=self.MAX_STEPS,
        )

    def _task_score(self) -> float:
        gold = {e["id"]: e for e in self._inbox}
        task = self._state.task_id
        if task == "1":
            return grade_task1(self._history, gold)
        if task == "2":
            return grade_task2(self._history, gold)
        return grade_task3(self._history, gold)

    def step(self, action: InboxAction) -> InboxObservation:  # type: ignore[override]
        if self._done:
            return InboxObservation(
                inbox_summary=self._summary(),
                email_body=None,
                action_result="Episode already finished.",
                step_count=self._state.step_count,
                budget_remaining=max(0, self.MAX_STEPS - self._state.step_count),
                reward=0.0,
                done=True,
            )

        self._state.step_count += 1
        act = action.action_type
        result = ""
        email_body = None

        if act == "done":
            self._done = True
            result = "Agent finished episode."
        else:
            email = self._find_email(action.email_id)
            if email is None:
                result = f"Email '{action.email_id}' not found."
            elif act == "read":
                email_body = email["body"]
                result = f"Read {action.email_id}."
            elif act == "label":
                result = f"Labeled {action.email_id} as {action.value or 'unknown'}."
            elif act == "reply":
                result = f"Replied to {action.email_id}."
            elif act == "route":
                result = f"Routed {action.email_id} to {action.value or 'unknown'}."
            elif act == "delete":
                result = f"Deleted {action.email_id}."
            else:
                result = f"Unsupported action '{act}'."

        self._history.append(
            {
                "action_type": act,
                "email_id": action.email_id,
                "value": action.value or "",
                "step": str(self._state.step_count),
            }
        )

        if self._state.step_count >= self.MAX_STEPS:
            self._done = True
            result = f"{result} Budget exhausted."

        self._score = self._task_score() if self._done else 0.0
        return InboxObservation(
            inbox_summary=self._summary(),
            email_body=email_body,
            action_result=result,
            step_count=self._state.step_count,
            budget_remaining=max(0, self.MAX_STEPS - self._state.step_count),
            reward=self._score if self._done else 0.0,
            done=self._done,
        )

    @property
    def state(self) -> InboxState:
        return self._state

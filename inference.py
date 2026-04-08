"""Inference runner for inbox_env with required stdout format."""

from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from client import InboxEnv
from models import InboxAction

BENCHMARK = "inbox_env"
SYSTEM_PROMPT = (
    "You are an email triage agent. Always return strict JSON only with this schema: "
    '{"action":"label","email_id":"e3","value":"urgent"}. '
    "Allowed actions: read,label,reply,route,delete,done. "
    "Do not repeat the same action on the same email unless new information requires it. "
    "Prefer reading unseen emails first, then label/route/reply/delete. "
    "Use done only when the budget is low or triage decisions are complete."
)


def _to_bool_str(value: bool) -> str:
    return "true" if value else "false"


def _parse_action(raw: str) -> InboxAction:
    try:
        data = json.loads(raw)
        return InboxAction(
            action_type=data.get("action", "done"),
            email_id=data.get("email_id", ""),
            value=data.get("value"),
        )
    except Exception:
        return InboxAction(action_type="done", email_id="", value=None)


def _safe_action(action: InboxAction, inbox_ids: list[str]) -> InboxAction:
    if action.action_type == "done":
        return action
    if action.email_id in inbox_ids:
        return action
    if not inbox_ids:
        return InboxAction(action_type="done", email_id="", value=None)
    return InboxAction(action_type="read", email_id=inbox_ids[0], value=None)


def _fallback_action(task_id: str, inbox_ids: list[str], seen_reads: set[str], labeled: set[str], routed: set[str]) -> InboxAction:
    remaining = [eid for eid in inbox_ids if eid not in seen_reads]
    if remaining:
        return InboxAction(action_type="read", email_id=remaining[0], value=None)

    if task_id == "1":
        unlabeled = [eid for eid in inbox_ids if eid not in labeled]
        if unlabeled:
            return InboxAction(action_type="label", email_id=unlabeled[0], value="normal")
    elif task_id == "2":
        unlabeled = [eid for eid in inbox_ids if eid not in labeled]
        if unlabeled:
            return InboxAction(action_type="label", email_id=unlabeled[0], value="high")
        return InboxAction(action_type="reply", email_id=inbox_ids[0] if inbox_ids else "", value="Thanks, we are looking into this.")
    else:
        unrouted = [eid for eid in inbox_ids if eid not in routed]
        if unrouted:
            return InboxAction(action_type="route", email_id=unrouted[0], value="support-tier1")

    return InboxAction(action_type="done", email_id="", value=None)


def _log_start(task: str, model_name: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={model_name}", flush=True)


def _log_step(step: int, action_str: str, reward: float, done: bool, error: Optional[str]) -> None:
    err = error if error else "null"
    print(
        f"[STEP]  step={step} action={action_str} reward={reward:.2f} done={_to_bool_str(done)} error={err}",
        flush=True,
    )


def _log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={_to_bool_str(success)} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def _run_task(env_base_url: str, client: OpenAI, model_name: str, task_id: str, seed: int) -> None:
    _log_start(task_id, model_name)
    rewards: list[float] = []
    steps = 0
    score = 0.0
    success = False
    try:
        with InboxEnv(base_url=env_base_url).sync() as env:
            result = env.reset(seed=seed, task_id=task_id, episode_id=f"task{task_id}-seed{seed}")
            done = bool(result.done)
            seen_reads: set[str] = set()
            labeled: set[str] = set()
            routed: set[str] = set()
            last_action_key = ""
            repeated_action_count = 0
            while not done:
                obs = result.observation
                inbox_ids = [item.get("id", "") for item in obs.inbox_summary if item.get("id")]
                payload = {
                    "task_id": task_id,
                    "step_count": obs.step_count,
                    "budget_remaining": obs.budget_remaining,
                    "inbox_summary": obs.inbox_summary,
                    "action_result": obs.action_result,
                    "email_body": obs.email_body,
                    "guidance": {
                        "already_read": sorted(seen_reads),
                        "already_labeled": sorted(labeled),
                        "already_routed": sorted(routed),
                    },
                }
                error: Optional[str] = None
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": json.dumps(payload)},
                        ],
                        temperature=0.0,
                        max_tokens=200,
                    )
                    raw = completion.choices[0].message.content or '{"action":"done","email_id":"","value":null}'
                except Exception as exc:
                    raw = '{"action":"done","email_id":"","value":null}'
                    error = str(exc)

                action = _safe_action(_parse_action(raw), inbox_ids)
                action_key = f"{action.action_type}:{action.email_id}:{action.value}"
                if action_key == last_action_key:
                    repeated_action_count += 1
                else:
                    repeated_action_count = 0
                last_action_key = action_key

                if repeated_action_count >= 2:
                    # Guardrail against loops when model repeats an ineffective move.
                    action = _fallback_action(task_id, inbox_ids, seen_reads, labeled, routed)
                    action_key = f"{action.action_type}:{action.email_id}:{action.value}"
                    repeated_action_count = 0

                action_str = json.dumps(
                    {"action": action.action_type, "email_id": action.email_id, "value": action.value},
                    separators=(",", ":"),
                )
                result = env.step(action)
                if action.action_type == "read" and action.email_id:
                    seen_reads.add(action.email_id)
                if action.action_type == "label" and action.email_id:
                    labeled.add(action.email_id)
                if action.action_type == "route" and action.email_id:
                    routed.add(action.email_id)
                done = bool(result.done)
                reward = float(result.reward or 0.0)
                steps = int(result.observation.step_count)
                rewards.append(reward)
                _log_step(steps, action_str, reward, done, error)

            score = float(result.reward or 0.0)
            score = max(0.0, min(1.0, score))
            success = score >= 0.7
    except Exception:
        # Episode failed (e.g. env unreachable); [END] still emitted in finally.
        pass
    finally:
        _log_end(success, steps, score, rewards)


def main() -> None:
    api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    env_base_url = os.getenv("ENV_BASE_URL", "http://localhost:8000")
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    hf_token = os.environ["HF_TOKEN"]
    LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
    _ = LOCAL_IMAGE_NAME
    llm = OpenAI(base_url=api_base_url, api_key=hf_token)

    _run_task(env_base_url, llm, model_name, task_id="1", seed=11)
    _run_task(env_base_url, llm, model_name, task_id="2", seed=22)
    _run_task(env_base_url, llm, model_name, task_id="3", seed=33)


if __name__ == "__main__":
    main()

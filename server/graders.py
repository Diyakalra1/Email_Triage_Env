"""Task graders for inbox triage."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics import f1_score
from sklearn.metrics.pairwise import cosine_similarity

_EMBEDDER: SentenceTransformer | None = None


def _model() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDER


def _clip(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


def _priority_f1(history: list[dict[str, Any]], gold: dict[str, dict[str, str]], weighted: bool) -> float:
    labels = []
    preds = []
    sample_weight = []
    latest_labels: dict[str, str] = {}
    for event in history:
        if event.get("action_type") == "label":
            eid = event.get("email_id", "")
            latest_labels[eid] = event.get("value", "")

    for eid, truth in gold.items():
        labels.append(truth.get("true_priority", "normal"))
        preds.append(latest_labels.get(eid, "normal"))
        w = 3.0 if truth.get("true_priority") == "urgent" else 1.0
        sample_weight.append(w if weighted else 1.0)

    if not labels:
        return 0.0
    return _clip(f1_score(labels, preds, average="macro", sample_weight=sample_weight))


def _reply_similarity(history: list[dict[str, Any]], gold: dict[str, dict[str, str]]) -> float:
    replies: dict[str, str] = {}
    for event in history:
        if event.get("action_type") == "reply":
            replies[event.get("email_id", "")] = event.get("value", "")

    pairs: list[tuple[str, str]] = []
    for eid, row in gold.items():
        target_type = row.get("true_type")
        if target_type in {"support", "billing", "legal", "hr"}:
            reference = f"A helpful {target_type} response for: {row.get('subject', '')}"
            candidate = replies.get(eid, "")
            if candidate:
                pairs.append((candidate, reference))

    if not pairs:
        return 0.0

    m = _model()
    cand_vec = m.encode([p[0] for p in pairs])
    ref_vec = m.encode([p[1] for p in pairs])
    sims = cosine_similarity(cand_vec, ref_vec).diagonal()
    return _clip(float(sims.mean()))


def grade_task1(history: list[dict[str, Any]], gold: dict[str, dict[str, str]]) -> float:
    """Weighted F1 on priority labels with urgent errors weighted 3x."""
    return _priority_f1(history, gold, weighted=True)


def grade_task2(history: list[dict[str, Any]], gold: dict[str, dict[str, str]]) -> float:
    """50% priority F1 + 50% semantic reply quality."""
    p = _priority_f1(history, gold, weighted=False)
    r = _reply_similarity(history, gold)
    return _clip(0.5 * p + 0.5 * r)


def grade_task3(history: list[dict[str, Any]], gold: dict[str, dict[str, str]]) -> float:
    """Composite score: routing + SLA bonus + spam + reply quality."""
    routed = {}
    deleted_spam = set()
    reply_count = defaultdict(int)
    steps = max(1, len(history))

    for event in history:
        act = event.get("action_type")
        eid = event.get("email_id", "")
        if act == "route":
            routed[eid] = event.get("value", "")
        elif act == "delete":
            deleted_spam.add(eid)
        elif act == "reply":
            reply_count[eid] += 1

    total = max(1, len(gold))
    route_hits = sum(1 for eid, row in gold.items() if routed.get(eid) == row.get("true_team"))
    routing_accuracy = route_hits / total

    spam_gold = {eid for eid, row in gold.items() if row.get("true_type") == "spam"}
    spam_detect = (len(spam_gold & deleted_spam) / max(1, len(spam_gold)))

    urgent_ids = {eid for eid, row in gold.items() if row.get("true_priority") == "urgent"}
    touched_urgent = {
        e.get("email_id", "")
        for e in history
        if e.get("email_id") in urgent_ids and e.get("action_type") in {"read", "label", "reply", "route"}
    }
    sla_bonus = len(touched_urgent) / max(1, len(urgent_ids))
    if steps <= 20:
        sla_bonus = min(1.0, sla_bonus + 0.1)

    reply_quality = _reply_similarity(history, gold)
    return _clip(0.35 * routing_accuracy + 0.2 * sla_bonus + 0.2 * spam_detect + 0.25 * reply_quality)

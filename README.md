---
title: Inbox Triage Environment
emoji: 📬
colorFrom: yellow
colorTo: pink
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# Inbox Triage Environment

A deterministic email triage benchmark for OpenEnv. The environment simulates a mixed inbox (support, billing, legal, HR, spam) and scores agents on prioritization, response quality, and full operational routing.

## Motivation

Real operations teams triage noisy inboxes under time limits. This environment provides reproducible episodes (seeded generation) so different agent strategies can be compared fairly.

## Action Space

`InboxAction` supports 6 actions:

- `read(email_id)` – reveal full email body
- `label(email_id, value)` – assign priority label
- `reply(email_id, value)` – send response text
- `route(email_id, value)` – send to team
- `delete(email_id)` – remove irrelevant/spam email
- `done()` – finish episode explicitly

## Observation Space

`InboxObservation` fields:

- `inbox_summary` – list of `{id, from_addr, subject, snippet}`
- `email_body` – full body only after `read`
- `action_result` – text feedback from last action
- `step_count` – current step index
- `budget_remaining` – steps left (max 25)
- `reward` and `done` – standard OpenEnv fields

## Tasks

### Task 1 (Priority Classification)
- Goal: assign priorities accurately.
- Metric: weighted priority F1 (urgent errors weighted 3x).
- Difficulty: medium.

### Task 2 (Priority + Reply)
- Goal: classify priority and produce quality replies.
- Metric: `0.5 * priority_f1 + 0.5 * reply_cosine_similarity`.
- Difficulty: medium-hard.

### Task 3 (Full Triage)
- Goal: route correctly, detect spam, respond with urgency.
- Metric: weighted composite of routing accuracy, SLA bonus, spam detection, and reply quality.
- Difficulty: hard.

## Setup

```bash
# Validate structure/spec
openenv validate

# Run local server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Inference

`inference.py` is required at project root and uses the OpenAI client interface.

Environment variables:

- `API_BASE_URL` (LLM endpoint, default `https://router.huggingface.co/v1`)
- `ENV_BASE_URL` (environment endpoint, e.g. your HF Space URL)
- `MODEL_NAME` (model id)
- `HF_TOKEN` (API token)

Run:

```bash
python inference.py
```

The script emits required stdout records:

- `[START] task=... env=... model=...`
- `[STEP] step=... action=... reward=... done=... error=...`
- `[END] success=... steps=... score=... rewards=...`

## Deployment

```bash
openenv push --repo-id <username>/inbox-env
```

After deploy:
- Health: `https://<username>-inbox-env.hf.space/health`
- API docs: `https://<username>-inbox-env.hf.space/docs`

## Baseline Scores (Example)

| Task | Score |
|---|---|
| Task 1 | 0.09 |
| Task 2 | 0.06 |
| Task 3 | 0.02 |

## Notes and Limitations

- Low scores above were collected under free-tier inference quota constraints.
- If provider credits are exhausted, `inference.py` logs the raw API error and falls back safely, still emitting valid stdout format.

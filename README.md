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

# Docker image (required by course pre-submission script; run where Docker is installed)
docker build -f server/Dockerfile .

# Run local server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Pre-submission checklist

1. `openenv validate` passes.
2. `docker build -f server/Dockerfile .` succeeds (2 vCPU / 8 GB builder or CI).
3. HF Space `/health` returns 200; `/reset` works as documented.
4. Set Space/repository secrets: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` (and `ENV_BASE_URL` for local inference against the Space).
5. Run `python inference.py` with a working LLM and live `ENV_BASE_URL`; exit code 0; update the baseline table below with captured scores.
6. Push to GitHub and resubmit through the course flow.

## Inference

`inference.py` is required at project root and uses the OpenAI client interface.

Environment variables:

- `API_BASE_URL` — OpenAI-compatible **LLM** endpoint (default `https://router.huggingface.co/v1`)
- `MODEL_NAME` — chat model id (default `Qwen/Qwen2.5-72B-Instruct`)
- `HF_TOKEN` — **required** API key (no default)
- `ENV_BASE_URL` — OpenEnv **server** base URL for `InboxEnv` (WebSocket + HTTP). For a Hugging Face Space named `inbox-env` under user `myuser`, use `https://myuser-inbox-env.hf.space` (HTTPS scheme, no trailing slash). Graders typically set this to your deployed Space URL. Local default is `http://localhost:8000` if unset.
- `LOCAL_IMAGE_NAME` — optional; only if you use `from_docker_image()` (not used by this script’s default path)

Run (example with live Space):

```bash
export ENV_BASE_URL="https://<owner>-<space>.hf.space"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="hf_..."
python inference.py
```

The script emits required stdout records (see course sample for strict field order). Each episode prints `[END]` even if the environment client fails to connect (e.g. wrong `ENV_BASE_URL`).

- `[START] task=... env=inbox_env model=...`
- `[STEP]  step=... action=... reward=... done=... error=...` (two spaces after `[STEP]` per sample)
- `[END] success=... steps=... score=... rewards=...`

## Deployment

```bash
openenv push --repo-id <username>/inbox-env
```

After deploy:
- Health: `https://<username>-inbox-env.hf.space/health`
- API docs: `https://<username>-inbox-env.hf.space/docs`

## Baseline Scores (Example)

Replace this table after a successful full run against your deployed Space and working inference quota.

| Task | Score |
|---|---|
| Task 1 | *run inference.py and paste* |
| Task 2 | *run inference.py and paste* |
| Task 3 | *run inference.py and paste* |

## Notes and Limitations

- Previous example scores (~0.09 / 0.06 / 0.02) were collected under free-tier inference quota constraints.
- If provider credits are exhausted, step logs include the API error in `error=`; the script still completes all three tasks with exit code 0 when the environment is reachable.
- **HF Space:** connect the Space to this GitHub repo (or redeploy with `openenv push`) so automated health/reset checks match the submitted revision.

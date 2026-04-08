# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Typed client for inbox_env."""

from typing import Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from models import InboxAction, InboxObservation, InboxState


class InboxEnv(EnvClient[InboxAction, InboxObservation, InboxState]):

    def _step_payload(self, action: InboxAction) -> dict[str, Any]:
        return {
            "action_type": action.action_type,
            "email_id": action.email_id,
            "value": action.value,
        }

    def _parse_result(self, payload: dict[str, Any]) -> StepResult[InboxObservation]:
        obs_data = payload.get("observation", {})
        observation = InboxObservation(
            inbox_summary=obs_data.get("inbox_summary", []),
            email_body=obs_data.get("email_body"),
            action_result=obs_data.get("action_result", ""),
            step_count=obs_data.get("step_count", 0),
            budget_remaining=obs_data.get("budget_remaining", 0),
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict[str, Any]) -> InboxState:
        return InboxState(
            task_id=payload.get("task_id", "1"),
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )

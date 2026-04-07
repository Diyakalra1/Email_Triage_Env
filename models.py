# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Inbox Env Environment.

The inbox_env environment models inbox triage actions and observations.
"""

from typing import Literal

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class InboxAction(Action):
    """Action schema for inbox triage operations."""

    action_type: Literal["read", "label", "reply", "route", "delete", "done"] = Field(
        ...,
        description="Type of action to execute.",
    )
    email_id: str = Field(
        default="",
        description="Target email id for read/label/reply/route/delete.",
    )
    value: str | None = Field(
        default=None,
        description="Optional payload, e.g. priority label, reply text, or team name.",
    )


class InboxObservation(Observation):
    """Observation schema returned after each environment interaction."""

    inbox_summary: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of email summaries containing id, subject, and snippet.",
    )
    email_body: str | None = Field(
        default=None,
        description="Full email body when read; otherwise null.",
    )
    action_result: str = Field(
        default="",
        description="Human-readable result for the last action.",
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="Current step number in the episode.",
    )
    budget_remaining: int = Field(
        default=25,
        ge=0,
        description="Remaining action budget for this episode.",
    )


class InboxState(State):
    """State schema for checkpointing episode progress."""

    task_id: str = Field(
        default="task1",
        description="Active task identifier.",
    )
    episode_id: str = Field(
        default="",
        description="Unique episode identifier.",
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="Number of steps taken in this episode.",
    )

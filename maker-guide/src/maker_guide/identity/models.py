"""Identity service models."""

from __future__ import annotations

from dataclasses import dataclass

from maker_guide.repositories.learner import Learner


@dataclass(frozen=True, kw_only=True, slots=True)
class EnsureLearnerInput:
    """Input for ensuring a learner identity exists."""

    handle: str
    """Learner handle."""

    joined_at: str
    """ISO timestamp for when the learner first joined."""

    source: str
    """Source that requested identity creation."""

    uid: int | None = None
    """POSIX uid captured when the learner account was provisioned."""

    tagline: str | None = None
    """Optional learner profile text."""


@dataclass(frozen=True, kw_only=True, slots=True)
class EnsureLearnerResult:
    """Result of ensuring a learner identity exists."""

    learner: Learner
    """Learner row after the operation."""

    created: bool
    """Whether this call created the learner row."""

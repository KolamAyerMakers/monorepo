"""Typed curriculum catalog models and lookup helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import PurePosixPath
from typing import Literal

type ContentAudience = Literal["learner", "instructor", "slides"]
type ContentPurpose = Literal[
    "slides",
    "self-study",
    "recap",
    "quest",
    "concept",
    "command",
    "guide",
]
_COMMAND_HISTORY_NESTED_REPEAT_PATTERN = re.compile(r"\((?:\?:)?[^)]*[+*][^)]*\)[+*{]")


@dataclass(frozen=True, kw_only=True, slots=True)
class ContentReference:
    """Packaged curriculum content referenced by the typed catalog."""

    id: str
    """Stable content id used for validation and generated indexes."""
    title: str
    """Human-readable content title."""
    path: str
    """Package-relative content resource path."""
    audience: ContentAudience
    """Primary audience for this content."""
    purpose: ContentPurpose
    """Instructional purpose for this content."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Course:
    """Course definition owned by the Python curriculum catalog."""

    id: str
    """Stable course id stored in learner-state rows."""
    title: str
    """Human-readable course title."""
    tutor_system_prompt: str
    """Course-specific system prompt fragment for the LLM tutor."""
    timezone: str
    """IANA timezone used for course-local dates."""
    starts_on: date
    """First course date."""
    ends_on: date
    """Last course date."""
    sessions: tuple[Session, ...]
    """Ordered course sessions."""
    quests: tuple[Quest, ...]
    """Ordered and gated course quests."""
    tiers: tuple[Tier, ...]
    """Course tier thresholds in increasing score order."""

    def __post_init__(self) -> None:
        """Reject invalid course definitions during construction."""
        _validate_course(self)


@dataclass(frozen=True, kw_only=True, slots=True)
class Session:
    """One scheduled teaching session."""

    id: str
    """Stable session id used by quest availability gates."""
    title: str
    """Human-readable session title."""
    date: date
    """Course-local session date."""
    starts_at: datetime
    """UTC timestamp after which objective evidence is accepted."""
    introduced_commands: tuple[str, ...]
    """Commands and command-like shell forms introduced in this session."""
    introduced_skills: tuple[str, ...]
    """Skill ids introduced in this session."""
    learning_objectives: tuple[str, ...]
    """Learner-facing objectives for this session."""
    content: tuple[ContentReference, ...]
    """Live teaching and learner follow-up content for this session."""
    enrichment_skills: tuple[str, ...] = ()
    """Optional skill ids available for curious learners, not required for critical path."""
    objectives: tuple[SessionObjective, ...] = ()
    """Measurable objectives that must precede post-session quests."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SessionObjective:
    """One measurable session outcome."""

    id: str
    title: str
    validation: SessionObjectiveValidation
    prompt: str = ""


@dataclass(frozen=True, kw_only=True, slots=True)
class Hint:
    """One step in a learner-facing hint ladder."""

    level: int
    """Hint level, ordered from gentlest to most explicit."""
    text: str
    """Hint text shown to the learner."""


@dataclass(frozen=True, kw_only=True, slots=True)
class FailureFeedback:
    """Learner-facing recovery guidance for failed validation."""

    reason: str
    """Stable failure reason id emitted by deterministic validators."""
    text: str
    """Recovery guidance shown when this failure reason occurs."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Quest:
    """One learner quest definition."""

    id: str
    """Stable quest id stored in learner-state rows."""
    title: str
    """Human-readable quest title."""
    sequence: int
    """Global quest order used for deterministic current quest selection."""
    available_after_session: str
    """Session id after which this quest may be assigned."""
    story: str
    """Short narrative setup explaining why the quest matters."""
    learner_goal: str
    """Concrete learner-facing outcome for this quest."""
    prompt: str
    """Learner-facing quest prompt."""
    autonomy_checklist: tuple[str, ...]
    """Checklist learners can follow without instructor help."""
    hints: tuple[Hint, ...]
    """Ordered learner-facing hints."""
    failure_feedback: tuple[FailureFeedback, ...]
    """Deterministic failure explanations and recovery guidance."""
    docs: tuple[ContentReference, ...]
    """Learner-facing documentation for this quest."""
    required_commands: tuple[str, ...]
    """Commands and shell forms the quest expects the learner to use."""
    practiced_skills: tuple[str, ...]
    """Skill ids practiced by this quest."""
    score: int
    """Score awarded on first successful completion."""
    validation: QuestValidation
    """Typed deterministic validation rule."""
    data: QuestData | None = None
    """Optional generated per-learner data strategy."""


@dataclass(frozen=True, kw_only=True, slots=True)
class CommandHistoryValidation:
    """Validation based on recent shell command observations."""

    required_patterns: tuple[str, ...]
    """Regex patterns that must be found in command observations."""
    observed_commands: tuple[str, ...]
    """Command names and forms these patterns validate."""
    ordered: bool = False
    """Whether patterns must match distinct observations from oldest to newest."""


@dataclass(frozen=True, kw_only=True, slots=True)
class AnswerConcept:
    """One deterministic concept expected in a learner answer."""

    id: str
    """Stable concept id used in validation evidence."""
    aliases: tuple[str, ...]
    """Regex aliases that can satisfy this concept."""
    rubric: str
    """Human-readable semantic expectations for grading this concept."""
    forbidden_patterns: tuple[str, ...] = ()
    """Regexes that contradict this concept when matched."""


@dataclass(frozen=True, kw_only=True, slots=True)
class AnswerConceptAssessment:
    """Validated semantic assessment used by deterministic answer grading."""

    concept_id: str
    verdict: Literal["demonstrated", "contradicted", "not_demonstrated"]


@dataclass(frozen=True, kw_only=True, slots=True)
class InteractiveQuestionValidation:
    """Validation based on a learner answer to a deterministic question."""

    question: str
    """Question the bot asks after the learner attempts the quest."""
    required_concepts: tuple[AnswerConcept, ...]
    """Concepts that must be present in the learner answer."""


@dataclass(frozen=True, kw_only=True, slots=True)
class FileCheckValidation:
    """Validation based on learner-owned file contents."""

    path: str
    """Learner-owned path to inspect."""
    required_regex: str
    """Regex that must match the file contents."""
    forbidden_regex: str | None = None
    """Optional regex that must not match the file contents."""


@dataclass(frozen=True, kw_only=True, slots=True)
class FileMatchesPathValidation:
    """Validation based on exact byte equality with a system file."""

    path: str
    """Learner-owned path to inspect."""
    source_path: str
    """Absolute system path whose bytes must match."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UserPortFileValidation:
    """Validation based on a file containing the learner's computed service port."""

    path: str
    """Learner-owned path to inspect."""
    required_regex_template: str
    """Regex template that must match after formatting with the computed port."""
    port_formula: str = "10000+uid"
    """Formula used by deterministic service code to compute the expected port."""


@dataclass(frozen=True, kw_only=True, slots=True)
class PathExistsValidation:
    """Validation based on learner-owned path existence."""

    paths: tuple[str, ...]
    """Learner-relative or absolute paths that must exist."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ExecutablePathValidation:
    """Validation based on learner-owned executable path permissions."""

    paths: tuple[str, ...]
    """Learner-relative or absolute paths that must be executable by the owner."""


@dataclass(frozen=True, kw_only=True, slots=True)
class OwnedPathValidation:
    """Validation based on a regular path owned by the learner."""

    path: str
    """Learner-relative or absolute path that must be a learner-owned regular file."""


@dataclass(frozen=True, kw_only=True, slots=True)
class LearnerHandleQuestionValidation:
    """Validation based on the learner answering with their own handle."""

    question: str
    """Question the bot asks after the learner attempts the quest."""


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcCtcpVersionValidation:
    """Validation based on IRC CTCP VERSION evidence recorded by the bot."""

    accepted_clients: tuple[str, ...]
    """Accepted IRC client names, matched case-insensitively in CTCP VERSION."""


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcChannelJoinObservedValidation:
    """Validation based on the learner joining an IRC channel."""

    channel: str
    """IRC channel the learner must join."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SshPublicKeyObservedValidation:
    """Validation based on a public-key SSH audit event."""


type QuestValidationLeaf = (
    CommandHistoryValidation
    | InteractiveQuestionValidation
    | FileCheckValidation
    | FileMatchesPathValidation
    | UserPortFileValidation
    | PathExistsValidation
    | ExecutablePathValidation
    | OwnedPathValidation
    | LearnerHandleQuestionValidation
    | IrcCtcpVersionValidation
)


@dataclass(frozen=True, kw_only=True, slots=True)
class AllOfValidation:
    """Validation that requires every child validation to pass."""

    validations: tuple[QuestValidationLeaf, ...]
    """Child validation rules that must all succeed."""


@dataclass(frozen=True, kw_only=True, slots=True)
class GeneratedFileData:
    """Generated file strategy for per-learner quest data."""

    path_template: str
    """Path template for generated learner data."""
    generator: str
    """Generator id implemented by deterministic service code."""
    seed_strategy: Literal["learner+quest"]
    """Seed strategy for reproducible per-learner data generation."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Tier:
    """One score threshold tier."""

    id: str
    """Stable tier id stored in learner-state rows."""
    minimum_score: int
    """Minimum course score required for this tier."""
    title: str
    """Human-readable tier title."""


type QuestValidation = QuestValidationLeaf | AllOfValidation
type QuestData = GeneratedFileData
type SessionObjectiveValidation = (
    QuestValidation | IrcChannelJoinObservedValidation | SshPublicKeyObservedValidation
)


class CourseCatalog:
    """Validated lookup API over a course definition."""

    def __init__(self, course: Course) -> None:
        """Validate and index a course definition."""
        validate_courses((course,))
        self.course = course
        self._session_by_id = {session.id: session for session in course.sessions}
        self._quest_by_id = {quest.id: quest for quest in course.quests}
        self._tier_by_id = {tier.id: tier for tier in course.tiers}
        self._session_index_by_id = {
            session.id: session_index for session_index, session in enumerate(course.sessions)
        }

    def session(self, session_id: str) -> Session:
        """Return a session by id."""
        return self._session_by_id[session_id]

    def quest(self, quest_id: str) -> Quest:
        """Return a quest by id."""
        return self._quest_by_id[quest_id]

    def tier(self, tier_id: str) -> Tier:
        """Return a tier by id."""
        return self._tier_by_id[tier_id]

    def content_references(self) -> tuple[ContentReference, ...]:
        """Return all package content references owned by this course."""
        return _content_references(self.course)

    def commands_available_through(self, session_id: str) -> frozenset[str]:
        """Return commands introduced from the start through a session."""
        return frozenset(
            command
            for session in self.sessions_through(session_id)
            for command in session.introduced_commands
        )

    def skills_available_through(self, session_id: str) -> frozenset[str]:
        """Return skills introduced from the start through a session."""
        return frozenset(
            skill
            for session in self.sessions_through(session_id)
            for skill in session.introduced_skills
        )

    def enrichment_skills_available_through(self, session_id: str) -> frozenset[str]:
        """Return optional skills available from the start through a session."""
        return frozenset(
            skill
            for session in self.sessions_through(session_id)
            for skill in session.enrichment_skills
        )

    def all_skills_available_through(self, session_id: str) -> frozenset[str]:
        """Return required and optional skills available through a session."""
        return self.skills_available_through(session_id) | self.enrichment_skills_available_through(
            session_id,
        )

    def quests_available_after(self, session_id: str) -> tuple[Quest, ...]:
        """Return quests assigned to the follow-up block after a session."""
        self.session(session_id)
        return tuple(
            quest
            for quest in sorted(self.course.quests, key=lambda course_quest: course_quest.sequence)
            if quest.available_after_session == session_id
        )

    def quests_available_through(self, session_id: str) -> tuple[Quest, ...]:
        """Return all quests released through a session."""
        released_session_ids = frozenset(
            session.id for session in self.sessions_through(session_id)
        )
        return tuple(
            quest
            for quest in sorted(self.course.quests, key=lambda course_quest: course_quest.sequence)
            if quest.available_after_session in released_session_ids
        )

    def session_is_after(self, session_id: str, previous_session_id: str) -> bool:
        """Return whether a session is later than another session."""
        return (
            self._session_index_by_id[session_id] > self._session_index_by_id[previous_session_id]
        )

    def next_quest_after(self, quest_id: str | None, session_reached: str) -> Quest | None:
        """Return the next ordered available quest after a quest id, or the first quest."""
        ordered_quests = self.quests_available_through(session_reached)
        if quest_id is None:
            return ordered_quests[0] if ordered_quests else None
        for quest_index, quest in enumerate(ordered_quests):
            if quest.id == quest_id:
                next_quest_index = quest_index + 1
                if next_quest_index >= len(ordered_quests):
                    return None
                return ordered_quests[next_quest_index]
        raise KeyError(quest_id)

    def next_assignable_quest(
        self,
        session_reached: str,
        completed_quest_ids: frozenset[str],
    ) -> Quest | None:
        """Return the highest-priority incomplete quest available to a learner."""
        completed_unknown_quest_ids = completed_quest_ids - frozenset(self._quest_by_id)
        if completed_unknown_quest_ids:
            raise KeyError(sorted(completed_unknown_quest_ids)[0])
        for quest in self.prioritized_quests(
            session_reached,
            self.quests_available_through(session_reached),
        ):
            if quest.id not in completed_quest_ids:
                return quest
        return None

    def prioritized_quests(
        self,
        session_reached: str,
        quests: tuple[Quest, ...],
    ) -> tuple[Quest, ...]:
        """Order released quests, prioritizing the currently released session."""
        available_quest_ids = frozenset(
            quest.id for quest in self.quests_available_through(session_reached)
        )
        return tuple(
            sorted(
                (quest for quest in quests if quest.id in available_quest_ids),
                key=lambda quest: (
                    quest.available_after_session != session_reached,
                    quest.sequence,
                ),
            ),
        )

    def sessions_through(self, session_id: str) -> tuple[Session, ...]:
        """Return sessions from the start of the course through one session."""
        session_index = self._session_index_by_id[session_id]
        return self.course.sessions[: session_index + 1]


def validate_courses(courses: tuple[Course, ...]) -> None:
    """Validate one or more course definitions."""
    _require_unique("course ids", tuple(course.id for course in courses))
    for course in courses:
        _validate_course(course)


def _validate_course(course: Course) -> None:
    _require_non_empty("course id", course.id)
    _require_non_empty("course title", course.title)
    _require_non_empty("course tutor system prompt", course.tutor_system_prompt)
    _require_non_empty("course timezone", course.timezone)
    if not course.sessions:
        raise ValueError("course needs sessions")
    _require_unique("session ids", tuple(session.id for session in course.sessions))
    _require_unique("quest ids", tuple(quest.id for quest in course.quests))
    _require_unique("quest sequences", tuple(quest.sequence for quest in course.quests))
    _require_unique("tier ids", tuple(tier.id for tier in course.tiers))
    _require_unique(
        "content reference ids",
        tuple(content_reference.id for content_reference in _content_references(course)),
    )
    _validate_course_dates(course)
    _validate_session_dates(course.sessions)
    for session in course.sessions:
        _validate_session(session)
    for tier in course.tiers:
        _validate_tier(tier)
    _validate_tier_thresholds(course.tiers)
    _validate_quests(course)


def _validate_session(session: Session) -> None:
    _require_non_empty("session id", session.id)
    _require_non_empty("session title", session.title)
    _require_non_empty_values("session command", session.introduced_commands)
    _require_non_empty_values("session skill", session.introduced_skills)
    _require_non_empty_values_if_present("session enrichment skill", session.enrichment_skills)
    _require_disjoint_values(
        "session required and enrichment skills",
        session.introduced_skills,
        session.enrichment_skills,
    )
    _require_non_empty_values("learning objective", session.learning_objectives)
    _require_unique(
        "session objective ids", tuple(objective.id for objective in session.objectives)
    )
    for objective in session.objectives:
        _require_non_empty("session objective id", objective.id)
        _require_non_empty("session objective title", objective.title)
        _require_non_empty("session objective prompt", objective.prompt)
        _validate_session_objective_validation(objective.validation)
    _validate_session_content(session)


def _validate_session_objective_validation(validation: object) -> None:
    if isinstance(
        validation,
        IrcChannelJoinObservedValidation | SshPublicKeyObservedValidation,
    ):
        return
    _validate_quest_validation(validation)


def _validate_tier(tier: Tier) -> None:
    _require_non_empty("tier id", tier.id)
    _require_non_empty("tier title", tier.title)
    if tier.minimum_score < 0:
        raise ValueError("tier minimum score must not be negative")


def _validate_quests(course: Course) -> None:
    session_ids = frozenset(session.id for session in course.sessions)
    for quest in course.quests:
        _validate_quest_shape(quest)
        if quest.available_after_session not in session_ids:
            raise ValueError(f"quest references unknown session: {quest.id}")
        _validate_quest_availability(course, quest)


def _validate_quest_shape(quest: Quest) -> None:
    _require_non_empty("quest id", quest.id)
    _require_non_empty("quest title", quest.title)
    _require_non_empty("quest story", quest.story)
    _require_non_empty("quest learner goal", quest.learner_goal)
    _require_non_empty("quest prompt", quest.prompt)
    _require_non_empty_values("quest autonomy checklist item", quest.autonomy_checklist)
    _require_non_empty_values("quest command", quest.required_commands)
    _require_non_empty_values("quest skill", quest.practiced_skills)
    _validate_hints(quest.hints)
    _validate_failure_feedback(quest.failure_feedback)
    _validate_quest_content(quest)
    if quest.sequence <= 0:
        raise ValueError("quest sequence must be positive")
    if quest.score <= 0:
        raise ValueError("quest score must be positive")
    _validate_quest_validation(quest.validation)
    _validate_quest_data(quest.data)


def _validate_quest_validation(validation: object) -> None:
    if isinstance(validation, AllOfValidation):
        _validate_all_of_validation(validation)
        return
    _validate_quest_validation_leaf(validation)


def _validate_quest_validation_leaf(validation: object) -> None:
    if _validate_command_or_question_validation(validation):
        return
    if _validate_file_based_validation(validation):
        return
    if _validate_path_based_validation(validation):
        return
    raise ValueError(f"unknown quest validation: {type(validation).__name__}")


def _validate_command_or_question_validation(validation: object) -> bool:
    if isinstance(validation, CommandHistoryValidation):
        _require_non_empty_values("command history pattern", validation.required_patterns)
        _require_non_empty_values("command history command", validation.observed_commands)
        for pattern in validation.required_patterns:
            _require_regex("command history pattern", pattern)
            _require_simple_command_history_regex(pattern)
        return True
    if isinstance(validation, InteractiveQuestionValidation):
        _require_non_empty("interactive question", validation.question)
        _require_answer_concepts(validation.required_concepts)
        return True
    if isinstance(validation, LearnerHandleQuestionValidation):
        _require_non_empty("learner handle question", validation.question)
        return True
    if isinstance(validation, IrcCtcpVersionValidation):
        _require_non_empty_values("IRC CTCP accepted client", validation.accepted_clients)
        return True
    return False


def _require_answer_concepts(concepts: tuple[AnswerConcept, ...]) -> None:
    if not concepts:
        raise ValueError("missing interactive answer concept")
    _require_unique("interactive answer concept ids", tuple(concept.id for concept in concepts))
    for concept in concepts:
        _require_non_empty("interactive answer concept id", concept.id)
        _require_non_empty_values("interactive answer concept alias", concept.aliases)
        _require_non_empty("interactive answer concept rubric", concept.rubric)
        for alias_pattern in concept.aliases:
            _require_regex("interactive answer concept alias", alias_pattern)
        _require_non_empty_values_if_present(
            "interactive answer forbidden pattern",
            concept.forbidden_patterns,
        )
        for forbidden_pattern in concept.forbidden_patterns:
            _require_regex("interactive answer forbidden pattern", forbidden_pattern)


def _validate_file_based_validation(validation: object) -> bool:
    if isinstance(validation, FileCheckValidation):
        _require_validation_path("file check path", validation.path)
        _require_non_empty("file check regex", validation.required_regex)
        _require_regex("file check regex", validation.required_regex)
        if validation.forbidden_regex is not None:
            _require_non_empty("forbidden file check regex", validation.forbidden_regex)
            _require_regex("forbidden file check regex", validation.forbidden_regex)
        return True
    if isinstance(validation, FileMatchesPathValidation):
        _require_validation_path("file match path", validation.path)
        if not validation.source_path.startswith("/"):
            raise ValueError("file match source path must be absolute")
        _require_validation_path("file match source path", validation.source_path)
        return True
    if isinstance(validation, UserPortFileValidation):
        _require_validation_path("user port file path", validation.path)
        _require_non_empty("user port file regex template", validation.required_regex_template)
        if "{port}" not in validation.required_regex_template:
            raise ValueError("user port file regex template must include port placeholder")
        if validation.port_formula != "10000+uid":
            raise ValueError("unknown user port formula")
        _require_regex(
            "user port file regex template",
            validation.required_regex_template.replace("{port}", "12345"),
        )
        return True
    return False


def _validate_path_based_validation(validation: object) -> bool:
    if isinstance(validation, PathExistsValidation):
        _require_non_empty_values("path existence path", validation.paths)
        for path in validation.paths:
            _require_validation_path("path existence path", path)
        return True
    if isinstance(validation, ExecutablePathValidation):
        _require_non_empty_values("executable path", validation.paths)
        for path in validation.paths:
            _require_validation_path("executable path", path)
        return True
    if isinstance(validation, OwnedPathValidation):
        _require_validation_path("owned path", validation.path)
        return True
    return False


def _validate_all_of_validation(validation: AllOfValidation) -> None:
    if not validation.validations:
        raise ValueError("all-of validation needs child validations")
    for child_validation in validation.validations:
        _validate_quest_validation_leaf(child_validation)


def _validate_quest_data(data: object | None) -> None:
    if data is None:
        return
    if isinstance(data, GeneratedFileData):
        _require_learner_path("generated file path template", data.path_template)
        _require_non_empty("generated file generator", data.generator)
        if data.seed_strategy != "learner+quest":
            raise ValueError("unknown generated data seed strategy")
        return
    raise ValueError(f"unknown quest data: {type(data).__name__}")


def _validate_session_content(session: Session) -> None:
    required_purposes = frozenset({"slides", "self-study", "recap"})
    content_purposes = frozenset(content_reference.purpose for content_reference in session.content)
    if not required_purposes <= content_purposes:
        raise ValueError(f"session missing required content: {session.id}")
    for content_reference in session.content:
        _validate_content_reference(content_reference)


def _validate_quest_content(quest: Quest) -> None:
    if not quest.docs:
        raise ValueError(f"quest missing documentation: {quest.id}")
    for content_reference in quest.docs:
        _validate_content_reference(content_reference)
    if not any(content_reference.purpose == "quest" for content_reference in quest.docs):
        raise ValueError(f"quest missing quest documentation: {quest.id}")


def _validate_content_reference(content_reference: ContentReference) -> None:
    _require_non_empty("content reference id", content_reference.id)
    _require_non_empty("content reference title", content_reference.title)
    _require_non_empty("content reference path", content_reference.path)
    if "\\" in content_reference.path:
        raise ValueError(f"content path must be POSIX-style: {content_reference.id}")
    path = PurePosixPath(content_reference.path)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"content path must stay inside the package: {content_reference.id}")
    if content_reference.purpose == "slides" and not content_reference.path.endswith("/slides.md"):
        raise ValueError(f"slides content must be named slides.md: {content_reference.id}")
    if content_reference.purpose == "self-study" and not content_reference.path.endswith(
        "/self-study.md",
    ):
        raise ValueError(f"self-study content must be named self-study.md: {content_reference.id}")
    if content_reference.purpose != "slides" and not content_reference.path.endswith(".md"):
        raise ValueError(f"content must use markdown: {content_reference.id}")


def _validate_hints(hints: tuple[Hint, ...]) -> None:
    if len(hints) < 3:
        raise ValueError("quest needs at least three hints")
    expected_hint_level = 1
    for hint in hints:
        if hint.level != expected_hint_level:
            raise ValueError("hint levels must start at 1 and increase by 1")
        _require_non_empty("hint text", hint.text)
        expected_hint_level += 1


def _validate_failure_feedback(failure_feedback: tuple[FailureFeedback, ...]) -> None:
    if not failure_feedback:
        raise ValueError("quest needs failure feedback")
    _require_unique(
        "failure feedback reasons",
        tuple(failure_feedback_item.reason for failure_feedback_item in failure_feedback),
    )
    for failure_feedback_item in failure_feedback:
        _require_non_empty("failure feedback reason", failure_feedback_item.reason)
        _require_non_empty("failure feedback text", failure_feedback_item.text)


def _validate_quest_availability(course: Course, quest: Quest) -> None:
    course_catalog = _UncheckedCourseCatalog(course)
    available_commands = course_catalog.commands_available_through(quest.available_after_session)
    available_skills = course_catalog.skills_available_through(quest.available_after_session)
    validation_commands = _validation_observed_commands(quest.validation)
    future_commands = tuple(
        command for command in quest.required_commands if command not in available_commands
    )
    unlisted_validation_commands = tuple(
        command for command in validation_commands if command not in quest.required_commands
    )
    future_skills = tuple(
        skill for skill in quest.practiced_skills if skill not in available_skills
    )
    if future_commands:
        raise ValueError(f"quest references future command: {quest.id}")
    if unlisted_validation_commands:
        raise ValueError(f"quest validation references unlisted command: {quest.id}")
    if future_skills:
        raise ValueError(f"quest references future skill: {quest.id}")


def _validation_observed_commands(validation: QuestValidation) -> tuple[str, ...]:
    if isinstance(validation, AllOfValidation):
        return tuple(
            command
            for child_validation in validation.validations
            for command in _validation_observed_commands(child_validation)
        )
    if isinstance(validation, CommandHistoryValidation):
        return validation.observed_commands
    return ()


def _validate_session_dates(sessions: tuple[Session, ...]) -> None:
    previous_date: date | None = None
    for session in sessions:
        if previous_date is not None and session.date <= previous_date:
            raise ValueError("session dates must be strictly increasing")
        previous_date = session.date


def _validate_course_dates(course: Course) -> None:
    if course.starts_on > course.ends_on:
        raise ValueError("course start date must not be after end date")
    for session in course.sessions:
        if session.date < course.starts_on or session.date > course.ends_on:
            raise ValueError(f"session date outside course bounds: {session.id}")


def _validate_tier_thresholds(tiers: tuple[Tier, ...]) -> None:
    previous_threshold: int | None = None
    for tier in tiers:
        if previous_threshold is not None and tier.minimum_score <= previous_threshold:
            raise ValueError("tier thresholds must be strictly increasing")
        previous_threshold = tier.minimum_score


def _content_references(course: Course) -> tuple[ContentReference, ...]:
    return tuple(
        content_reference for session in course.sessions for content_reference in session.content
    ) + tuple(content_reference for quest in course.quests for content_reference in quest.docs)


def _require_unique(label: str, values: tuple[object, ...]) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate {label}")


def _require_non_empty(label: str, value: str) -> None:
    if value.strip() == "":
        raise ValueError(f"empty {label}")


def _require_non_empty_values(label: str, values: tuple[str, ...]) -> None:
    if not values:
        raise ValueError(f"missing {label}")
    for value in values:
        _require_non_empty(label, value)


def _require_learner_path(label: str, path: str) -> None:
    _require_non_empty(label, path)
    if "\\" in path:
        raise ValueError(f"{label} must be POSIX-style")
    if path == "~":
        raise ValueError(f"{label} must identify a learner-owned artifact")
    if not path.startswith("~/"):
        raise ValueError(f"{label} must be learner-owned")
    if _path_contains_traversal(path):
        raise ValueError(f"{label} must stay inside learner home")


def _require_validation_path(label: str, path: str) -> None:
    _require_non_empty(label, path)
    if "\\" in path:
        raise ValueError(f"{label} must be POSIX-style")
    if path.startswith("~") and path != "~" and not path.startswith("~/"):
        raise ValueError(f"{label} must use ~ or ~/ for learner home")
    if _path_contains_traversal(path):
        raise ValueError(f"{label} must not contain traversal")


def _path_contains_traversal(path: str) -> bool:
    return any(path_part in {".", ".."} for path_part in path.split("/"))


def _require_non_empty_values_if_present(label: str, values: tuple[str, ...]) -> None:
    for value in values:
        _require_non_empty(label, value)


def _require_regex(label: str, pattern: str) -> None:
    try:
        re.compile(pattern)
    except re.error as regex_error:
        raise ValueError(f"invalid {label}: {pattern}") from regex_error


def _require_simple_command_history_regex(pattern: str) -> None:
    if _COMMAND_HISTORY_NESTED_REPEAT_PATTERN.search(pattern) is not None:
        raise ValueError(f"pathological command history pattern: {pattern}")


def _require_disjoint_values(
    label: str,
    left_values: tuple[str, ...],
    right_values: tuple[str, ...],
) -> None:
    if set(left_values) & set(right_values):
        raise ValueError(f"overlapping {label}")


class _UncheckedCourseCatalog:
    """Lookup helper used while a course is still being validated."""

    def __init__(self, course: Course) -> None:
        self.course = course
        self._session_index_by_id = {
            session.id: session_index for session_index, session in enumerate(course.sessions)
        }

    def commands_available_through(self, session_id: str) -> frozenset[str]:
        return frozenset(
            command
            for session in self._sessions_through(session_id)
            for command in session.introduced_commands
        )

    def skills_available_through(self, session_id: str) -> frozenset[str]:
        return frozenset(
            skill
            for session in self._sessions_through(session_id)
            for skill in session.introduced_skills
        )

    def _sessions_through(self, session_id: str) -> tuple[Session, ...]:
        session_index = self._session_index_by_id[session_id]
        return self.course.sessions[: session_index + 1]

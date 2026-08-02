"""`/makers` projection writer."""

from __future__ import annotations

import fcntl
import json
import os
import posixpath
import re
import sqlite3
import uuid
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import abc, files
from pathlib import Path

from maker_guide.curriculum.documentation import released_quest_index_text
from maker_guide.curriculum.models import CourseCatalog, Quest, Session
from maker_guide.curriculum.tiers import current_tier_id
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import RepositoryError, transaction
from maker_guide.repositories.maker_projection import (
    MakerCompletedQuest,
    MakerCompletedSessionObjective,
    MakerLearnerState,
    list_maker_completed_quests,
    list_maker_completed_session_objectives,
    list_maker_learner_states,
)
from maker_guide.repositories.outbox_item import (
    PROJECTION_OUTBOX_KIND,
    OutboxItem,
    list_retryable_outbox_items_by_kind,
    mark_outbox_item_processed,
    validate_projection_outbox_item,
)
from maker_guide.repositories.peer_thank import PeerThank, list_peer_thanks_by_recipient
from maker_guide.repositories.projection_version import ProjectionVersion, upsert_projection_version
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, list_score_entries

MAKERS_PROJECTION_NAME = "makers"
MAKERS_PROJECTION_VERSION = 13
_LOCK_FILENAME = ".sync.lock"
_TEMPORARY_FILE_PREFIX = ".maker-guide-projection-"
_TEMPORARY_FILE_SUFFIX = ".tmp"
_DIRECTORY_MODE = 0o755
_FILE_MODE = 0o644
_LOCAL_MARKDOWN_LINK_TARGET = re.compile(
    r"(?<=\]\()(?P<target>(?![a-z][a-z0-9+.-]*:|/|#)[^)\s]+\.md(?:#[^)]*)?)",
)


class MakersProjectionError(RuntimeError):
    """Raised when `/makers` projection cannot be written safely."""


@dataclass(frozen=True, kw_only=True, slots=True)
class MakersProjectionOptions:
    """Options for one `/makers` projection sync."""

    makers_root: Path
    """Root directory for learner-visible `/makers` files."""
    projected_at: str
    """ISO timestamp recorded for this projection write."""
    documents_root: Path | None = None
    """Root directory for learner-visible curriculum docs."""
    process_outbox: bool = True
    """Whether retryable projection outbox rows should be marked processed."""
    outbox_limit: int = 1000
    """Maximum number of projection outbox rows to mark processed."""


@dataclass(frozen=True, kw_only=True, slots=True)
class MakersProjectionResult:
    """Result of a `/makers` projection sync."""

    learner_count: int
    """Number of learner directories projected."""
    processed_outbox_count: int
    """Number of projection outbox rows marked processed."""
    projected_at: str
    """ISO timestamp recorded for this projection write."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _ProjectionWriteContext:
    """Mutable write manifest for one projection pass."""

    root: Path
    """Root directory being regenerated."""
    expected_directories: set[Path]
    """Projected directories that should exist after sync."""
    expected_files: set[Path]
    """Projected files that should exist after sync."""


def sync_makers_projection(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    options: MakersProjectionOptions,
) -> MakersProjectionResult:
    """Regenerate `/makers` from SQLite and optionally clear projection outbox rows."""
    documents_root = options.documents_root or options.makers_root.with_name("docs")
    if documents_root == options.makers_root:
        raise MakersProjectionError("documents root must differ from makers root")
    _ensure_directory(options.makers_root)
    with _makers_projection_lock(options.makers_root):
        retryable_projection_items = _retryable_projection_outbox_items(
            database_connection,
            options.process_outbox,
            options.outbox_limit,
        )
        learner_states = list_maker_learner_states(database_connection, catalog.course.id)
        completed_quests_by_handle = _completed_quests_by_handle(
            list_maker_completed_quests(database_connection, catalog.course.id),
        )
        completed_objectives_by_handle = _completed_objectives_by_handle(
            list_maker_completed_session_objectives(database_connection, catalog.course.id),
        )
        thanks_by_recipient = list_peer_thanks_by_recipient(
            database_connection,
            catalog.course.id,
        )
        _write_makers_files(
            database_connection,
            options.makers_root,
            catalog,
            learner_states,
            completed_quests_by_handle,
            completed_objectives_by_handle,
            thanks_by_recipient,
        )
        course_release = get_course_release(database_connection, catalog.course.id)
        _write_content_files(
            documents_root,
            catalog,
            None if course_release is None else course_release.session_reached,
        )
        processed_outbox_count = _record_projection_write(
            database_connection,
            options.projected_at,
            options.process_outbox,
            retryable_projection_items,
        )
    return MakersProjectionResult(
        learner_count=len(learner_states),
        processed_outbox_count=processed_outbox_count,
        projected_at=options.projected_at,
    )


@contextmanager
def _makers_projection_lock(makers_root: Path) -> Generator[None]:
    lock_path = makers_root / _LOCK_FILENAME
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise MakersProjectionError(
                f"makers projection sync already in progress for {makers_root}",
            ) from error
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _rank_learners(
    learner_states: list[MakerLearnerState],
) -> list[tuple[int, MakerLearnerState]]:
    ranked_states: list[tuple[int, MakerLearnerState]] = []
    for rank_position, learner_state in enumerate(
        sorted(
            [learner_state for learner_state in learner_states if learner_state.rank_eligible],
            key=lambda learner_state: (
                -learner_state.score_total,
                -learner_state.completed_quest_count,
                learner_state.last_score_at is None,
                learner_state.last_score_at or "",
                learner_state.handle,
            ),
        ),
        start=1,
    ):
        ranked_states.append((rank_position, learner_state))
    return ranked_states


def _completed_quests_by_handle(
    completed_quests: list[MakerCompletedQuest],
) -> dict[str, tuple[MakerCompletedQuest, ...]]:
    quests_by_handle: defaultdict[str, list[MakerCompletedQuest]] = defaultdict(list)
    for completed_quest in completed_quests:
        quests_by_handle[completed_quest.handle].append(completed_quest)
    return {
        handle: tuple(handle_completed_quests)
        for handle, handle_completed_quests in quests_by_handle.items()
    }


def _completed_objectives_by_handle(
    completed_objectives: list[MakerCompletedSessionObjective],
) -> dict[str, tuple[MakerCompletedSessionObjective, ...]]:
    objectives_by_handle: defaultdict[str, list[MakerCompletedSessionObjective]] = defaultdict(list)
    for completed_objective in completed_objectives:
        objectives_by_handle[completed_objective.handle].append(completed_objective)
    return {
        handle: tuple(handle_completed_objectives)
        for handle, handle_completed_objectives in objectives_by_handle.items()
    }


def _write_makers_files(  # noqa: PLR0913 - Projection inputs are distinct state sources.
    database_connection: sqlite3.Connection,
    makers_root: Path,
    catalog: CourseCatalog,
    learner_states: list[MakerLearnerState],
    completed_quests_by_handle: dict[str, tuple[MakerCompletedQuest, ...]],
    completed_objectives_by_handle: dict[str, tuple[MakerCompletedSessionObjective, ...]],
    thanks_by_recipient: dict[str, tuple[PeerThank, ...]],
) -> None:
    _ensure_directory(makers_root)
    write_context = _ProjectionWriteContext(
        root=makers_root,
        expected_directories={Path()},
        expected_files=set(),
    )
    rank_positions = {
        learner_state.handle: rank_position
        for rank_position, learner_state in _rank_learners(learner_states)
    }
    for learner_state in learner_states:
        completed_quests = completed_quests_by_handle.get(learner_state.handle, ())
        completed_objectives = completed_objectives_by_handle.get(learner_state.handle, ())
        received_thanks = thanks_by_recipient.get(learner_state.handle, ())
        _write_learner_files(
            database_connection,
            write_context,
            catalog,
            rank_positions.get(learner_state.handle),
            learner_state,
            completed_quests,
            completed_objectives,
            received_thanks,
        )
    _remove_stale_paths(
        makers_root,
        write_context.expected_directories,
        write_context.expected_files,
    )


def _write_content_files(
    documents_root: Path,
    catalog: CourseCatalog,
    released_through: str | None,
) -> None:
    """Project the open reference library and release-gated sessions and quests."""
    content_resource = files("maker_guide.curriculum").joinpath("content", catalog.course.id)
    if not content_resource.is_dir():
        raise MakersProjectionError("packaged curriculum content directory is missing")
    write_context = _ProjectionWriteContext(
        root=documents_root,
        expected_directories={Path()},
        expected_files=set(),
    )
    _ensure_directory(documents_root)
    for directory_name in ("commands", "concepts", "guides", "mentors"):
        _write_content_resource(
            write_context,
            content_resource.joinpath(directory_name),
            Path(directory_name),
        )
    if released_through is None:
        _write_course_index(write_context, catalog, None)
    else:
        _write_course_index(write_context, catalog, released_through)
        for relative_path in _released_content_paths(content_resource, catalog, released_through):
            write_context.expected_directories.update(relative_path.parents)
            _write_projected_file(
                write_context.root,
                relative_path,
                content_resource.joinpath(*relative_path.parts).read_text(encoding="utf-8"),
                write_context.expected_files,
            )
        relative_path = Path("quests/README.md")
        write_context.expected_directories.update(relative_path.parents)
        _write_projected_file(
            write_context.root,
            relative_path,
            released_quest_index_text(catalog, released_through),
            write_context.expected_files,
        )
    _remove_stale_paths(
        documents_root,
        write_context.expected_directories,
        write_context.expected_files,
    )


def _write_course_index(
    write_context: _ProjectionWriteContext,
    catalog: CourseCatalog,
    released_through: str | None,
) -> None:
    """Write release-filtered course navigation; references are projected separately."""
    sections = [f"# {catalog.course.title}", ""]
    if released_through is None:
        sections.extend(
            (
                "Session material will be published when the first session begins.",
                "",
            ),
        )
    else:
        for session in catalog.course.sessions:
            sections.extend((f"## {session.id}: {session.title}", ""))
            for content in session.content:
                if content.audience != "instructor":
                    content_path = content.path.removeprefix(f"content/{catalog.course.id}/")
                    sections.append(f"- [{content.title}]({content_path})")
            sections.append("")
            if session.id == released_through:
                break
    sections.extend(
        (
            "## Reference Cards",
            "",
            "- [Commands](commands/README.md)",
            "- [Concepts](concepts/README.md)",
            "- [Guides](guides/docs-map.md)",
        )
    )
    if released_through is not None:
        sections.append("- [Quests](quests/README.md)")
    sections.append("")
    _write_projected_file(
        write_context.root,
        Path("README.md"),
        "\n".join(sections),
        write_context.expected_files,
    )


def _released_content_paths(
    content_resource: abc.Traversable,
    catalog: CourseCatalog,
    released_through: str,
) -> tuple[Path, ...]:
    """Return documents reachable from released sessions and quests."""
    released_session_index = next(
        session_index
        for session_index, session in enumerate(catalog.course.sessions)
        if session.id == released_through
    )
    content_paths = {
        Path(content.path.removeprefix(f"content/{catalog.course.id}/"))
        for session in catalog.course.sessions[: released_session_index + 1]
        for content in session.content
    }
    content_paths.update(
        Path(content.path.removeprefix(f"content/{catalog.course.id}/"))
        for quest in catalog.quests_available_through(released_through)
        for content in quest.docs
    )
    pending_paths = list(content_paths)
    while pending_paths:
        relative_path = pending_paths.pop()
        markdown_text = content_resource.joinpath(*relative_path.parts).read_text(encoding="utf-8")
        for link_match in _LOCAL_MARKDOWN_LINK_TARGET.finditer(markdown_text):
            linked_path = _linked_content_path(relative_path, link_match.group("target"))
            if linked_path.is_relative_to("..") or linked_path in content_paths:
                continue
            if content_resource.joinpath(*linked_path.parts).is_file():
                content_paths.add(linked_path)
                pending_paths.append(linked_path)
    return tuple(sorted(content_paths))


def _linked_content_path(relative_path: Path, link_target: str) -> Path:
    """Resolve a package-relative Markdown link without leaving course content."""
    document_path, _separator, _anchor = link_target.partition("#")
    return Path(posixpath.normpath((relative_path.parent / document_path).as_posix()))


def _write_content_resource(
    write_context: _ProjectionWriteContext,
    content_resource: abc.Traversable,
    relative_path: Path,
) -> None:
    if content_resource.is_dir():
        write_context.expected_directories.add(relative_path)
        _ensure_directory(write_context.root / relative_path)
        for child_resource in sorted(
            content_resource.iterdir(),
            key=lambda child_resource: child_resource.name,
        ):
            _write_content_resource(
                write_context,
                child_resource,
                relative_path / child_resource.name,
            )
        return
    if content_resource.is_file():
        _write_projected_file(
            write_context.root,
            relative_path,
            content_resource.read_text(encoding="utf-8"),
            write_context.expected_files,
        )


def _write_learner_files(  # noqa: PLR0913 - Projection inputs are distinct state sources.
    database_connection: sqlite3.Connection,
    write_context: _ProjectionWriteContext,
    catalog: CourseCatalog,
    rank_position: int | None,
    learner_state: MakerLearnerState,
    completed_quests: tuple[MakerCompletedQuest, ...],
    completed_objectives: tuple[MakerCompletedSessionObjective, ...],
    received_thanks: tuple[PeerThank, ...],
) -> None:
    learner_relative_directory = _safe_relative_path(learner_state.handle)
    solves_relative_directory = learner_relative_directory / "solves"
    adoptions_relative_directory = learner_relative_directory / "adoptions"
    tracks_relative_directory = learner_relative_directory / "tracks"
    for relative_directory in (
        learner_relative_directory,
        solves_relative_directory,
        adoptions_relative_directory,
        tracks_relative_directory,
    ):
        write_context.expected_directories.add(relative_directory)
        _ensure_directory(write_context.root / relative_directory)

    if rank_position is not None:
        _write_projected_file(
            write_context.root,
            learner_relative_directory / "rank",
            f"{rank_position}\n",
            write_context.expected_files,
        )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "score",
        f"{learner_state.score_total}\n",
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "tier",
        f"{current_tier_id(catalog, learner_state.score_total) or 'none'}\n",
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "joined",
        f"{learner_state.joined_at}\n",
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "key-auth-progress",
        _key_auth_progress_file_content(completed_objectives),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "quests.json",
        _quest_progress_file_content(catalog, completed_quests, learner_state.session_reached),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "objectives.json",
        _objective_progress_file_content(catalog, completed_objectives),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "sessions.json",
        _session_progress_file_content(catalog, learner_state.session_reached),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "thanks.json",
        _thanks_file_content(received_thanks),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        learner_relative_directory / "score-ledger.json",
        _score_ledger_file_content(
            list_score_entries(
                database_connection,
                learner_state.handle,
                catalog.course.id,
            ),
            catalog,
            received_thanks,
        ),
        write_context.expected_files,
    )
    _write_projected_file(
        write_context.root,
        tracks_relative_directory / "lockouts",
        "none\n",
        write_context.expected_files,
    )
    for completed_quest in completed_quests:
        _write_projected_file(
            write_context.root,
            solves_relative_directory / _safe_relative_path(completed_quest.quest_id),
            f"{completed_quest.completed_at}\n",
            write_context.expected_files,
        )


def _key_auth_progress_file_content(
    completed_objectives: tuple[MakerCompletedSessionObjective, ...],
) -> str:
    for completed_objective in completed_objectives:
        if (completed_objective.session_id, completed_objective.objective_id) == (
            "S2",
            "ssh-public-key",
        ):
            return f"reinforcement\ncompleted_at={completed_objective.completed_at}\n"
    return "pending\n"


def _quest_progress_file_content(
    catalog: CourseCatalog,
    completed_quests: tuple[MakerCompletedQuest, ...],
    session_reached: str | None,
) -> str:
    completed_quest_ids = {quest.quest_id for quest in completed_quests}
    released_quests = (
        () if session_reached is None else catalog.quests_available_through(session_reached)
    )
    return (
        json.dumps(
            {
                "total": len(catalog.course.quests),
                "completed": [
                    _quest_progress_entry(quest)
                    for quest in catalog.course.quests
                    if quest.id in completed_quest_ids
                ],
                "remaining": [
                    _quest_progress_entry(quest)
                    for quest in released_quests
                    if quest.id not in completed_quest_ids
                ],
            },
            indent=2,
        )
        + "\n"
    )


def _objective_progress_file_content(
    catalog: CourseCatalog,
    completed_objectives: tuple[MakerCompletedSessionObjective, ...],
) -> str:
    completed_objective_ids = {
        (objective.session_id, objective.objective_id) for objective in completed_objectives
    }
    return (
        json.dumps(
            {
                "total": sum(len(session.objectives) for session in catalog.course.sessions),
                "completed": [
                    {
                        "id": objective.id,
                        "title": objective.title,
                        "documentation_path": _session_progress_entry(
                            session,
                            catalog.course.id,
                        )["documentation_path"],
                    }
                    for session in catalog.course.sessions
                    for objective in session.objectives
                    if (session.id, objective.id) in completed_objective_ids
                ],
            },
            indent=2,
        )
        + "\n"
    )


def _quest_progress_entry(quest: Quest) -> dict[str, str]:
    return {
        "id": quest.id,
        "title": quest.title,
        "documentation_path": f"quests/{quest.id}.md",
    }


def _session_progress_file_content(
    catalog: CourseCatalog,
    session_reached: str | None,
) -> str:
    session_reached_index = 0
    if session_reached is not None:
        catalog.session(session_reached)
        session_reached_index = next(
            session_index + 1
            for session_index, session in enumerate(catalog.course.sessions)
            if session.id == session_reached
        )
    return (
        json.dumps(
            {
                "reached": [
                    _session_progress_entry(session, catalog.course.id)
                    for session in catalog.course.sessions[:session_reached_index]
                ],
                "remaining": [
                    _session_progress_entry(session, catalog.course.id)
                    for session in catalog.course.sessions[session_reached_index:]
                ],
            },
            indent=2,
        )
        + "\n"
    )


def _session_progress_entry(session: Session, course_id: str) -> dict[str, str]:
    for content_reference in session.content:
        if content_reference.audience == "learner" and content_reference.purpose == "self-study":
            return {
                "id": session.id,
                "title": session.title,
                "documentation_path": content_reference.path.removeprefix(
                    f"content/{course_id}/",
                ),
            }
    raise MakersProjectionError(f"session {session.id} has no learner self-study guide")


def _thanks_file_content(received_thanks: tuple[PeerThank, ...]) -> str:
    return (
        json.dumps(
            [
                {
                    "from": peer_thank.giver_handle,
                    "reason": peer_thank.reason,
                    "thanked_on": peer_thank.thanked_on,
                    "created_at": peer_thank.created_at,
                }
                for peer_thank in received_thanks
            ],
            indent=2,
        )
        + "\n"
    )


def _score_ledger_file_content(
    entries: list[ScoreLedgerEntry],
    catalog: CourseCatalog,
    received_thanks: tuple[PeerThank, ...],
) -> str:
    quest_titles = {quest.id: quest.title for quest in catalog.course.quests}
    objective_titles = {
        f"{session.id}:{objective.id}": objective.title
        for session in catalog.course.sessions
        for objective in session.objectives
    }
    thank_givers = {
        str(peer_thank.id): peer_thank.giver_handle
        for peer_thank in received_thanks
        if peer_thank.id is not None
    }
    thank_reasons = {
        str(peer_thank.id): peer_thank.reason
        for peer_thank in received_thanks
        if peer_thank.id is not None
    }
    return (
        json.dumps(
            [
                {
                    "amount": entry.amount,
                    "reason": entry.reason,
                    "related_type": entry.related_type,
                    "related_id": entry.related_id,
                    "related_name": (
                        quest_titles.get(entry.related_id or "", entry.related_id)
                        if entry.related_type == "quest"
                        else objective_titles.get(entry.related_id or "", entry.related_id)
                        if entry.related_type == "session_objective"
                        else None
                    ),
                    "peer_thank_giver": (
                        thank_givers.get(entry.related_id or "")
                        if entry.related_type == "peer_thank"
                        else None
                    ),
                    "peer_thank_reason": (
                        thank_reasons.get(entry.related_id or "")
                        if entry.related_type == "peer_thank"
                        else None
                    ),
                    "created_at": entry.created_at,
                }
                for entry in entries
            ],
            indent=2,
        )
        + "\n"
    )


def _write_projected_file(
    makers_root: Path,
    relative_path: Path,
    content: str,
    expected_files: set[Path],
) -> None:
    expected_files.add(relative_path)
    destination_path = makers_root / relative_path
    _ensure_directory(destination_path.parent)
    temporary_path = _temporary_projection_path(destination_path)
    with temporary_path.open("w", encoding="utf-8") as temporary_file:
        temporary_file.write(content)
        temporary_file.flush()
        temporary_path.chmod(_FILE_MODE)
        os.fsync(temporary_file.fileno())
    temporary_path.replace(destination_path)
    _fsync_directory(destination_path.parent)


def _temporary_projection_path(destination_path: Path) -> Path:
    temporary_name = "".join(
        (
            f"{_TEMPORARY_FILE_PREFIX}{destination_path.name}.",
            uuid.uuid4().hex,
            _TEMPORARY_FILE_SUFFIX,
        ),
    )
    return destination_path.with_name(
        temporary_name,
    )


def _remove_stale_paths(
    makers_root: Path,
    expected_directories: set[Path],
    expected_files: set[Path],
) -> None:
    for projected_path in sorted(makers_root.rglob("*"), reverse=True):
        relative_path = projected_path.relative_to(makers_root)
        if relative_path == Path(_LOCK_FILENAME):
            continue
        if projected_path.is_dir() and not projected_path.is_symlink():
            if relative_path not in expected_directories:
                projected_path.rmdir()
                _fsync_directory(projected_path.parent)
        elif relative_path not in expected_files:
            projected_path.unlink()
            _fsync_directory(projected_path.parent)


def _record_projection_write(
    database_connection: sqlite3.Connection,
    projected_at: str,
    process_outbox: bool,
    retryable_projection_items: list[OutboxItem],
) -> int:
    with transaction(database_connection):
        upsert_projection_version(
            database_connection,
            ProjectionVersion(
                name=MAKERS_PROJECTION_NAME,
                last_written_at=projected_at,
                version=MAKERS_PROJECTION_VERSION,
            ),
        )
        if not process_outbox:
            return 0
        for retryable_projection_item in retryable_projection_items:
            if retryable_projection_item.id is None:
                raise MakersProjectionError("retryable outbox item has no id")
            mark_outbox_item_processed(
                database_connection,
                retryable_projection_item.id,
                projected_at,
            )
        return len(retryable_projection_items)


def _retryable_projection_outbox_items(
    database_connection: sqlite3.Connection,
    process_outbox: bool,
    outbox_limit: int,
) -> list[OutboxItem]:
    if not process_outbox:
        return []
    retryable_projection_items = list_retryable_outbox_items_by_kind(
        database_connection,
        PROJECTION_OUTBOX_KIND,
        outbox_limit,
    )
    try:
        for retryable_projection_item in retryable_projection_items:
            validate_projection_outbox_item(retryable_projection_item)
    except RepositoryError as error:
        raise MakersProjectionError(str(error)) from error
    return retryable_projection_items


def _ensure_directory(path: Path) -> None:
    if path.is_symlink():
        raise MakersProjectionError(f"unsafe symlinked projection directory: {path}")
    path.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    if not path.is_dir() or path.is_symlink():
        raise MakersProjectionError(f"unsafe projection directory: {path}")
    path.chmod(_DIRECTORY_MODE)
    _fsync_directory(path)
    if path.parent != path and path.parent.exists():
        _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    directory_descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _safe_relative_path(value: str) -> Path:
    if value in {"", ".", "..", _LOCK_FILENAME} or "/" in value or "\x00" in value:
        raise MakersProjectionError(f"unsafe projection path component: {value}")
    return Path(value)

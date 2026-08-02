"""Deterministic tutor documentation selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import abc, files
from typing import Literal

from maker_guide.curriculum.documentation import command_card_slug, document_title
from maker_guide.curriculum.models import ContentReference, CourseCatalog, Quest
from maker_guide.llm_tutor import ReadOnlyDocContext

type _InferredContentPurpose = Literal["command", "concept", "guide"]

_PACKAGE_CONTENT_PREFIX = "content/"
_LEARNER_DOCUMENTS_ROOT = "/docs"
_TOKEN_PATTERN = re.compile(r"\w+")
_CODE_SPAN_PATTERN = re.compile(r"`[^`\n]+`")
_TOPIC_PHRASE_OVERRIDES = {
    ("commands", "for"): ("for loop",),
    ("commands", "if"): ("if command",),
    ("commands", "read"): ("read command",),
    ("concepts", "io"): ("io", "i/o"),
}
_GUIDE_KEYWORDS = {
    "docs-map": ("docs", "documentation", "where find", "where is", "navigation"),
    "irc-support": ("irc", "weechat", "channel", "nick", "nickname"),
    "passwords": ("password", "passphrase", "login", "ssh key", "key"),
    "platform-reference": (
        "service",
        "systemd",
        "timer",
        "port",
        "url",
        "website",
        "homepage",
        "public_html",
        "nginx",
        "502",
    ),
}


@dataclass(frozen=True, kw_only=True, slots=True)
class TutorDocSelectionInput:
    """Inputs used to choose learner docs for one tutor request."""

    catalog: CourseCatalog
    current_session_id: str | None
    pending_quests: tuple[str, ...]
    message: str


def learner_document_path(package_path: str) -> str:
    """Convert a packaged curriculum path to a learner-visible docs path."""
    if not package_path.startswith(_PACKAGE_CONTENT_PREFIX):
        raise ValueError(
            f"content path must start with {_PACKAGE_CONTENT_PREFIX!r}: {package_path}",
        )
    course_relative_path, separator, learner_path = package_path.removeprefix(
        _PACKAGE_CONTENT_PREFIX,
    ).partition("/")
    if not separator or not course_relative_path:
        raise ValueError(f"content path must include a course directory: {package_path}")
    return f"{_LEARNER_DOCUMENTS_ROOT}/{learner_path}"


def select_tutor_docs(selection_input: TutorDocSelectionInput) -> tuple[ReadOnlyDocContext, ...]:
    """Select relevant Markdown docs for the tutor without guessing through the LLM."""
    selected_references: list[ContentReference] = []
    current_quests = tuple(
        selection_input.catalog.quest(quest_id) for quest_id in selection_input.pending_quests[:3]
    )
    for quest in current_quests:
        selected_references.extend(quest.docs)
    if selection_input.current_session_id is not None:
        current_session = selection_input.catalog.session(selection_input.current_session_id)
        selected_references.extend(
            reference
            for reference in current_session.content
            if reference.purpose in {"self-study", "recap"}
        )
    for quest in current_quests:
        for command in quest.required_commands:
            command_slug = command_card_slug(command)
            if _content_exists(selection_input.catalog.course.id, "commands", command_slug):
                selected_references.append(
                    _content_reference(
                        selection_input.catalog.course.id,
                        "commands",
                        command_slug,
                        "command",
                    ),
                )
    selected_references.extend(
        _content_reference(selection_input.catalog.course.id, "concepts", skill, "concept")
        for quest in current_quests
        for skill in quest.practiced_skills
        if _content_exists(selection_input.catalog.course.id, "concepts", skill)
    )
    selected_references.extend(
        _message_selected_references(selection_input.catalog.course.id, selection_input.message),
    )
    return tuple(
        _read_only_doc_context(reference) for reference in _deduplicate(selected_references)
    )


def quest_doc_contexts(quest: Quest) -> tuple[ReadOnlyDocContext, ...]:
    """Build read-only contexts for docs directly attached to a quest."""
    return tuple(_read_only_doc_context(reference) for reference in quest.docs)


def _message_selected_references(course_id: str, message: str) -> tuple[ContentReference, ...]:
    casefolded_message = message.casefold()
    message_phrase = _token_phrase(casefolded_message)
    code_command_words = _code_span_command_words(casefolded_message)
    references: list[ContentReference] = []
    content_sources: tuple[tuple[str, _InferredContentPurpose], ...] = (
        ("commands", "command"),
        ("concepts", "concept"),
    )
    for content_kind, purpose in content_sources:
        for resource in _content_directory(course_id, content_kind).iterdir():
            if (
                not resource.is_file()
                or resource.name == "README.md"
                or not resource.name.endswith(".md")
            ):
                continue
            slug = resource.name.removesuffix(".md")
            normalized_slug = slug.casefold()
            if any(
                _token_phrase(phrase) in message_phrase
                for phrase in _TOPIC_PHRASE_OVERRIDES.get(
                    (content_kind, normalized_slug),
                    (normalized_slug,),
                )
            ) or (content_kind == "commands" and normalized_slug in code_command_words):
                references.append(_content_reference(course_id, content_kind, slug, purpose))
    for guide_slug, keywords in _GUIDE_KEYWORDS.items():
        if any(_token_phrase(keyword) in message_phrase for keyword in keywords):
            references.append(_content_reference(course_id, "guides", guide_slug, "guide"))
    return tuple(references)


def _token_phrase(text: str) -> str:
    return f" {' '.join(_TOKEN_PATTERN.findall(text.casefold()))} "


def _code_span_command_words(message: str) -> set[str]:
    command_words: set[str] = set()
    for code_span_match in _CODE_SPAN_PATTERN.finditer(message):
        if command_word_match := _TOKEN_PATTERN.search(code_span_match.group()):
            command_words.add(command_word_match.group())
    return command_words


def _read_only_doc_context(reference: ContentReference) -> ReadOnlyDocContext:
    learner_path = learner_document_path(reference.path)
    return ReadOnlyDocContext(
        title=reference.title,
        path=reference.path,
        learner_path=learner_path,
        command=f"glow -p {learner_path}",
        purpose=reference.purpose,
        content=files("maker_guide.curriculum")
        .joinpath(reference.path)
        .read_text(encoding="utf-8"),
    )


def _deduplicate(references: list[ContentReference]) -> tuple[ContentReference, ...]:
    seen_paths: set[str] = set()
    deduplicated_references: list[ContentReference] = []
    for reference in references:
        if reference.path in seen_paths:
            continue
        seen_paths.add(reference.path)
        deduplicated_references.append(reference)
    return tuple(deduplicated_references)


def _content_exists(course_id: str, content_kind: str, slug: str) -> bool:
    return _content_directory(course_id, content_kind).joinpath(f"{slug}.md").is_file()


def _content_reference(
    course_id: str,
    content_kind: str,
    slug: str,
    purpose: _InferredContentPurpose,
) -> ContentReference:
    title = document_title(_content_directory(course_id, content_kind).joinpath(f"{slug}.md"))
    return ContentReference(
        id=f"{slug}-{purpose}-doc",
        title=title,
        path=f"content/{course_id}/{content_kind}/{slug}.md",
        audience="learner",
        purpose=purpose,
    )


def _content_directory(course_id: str, content_kind: str) -> abc.Traversable:
    return files("maker_guide.curriculum").joinpath("content", course_id, content_kind)

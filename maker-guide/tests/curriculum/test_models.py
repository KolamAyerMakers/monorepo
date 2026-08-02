"""Tests for curriculum catalog models and validation."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Literal, cast

import pytest

from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConcept,
    CommandHistoryValidation,
    ContentAudience,
    ContentPurpose,
    ContentReference,
    Course,
    CourseCatalog,
    ExecutablePathValidation,
    FailureFeedback,
    FileCheckValidation,
    GeneratedFileData,
    Hint,
    InteractiveQuestionValidation,
    PathExistsValidation,
    Quest,
    QuestValidation,
    Session,
    SessionObjective,
    Tier,
    UserPortFileValidation,
    validate_courses,
)


def test_validate_courses_rejects_duplicate_course_ids() -> None:
    """Course ids must be unique across catalog definitions."""
    with pytest.raises(ValueError, match="duplicate course ids"):
        validate_courses(
            (
                _course(course_id="lf2607"),
                _course(course_id="lf2607", title="Duplicate"),
            ),
        )


def test_course_catalog_rejects_duplicate_session_ids() -> None:
    """Session ids must be unique inside a course."""
    course = _course()

    with pytest.raises(ValueError, match="duplicate session ids"):
        CourseCatalog(replace(course, sessions=(course.sessions[0], course.sessions[0])))


def test_course_catalog_rejects_duplicate_quest_ids() -> None:
    """Quest ids must be unique inside a course."""
    course = _course()

    with pytest.raises(ValueError, match="duplicate quest ids"):
        CourseCatalog(replace(course, quests=(course.quests[0], course.quests[0])))


def test_course_catalog_rejects_duplicate_quest_sequences() -> None:
    """Quest sequences must be unique inside a course."""
    course = _course()

    with pytest.raises(ValueError, match="duplicate quest sequences"):
        CourseCatalog(
            replace(
                course,
                quests=(course.quests[0], replace(course.quests[0], id="name-system")),
            ),
        )


def test_course_catalog_reports_unknown_completed_quest_deterministically() -> None:
    """Unknown completion ids report the sorted first id."""
    course_catalog = CourseCatalog(_course())

    with pytest.raises(KeyError) as key_error_info:
        course_catalog.next_assignable_quest("S1", frozenset({"zzz", "aaa"}))

    assert key_error_info.value.args == ("aaa",)


def test_course_catalog_rejects_future_session_commands() -> None:
    """A quest cannot use commands that have not been taught yet."""
    course = _course()

    with pytest.raises(ValueError, match="quest references future command"):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], required_commands=("grep",)),),
            ),
        )


def test_course_catalog_rejects_future_validation_commands() -> None:
    """Command-history metadata cannot bypass taught-command gating."""
    course = _course()

    with pytest.raises(ValueError, match="quest references future command"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        required_commands=("grep",),
                        validation=CommandHistoryValidation(
                            required_patterns=(r"^grep .+$",),
                            observed_commands=("grep",),
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_future_session_skills() -> None:
    """A quest cannot practice skills that have not been taught yet."""
    course = _course()

    with pytest.raises(ValueError, match="quest references future skill"):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], practiced_skills=("pipes",)),),
            ),
        )


def test_course_catalog_keeps_enrichment_skills_off_required_path() -> None:
    """Optional deep-dive skills are discoverable without becoming quest gates."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            sessions=(
                replace(course.sessions[0], enrichment_skills=("kernel",)),
                course.sessions[1],
            ),
        ),
    )

    assert "kernel" not in course_catalog.skills_available_through("S1")
    assert "kernel" in course_catalog.enrichment_skills_available_through("S1")
    assert "kernel" in course_catalog.all_skills_available_through("S1")

    with pytest.raises(ValueError, match="quest references future skill"):
        CourseCatalog(
            replace(
                course_catalog.course,
                quests=(replace(course.quests[0], practiced_skills=("kernel",)),),
            ),
        )


def test_course_catalog_rejects_bad_enrichment_skills() -> None:
    """Enrichment skills must be non-empty and separate from required skills."""
    course = _course()

    with pytest.raises(ValueError, match="empty session enrichment skill"):
        CourseCatalog(
            replace(
                course,
                sessions=(replace(course.sessions[0], enrichment_skills=("",)), course.sessions[1]),
            ),
        )

    with pytest.raises(ValueError, match="overlapping session required and enrichment skills"):
        CourseCatalog(
            replace(
                course,
                sessions=(
                    replace(
                        course.sessions[0],
                        enrichment_skills=("filesystem-navigation",),
                    ),
                    course.sessions[1],
                ),
            ),
        )


def test_course_catalog_rejects_non_increasing_tier_thresholds() -> None:
    """Tier thresholds must strictly increase."""
    course = _course()

    with pytest.raises(ValueError, match="tier thresholds must be strictly increasing"):
        CourseCatalog(
            replace(
                course,
                tiers=(
                    course.tiers[0],
                    replace(course.tiers[1], minimum_score=0),
                ),
            ),
        )


def test_course_catalog_rejects_bad_course_dates() -> None:
    """Course windows must contain every session."""
    course = _course()

    with pytest.raises(ValueError, match="course start date must not be after end date"):
        CourseCatalog(
            replace(
                course,
                starts_on=date(2026, 8, 1),
                ends_on=date(2026, 7, 1),
            ),
        )

    with pytest.raises(ValueError, match="session date outside course bounds"):
        CourseCatalog(replace(course, starts_on=date(2026, 7, 12)))


def test_course_catalog_rejects_duplicate_content_reference_ids() -> None:
    """Content ids must be unique across sessions and quests."""
    course = _course()

    with pytest.raises(ValueError, match="duplicate content reference ids"):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], docs=(course.sessions[0].content[0],)),),
            ),
        )


def test_course_catalog_rejects_missing_session_content() -> None:
    """Every session needs live and autonomous learner content."""
    course = _course()

    with pytest.raises(ValueError, match="session missing required content"):
        CourseCatalog(
            replace(
                course,
                sessions=(replace(course.sessions[0], content=course.sessions[0].content[:2]),),
            ),
        )


def test_course_catalog_rejects_bad_content_paths() -> None:
    """Content references cannot escape package resources or use bad slide names."""
    course = _course()

    with pytest.raises(ValueError, match="content path must stay inside the package"):
        CourseCatalog(
            replace(
                course,
                sessions=(
                    replace(
                        course.sessions[0],
                        content=(
                            replace(course.sessions[0].content[0], path="../slides.md"),
                            *course.sessions[0].content[1:],
                        ),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match=r"slides content must be named slides\.md"):
        CourseCatalog(
            replace(
                course,
                sessions=(
                    replace(
                        course.sessions[0],
                        content=(
                            replace(
                                course.sessions[0].content[0],
                                path="content/course/sessions/S1/deck.md",
                            ),
                            *course.sessions[0].content[1:],
                        ),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match=r"self-study content must be named self-study\.md"):
        CourseCatalog(
            replace(
                course,
                sessions=(
                    replace(
                        course.sessions[0],
                        content=(
                            course.sessions[0].content[0],
                            replace(
                                course.sessions[0].content[1],
                                path="content/course/sessions/S1/guide.md",
                            ),
                            course.sessions[0].content[2],
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_thin_quest_autonomy_fields() -> None:
    """Quests need enough content to support autonomous progress."""
    course = _course()

    with pytest.raises(ValueError, match="quest needs at least three hints"):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], hints=course.quests[0].hints[:2]),),
            ),
        )

    with pytest.raises(ValueError, match="quest needs failure feedback"):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], failure_feedback=()),),
            ),
        )

    with pytest.raises(ValueError, match="quest missing documentation"):
        CourseCatalog(replace(course, quests=(replace(course.quests[0], docs=()),)))


def test_course_catalog_rejects_empty_all_of_validation() -> None:
    """Composite validation needs at least one child rule."""
    course = _course()

    with pytest.raises(ValueError, match="all-of validation needs child validations"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=AllOfValidation(validations=()),
                    ),
                ),
            ),
        )


def test_course_catalog_accepts_all_of_validation() -> None:
    """Composite validation can combine deterministic proof rules."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            quests=(
                replace(
                    course.quests[0],
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r"^ls$",),
                                observed_commands=("ls",),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    assert isinstance(course_catalog.quest("prove-shell-alive").validation, AllOfValidation)


def test_course_catalog_accepts_executable_path_validation() -> None:
    """Executable path validation is a deterministic proof rule."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            quests=(
                replace(
                    course.quests[0],
                    validation=ExecutablePathValidation(paths=("~/run.sh",)),
                ),
            ),
        ),
    )

    assert isinstance(
        course_catalog.quest("prove-shell-alive").validation,
        ExecutablePathValidation,
    )


def test_course_catalog_accepts_user_port_file_validation() -> None:
    """User-port file validation can require runtime-computed ports."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            quests=(
                replace(
                    course.quests[0],
                    validation=UserPortFileValidation(
                        path="~/.config/systemd/user/site.service",
                        required_regex_template=r"http\.server {port} --bind 127\.0\.0\.1",
                    ),
                ),
            ),
        ),
    )

    assert isinstance(course_catalog.quest("prove-shell-alive").validation, UserPortFileValidation)


def test_course_catalog_accepts_user_port_regex_quantifiers() -> None:
    """User-port regex templates can contain normal regex braces."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            quests=(
                replace(
                    course.quests[0],
                    validation=UserPortFileValidation(
                        path="~/.config/systemd/user/site.service",
                        required_regex_template=r"http\.server [0-9]{1,5} {port}",
                    ),
                ),
            ),
        ),
    )

    assert isinstance(course_catalog.quest("prove-shell-alive").validation, UserPortFileValidation)


def test_course_catalog_accepts_generated_file_data() -> None:
    """Generated quest data strategies can be attached to quests."""
    course = _course()
    course_catalog = CourseCatalog(
        replace(
            course,
            quests=(
                replace(
                    course.quests[0],
                    data=GeneratedFileData(
                        path_template="~/playground/{quest_id}.txt",
                        generator="word-list",
                        seed_strategy="learner+quest",
                    ),
                ),
            ),
        ),
    )

    assert isinstance(course_catalog.quest("prove-shell-alive").data, GeneratedFileData)


def test_course_catalog_rejects_invalid_validation_regex() -> None:
    """Regex validators fail during catalog validation, not during learner checks."""
    course = _course()

    with pytest.raises(ValueError, match="invalid command history pattern"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=CommandHistoryValidation(
                            required_patterns=("(",),
                            observed_commands=("ls",),
                        ),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="invalid file check regex"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=FileCheckValidation(path="~/file", required_regex="("),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize(
    ("validation", "error_pattern"),
    [
        (
            InteractiveQuestionValidation(question="What happened?", required_concepts=()),
            "missing interactive answer concept",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(
                    AnswerConcept(id="", aliases=(r"thing",), rubric="The answer identifies it."),
                ),
            ),
            "empty interactive answer concept id",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(
                    AnswerConcept(id="thing", aliases=(), rubric="The answer identifies it."),
                ),
            ),
            "missing interactive answer concept alias",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(AnswerConcept(id="thing", aliases=(r"thing",), rubric=" "),),
            ),
            "empty interactive answer concept rubric",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(
                    AnswerConcept(
                        id="thing",
                        aliases=("(",),
                        rubric="The answer identifies it.",
                    ),
                ),
            ),
            "invalid interactive answer concept alias",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(
                    AnswerConcept(
                        id="thing",
                        aliases=(r"thing",),
                        rubric="The answer identifies it.",
                        forbidden_patterns=("(",),
                    ),
                ),
            ),
            "invalid interactive answer forbidden pattern",
        ),
        (
            InteractiveQuestionValidation(
                question="What happened?",
                required_concepts=(
                    AnswerConcept(
                        id="thing",
                        aliases=(r"thing",),
                        rubric="The answer identifies the first thing.",
                    ),
                    AnswerConcept(
                        id="thing",
                        aliases=(r"other",),
                        rubric="The answer identifies the other thing.",
                    ),
                ),
            ),
            "duplicate interactive answer concept ids",
        ),
    ],
)
def test_course_catalog_rejects_bad_interactive_answer_concepts(
    validation: QuestValidation,
    error_pattern: str,
) -> None:
    """Interactive answer concepts must have stable ids and valid regexes."""
    course = _course()

    with pytest.raises(ValueError, match=error_pattern):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], validation=validation),),
            ),
        )


def test_course_catalog_rejects_missing_command_history_commands() -> None:
    """Command-history regexes declare the command forms they validate."""
    course = _course()

    with pytest.raises(ValueError, match="missing command history command"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=CommandHistoryValidation(
                            required_patterns=(r"^ls$",),
                            observed_commands=(),
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_unlisted_command_history_commands() -> None:
    """Command-history validators cannot smuggle commands outside quest intent."""
    course = _course()

    with pytest.raises(ValueError, match="quest validation references unlisted command"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=CommandHistoryValidation(
                            required_patterns=(r"^grep .+$",),
                            observed_commands=("grep",),
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_pathological_command_history_regex() -> None:
    """Command-history regexes reject obvious nested-repeat patterns."""
    course = _course()

    with pytest.raises(ValueError, match="pathological command history pattern"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=CommandHistoryValidation(
                            required_patterns=(r"^(ls+)+$",),
                            observed_commands=("ls",),
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_invalid_forbidden_file_check_regex() -> None:
    """Forbidden file regexes are compiled during catalog validation."""
    course = _course()

    with pytest.raises(ValueError, match="invalid forbidden file check regex"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=FileCheckValidation(
                            path="~/file",
                            required_regex=r".",
                            forbidden_regex="(",
                        ),
                    ),
                ),
            ),
        )


def test_course_catalog_rejects_bad_user_port_file_validation() -> None:
    """User-port validation must declare a usable regex template."""
    course = _course()

    with pytest.raises(ValueError, match="user port file regex template must include port"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=UserPortFileValidation(
                            path="~/.config/systemd/user/site.service",
                            required_regex_template=r"http\.server [0-9]+",
                        ),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="invalid user port file regex template"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=UserPortFileValidation(
                            path="~/.config/systemd/user/site.service",
                            required_regex_template="({port}",
                        ),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize(
    "validation",
    [
        FileCheckValidation(path="/etc/passwd", required_regex=r"."),
        FileCheckValidation(path="public_html/index.html", required_regex=r"."),
        FileCheckValidation(path="~", required_regex=r"."),
        UserPortFileValidation(path="~", required_regex_template=r"{port}"),
        PathExistsValidation(paths=("~", "~/public_html/index.html", "public_html/index.html")),
        ExecutablePathValidation(paths=("~/bin/run", "bin/run", "/usr/local/bin/tool")),
    ],
)
def test_course_catalog_accepts_validation_path_declarations(
    validation: QuestValidation,
) -> None:
    """Validation paths support learner-home, relative, and exact absolute declarations."""
    course = _course()

    CourseCatalog(
        replace(
            course,
            quests=(replace(course.quests[0], validation=validation),),
        ),
    )


@pytest.mark.parametrize(
    ("validation", "error_pattern"),
    [
        (FileCheckValidation(path="", required_regex=r"."), "empty file check path"),
        (FileCheckValidation(path=r"~\file", required_regex=r"."), "must be POSIX-style"),
        (PathExistsValidation(paths=("../outside",)), "must not contain traversal"),
        (ExecutablePathValidation(paths=("~/../run.sh",)), "must not contain traversal"),
        (
            FileCheckValidation(path="safe/./file", required_regex=r"."),
            "must not contain traversal",
        ),
        (FileCheckValidation(path="~alice/file", required_regex=r"."), "must use ~ or ~/"),
    ],
)
def test_course_catalog_rejects_unsafe_validation_paths(
    validation: QuestValidation,
    error_pattern: str,
) -> None:
    """Validation path declarations reject traversal and non-POSIX forms."""
    course = _course()

    with pytest.raises(ValueError, match=error_pattern):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], validation=validation),),
            ),
        )


def test_course_catalog_rejects_unknown_validation_object() -> None:
    """Validation errors stay deterministic for unexpected validator objects."""
    course = _course()

    with pytest.raises(ValueError, match="unknown quest validation: object"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=cast("QuestValidation", object()),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize(
    ("generated_file_data", "error_pattern"),
    [
        (
            GeneratedFileData(
                path_template="",
                generator="word-list",
                seed_strategy="learner+quest",
            ),
            "empty generated file path template",
        ),
        (
            GeneratedFileData(
                path_template="~/playground/{quest_id}.txt",
                generator="",
                seed_strategy="learner+quest",
            ),
            "empty generated file generator",
        ),
        (
            GeneratedFileData(
                path_template="/home/other/{quest_id}.txt",
                generator="word-list",
                seed_strategy="learner+quest",
            ),
            "generated file path template must be learner-owned",
        ),
        (
            GeneratedFileData(
                path_template="~",
                generator="word-list",
                seed_strategy="learner+quest",
            ),
            "generated file path template must identify a learner-owned artifact",
        ),
        (
            GeneratedFileData(
                path_template="~/playground/{quest_id}.txt",
                generator="word-list",
                seed_strategy=cast("Literal['learner+quest']", "learner"),
            ),
            "unknown generated data seed strategy",
        ),
    ],
)
def test_course_catalog_rejects_invalid_generated_file_data(
    generated_file_data: GeneratedFileData,
    error_pattern: str,
) -> None:
    """Generated quest data strategies must be usable by deterministic services."""
    course = _course()

    with pytest.raises(ValueError, match=error_pattern):
        CourseCatalog(
            replace(
                course,
                quests=(replace(course.quests[0], data=generated_file_data),),
            ),
        )


def test_course_catalog_rejects_empty_catalog_text() -> None:
    """Titles, prompts, command names, and skill names cannot be empty."""
    course = _course()

    with pytest.raises(ValueError, match="empty quest prompt"):
        CourseCatalog(replace(course, quests=(replace(course.quests[0], prompt=""),)))

    with pytest.raises(ValueError, match="empty course tutor system prompt"):
        CourseCatalog(replace(course, tutor_system_prompt=""))

    with pytest.raises(ValueError, match="empty session objective prompt"):
        CourseCatalog(
            replace(
                course,
                sessions=(
                    replace(
                        course.sessions[0],
                        objectives=(
                            SessionObjective(
                                id="objective",
                                title="Objective",
                                prompt="",
                                validation=CommandHistoryValidation(
                                    required_patterns=(r"^ls$",),
                                    observed_commands=("ls",),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        )

    with pytest.raises(ValueError, match="empty session command"):
        CourseCatalog(
            replace(
                course,
                sessions=(replace(course.sessions[0], introduced_commands=("",)),),
            ),
        )

    with pytest.raises(ValueError, match="missing executable path"):
        CourseCatalog(
            replace(
                course,
                quests=(
                    replace(
                        course.quests[0],
                        validation=ExecutablePathValidation(paths=()),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="empty session skill"):
        CourseCatalog(
            replace(
                course,
                sessions=(replace(course.sessions[0], introduced_skills=("",)),),
            ),
        )


def _course(
    course_id: str = "lf2607",
    title: str = "Linux Foundations",
) -> Course:
    return Course(
        id=course_id,
        title=title,
        tutor_system_prompt="Teach Linux with short guiding questions.",
        timezone="Asia/Singapore",
        starts_on=date(2026, 7, 11),
        ends_on=date(2026, 7, 13),
        sessions=(
            _session(
                session_id="S1",
                session_date=date(2026, 7, 11),
                commands=("ls",),
                skills=("filesystem-navigation",),
            ),
            _session(
                session_id="S2",
                session_date=date(2026, 7, 13),
                commands=("grep",),
                skills=("pipes",),
            ),
        ),
        quests=(_quest(),),
        tiers=(
            Tier(id="newcomer", minimum_score=0, title="Newcomer"),
            Tier(id="apprentice", minimum_score=100, title="Apprentice"),
        ),
    )


def _session(
    session_id: str,
    session_date: date,
    commands: tuple[str, ...],
    skills: tuple[str, ...],
) -> Session:
    return Session(
        id=session_id,
        title=f"Session {session_id}",
        date=session_date,
        starts_at=datetime.combine(session_date, datetime.min.time(), tzinfo=UTC),
        introduced_commands=commands,
        introduced_skills=skills,
        learning_objectives=("Learn one thing.",),
        content=(
            _content_reference(
                f"{session_id}-slides",
                f"content/course/sessions/{session_id}/slides.md",
                "slides",
                "slides",
            ),
            _content_reference(
                f"{session_id}-self-study",
                f"content/course/sessions/{session_id}/self-study.md",
                "learner",
                "self-study",
            ),
            _content_reference(
                f"{session_id}-recap",
                f"content/course/sessions/{session_id}/recap.md",
                "learner",
                "recap",
            ),
        ),
    )


def _quest() -> Quest:
    return Quest(
        id="prove-shell-alive",
        title="List files",
        sequence=1,
        available_after_session="S1",
        story="The shell should answer a simple question first.",
        learner_goal="Run one command and understand the output.",
        prompt="Run `ls`.",
        autonomy_checklist=("Run `ls`.", "Read the output.", "Ask for a check."),
        hints=(
            Hint(level=1, text="Look at your prompt."),
            Hint(level=2, text="Type the command name."),
            Hint(level=3, text="Type `ls` and press enter."),
        ),
        failure_feedback=(
            FailureFeedback(reason="missing-command", text="Run `ls` and ask again."),
        ),
        docs=(
            _content_reference(
                "prove-shell-alive-doc",
                "content/course/quests/prove-shell-alive.md",
                "learner",
                "quest",
            ),
        ),
        required_commands=("ls",),
        practiced_skills=("filesystem-navigation",),
        score=25,
        validation=CommandHistoryValidation(
            required_patterns=(r"^ls$",),
            observed_commands=("ls",),
        ),
    )


def _content_reference(
    content_id: str,
    path: str,
    audience: ContentAudience,
    purpose: ContentPurpose,
) -> ContentReference:
    return ContentReference(
        id=content_id,
        title=f"{content_id} title",
        path=path,
        audience=audience,
        purpose=purpose,
    )

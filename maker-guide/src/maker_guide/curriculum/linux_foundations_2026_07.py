"""Linux Foundations July 2026 curriculum catalog."""

from __future__ import annotations

import textwrap
from collections.abc import Iterable
from datetime import UTC, date, datetime
from types import MappingProxyType

from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConcept,
    CommandHistoryValidation,
    ContentReference,
    Course,
    ExecutablePathValidation,
    FailureFeedback,
    FileCheckValidation,
    FileMatchesPathValidation,
    GitTrackedPathValidation,
    Hint,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    IrcCtcpVersionValidation,
    LearnerHandleQuestionValidation,
    OwnedPathValidation,
    PathExistsValidation,
    Quest,
    QuestValidation,
    Session,
    SessionObjective,
    SiteCheckValidation,
    SshPublicKeyObservedValidation,
    Tier,
    UserPortFileValidation,
)

COURSE_ID = "lf2607"
_KEEP_PIPELINE_COPY_PATTERN = (
    r"^cut -d: -f7 /etc/passwd\s*\|\s*tee ~/playground/login-shells\.txt\s*\|\s*wc -l$"
)
_COMBINE_STANDARD_STREAMS_PATTERN = (
    r"^date --debug \+%F 2>&1\s*\|\s*tee ~/playground/combined\.txt\s*\|\s*wc -l$"
)
_S5_KNOWN_COMMANDS_SCRIPT_PATTERN = (
    r"(?ms)\A"
    r"(?=.*^[ \t]*whoami[ \t]*(?:#.*)?$)"
    r"(?=.*^[ \t]*hostname[ \t]*(?:#.*)?$)"
    r"(?=.*^[ \t]*date[ \t]*(?:#.*)?$)"
    r".+\Z"
)
_S5_SHEBANG_PATTERN = r"\A#!/bin/bash(?:\n|\Z)"
_S5_REPORT_TITLE_SCRIPT_PATTERN = (
    r"""(?ms)\A"""
    r"""(?=.*^[ \t]*report_title=(?:"\$(?:1|\{1\})"|\$(?:1|\{1\}))[ \t]*(?:#.*)?$"""
    r"""(?=.*^[ \t]*printf[ \t]+(?:"""
    r"""(?:'[^'\n]*(?<!%)%s[^'\n]*'|"[^"\n]*(?<!%)%s[^"\n]*")[ \t]+"""
    r"""(?:"\$(?:report_title|\{report_title\})"|\$(?:report_title|\{report_title\}))"""
    r"""|"\$(?:report_title|\{report_title\})\\n")[ \t]*(?:#.*)?$))"""
    r""".+\Z"""
)
_S5_REPORT_HEADING_SCRIPT_PATTERN = (
    r"""(?ms)\A"""
    r"""(?=.*^[ \t]*report_title=(?:"\$(?:1|\{1\})"|\$(?:1|\{1\}))[ \t]*(?:#.*)?$"""
    r""".*?^[ \t]*printf[ \t]+(?:'#[ \t]+%s\\n(?:\\n)?'|"#[ \t]+%s\\n(?:\\n)?")"""
    r"""[ \t]+"\$(?:report_title|\{report_title\})"[ \t]*(?:#.*)?$)"""
    r""".+\Z"""
)
_S5_REPORT_LABELS_SCRIPT_PATTERN = (
    r"""(?ms)\A"""
    r"""(?=.*^[ \t]*printf[ \t]+(?:'\*[ \t]+User:[ \t]*'|"\*[ \t]+User:[ \t]*")"""
    r"""[ \t]*(?:#.*)?$\n[ \t]*whoami[ \t]*(?:#.*)?$)"""
    r"""(?=.*^[ \t]*printf[ \t]+(?:'\*[ \t]+Host:[ \t]*'|"\*[ \t]+Host:[ \t]*")"""
    r"""[ \t]*(?:#.*)?$\n[ \t]*hostname[ \t]*(?:#.*)?$)"""
    r"""(?=.*^[ \t]*printf[ \t]+(?:'\*[ \t]+Date:[ \t]*'|"\*[ \t]+Date:[ \t]*")"""
    r"""[ \t]*(?:#.*)?$\n[ \t]*date[ \t]*(?:#.*)?$)"""
    r""".+\Z"""
)
_S5_REPORT_PIPELINE_PATTERN = (
    r"(?m)^[ \t]*cut[ \t]+-d:[ \t]+-f7[ \t]+/etc/passwd"
    r"[ \t]*\|[ \t]*sort[ \t]+-u[ \t]*(?:#.*)?$"
)
_S5_REPORT_DESTINATION_SCRIPT_PATTERN = (
    r"(?ms)\A"
    r"(?=.*^[ \t]*(?:\{|\()[ \t]*(?:#.*)?$"
    r".*?^[ \t]*(?:\}|\))[ \t]*>[ \t]*~/src/pages/maker-report\.md[ \t]*(?:#.*)?$)"
    r".+\Z"
)
_S5_REPORT_FENCES_SCRIPT_PATTERN = (
    r"""(?ms)\A"""
    r"""(?=.*^[ \t]*printf[^\n]*(?:```(?:text)?\\n|'%s\\n'[ \t]+'```(?:text)?')[^\n]*$"""
    r""".*?^[ \t]*cut[^\n]*$"""
    r""".*?^[ \t]*printf[ \t]+(?:'```\\n'|"```\\n"|'%s\\n'[ \t]+'```')[ \t]*(?:#.*)?$"""
    r""".*?^[ \t]*(?:\}|\))[ \t]*>[ \t]*~/src/pages/maker-report\.md[ \t]*(?:#.*)?$)"""
    r""".+\Z"""
)
_S5_MARKDOWN_REPORT_PATTERN = (
    r"(?ms)\A#[ \t]+\S[^\n]*\n"
    r"(?=.*?^\*[ \t]+User:[^\n]*$)"
    r"(?=.*?^\*[ \t]+Host(?:name)?:[^\n]*$)"
    r"(?=.*?^\*[ \t]+Date:[^\n]*$)"
    r"(?=.*?^##[ \t]+Shell fields in /etc/passwd[ \t]*:?[ \t]*$)"
    r"(?=.*?^```(?:text)?[ \t]*$)"
    r"(?=.*?^/[^\n]+$)"
    r".*?^```[ \t]*$\n?\Z"
)
_S5_HTML_REPORT_PATTERN = (
    r"(?is)<h1[^>]*>.+?</h1>.*User:.*Host(?:name)?:.*Date:.*"
    r"<h2[^>]*>Shell fields in /etc/passwd:?</h2>"
)
_S5_HOME_TITLED_REPORT_COMMAND_PATTERN = (
    r"^(?:(?:bash|/bin/bash)[ \t]+)?~/scripts/maker-report\.sh[ \t]+"
    r"""(?:"[^"]+"|'[^']+')$"""
)
_S5_UPTIME_SCRIPT_PATTERN = (
    r"(?im)^\s*(?:printf|echo)\b[^\n]*\bUptime\b[^\n]*"
    r"(?:\n[^\n]*){0,2}\n\s*uptime\b"
)
_S5_UPTIME_REPORT_PATTERN = r"(?m)^\*[ \t]+Uptime:[ \t]*(?:\S|\n[ \t]*(?![#*])\S)"
_S5_UPTIME_HTML_PATTERN = r"(?is)Uptime:\s*[^<\n]*\bup\s+\d"
_CLASSROOM_HOSTNAME_PATTERN = r"(?:lf2607|lf-dev)\.kolamayermakers\.org"
_STATIC_HOMEPAGE_COMMAND_PATTERN = (
    r"""^curl -I (?:--max-time [0-9]+ )?(?:(?P<quote>["']?)"""
    rf"""https://{_CLASSROOM_HOSTNAME_PATTERN}/~"""
    r"""[a-z_][a-z0-9_-]*/(?P=quote)|(?P<variable_quote>"?)"""
    rf"""https://{_CLASSROOM_HOSTNAME_PATTERN}/~"""
    r"""\$(?:USER|\{USER\})/(?P=variable_quote))$"""
)
_SERVICE_HOMEPAGE_COMMAND_PATTERN = (
    r"""^curl -I (?:--max-time [0-9]+ )?(?:(?P<quote>["']?)https://[a-z_][a-z0-9_-]*"""
    rf"""\.{_CLASSROOM_HOSTNAME_PATTERN}/(?P=quote)|(?P<variable_quote>"?)"""
    r"""https://\$(?:USER|\{USER\})"""
    rf"""\.{_CLASSROOM_HOSTNAME_PATTERN}/(?P=variable_quote))$"""
)
_LOCAL_SERVICE_COMMAND_PATTERN = (
    r'^curl -I (?:--max-time [0-9]+ )?"?http://127\.0\.0\.1:'
    r'(?:[0-9]+|\$PORT|\$\{PORT\})/"?$'
)
_SOURCE_HANDOFF_PATHS = (
    "README.md",
    "scripts/maker-report.sh",
    "scripts/site-check.sh",
    "scripts/site.sh",
    "services/site.service",
    "services/site-build.service",
    "services/site-build.timer",
)
_S6_SITE_CHECK_PROMPT = (
    "Finish `~/scripts/site-check.sh PAGE [PAGE ...]` to query any supplied page paths. "
    'Use `bash ~/scripts/site-check.sh "" maker-report.html` for homepage and report; '
    "an empty argument selects home, while no arguments must print usage and exit nonzero. "
    "Report HTTP 200 as OK only when curl succeeds; "
    "diagnose other statuses and suggest maker-report.sh plus build-website for report 404. "
    "For other missing pages, do not suggest report regeneration. "
    "Handle connection failures and still check remaining pages, even if curl prints 200 "
    "but exits nonzero. Equivalent variables, functions, case statements, and page order are "
    "accepted; the reference example is not mandatory. Run `guide now` or `guide check` in "
    "the classroom shell to run simulated checks locally. Separately run the script against "
    "your live site and inspect both pages in a browser; simulated completion does not prove "
    "the live site works."
)
_EXECUTABLE_NOT_FILE_PATTERN = (
    r"\b(executable|program|binary)\b.{0,12}\b(isn't|is not|means not|never)\s+"
    r"(a )?(file|disk)\b"
)
_PROCESS_NOT_RUNNING_PATTERN = (
    r"\bprocess\b.{0,20}\b(is|means)\s+(not|never)\s+(a )?(running|instance)\b"
)
_PIPE_RELATION_CONCEPT = AnswerConcept(
    id="pipe-output-to-input",
    rubric=(
        "The answer must identify the stream leaving cut as stdout and the stream wc reads as "
        "stdin. Because the question asks how the pipe connects those streams, concise wording "
        "such as 'stdout leaves cut, wc reads stdin' demonstrates the concept without repeating "
        "that the pipe joins them. Saying cut's stdout goes elsewhere, wc's stdin comes from "
        "elsewhere, or either side is not connected through the pipe contradicts the concept."
    ),
    aliases=(
        r"\bcut(?:'s)? stdout\b.{0,12}\bbecomes\b.{0,12}\bwc(?:'s)? stdin\b",
        r"\bstdout\b.{0,12}\bleaves\b.{0,12}\bcut\b.{0,20}\bwc\b.{0,12}\breads\b.{0,12}\bstdin\b",
        "".join(  # noqa: FLY002
            (
                r"\bcut\b.{0,20}\b(?:writes|sends|feeds|produces)\b.{0,20}\bstdout\b",
                r".{0,20}\b(?:to|into)\b.{0,20}\bwc(?:'s)?\s+stdin\b",
            ),
        ),
        "".join(  # noqa: FLY002
            (
                r"\bwc\b.{0,20}\b(?:reads|receives|gets)\b.{0,20}\bstdin\b",
                r".{0,20}\bfrom\b.{0,20}\bcut(?:'s)?\s+stdout\b",
            ),
        ),
    ),
    forbidden_patterns=(
        r"\bcut (?:doesn't|does not) (?:write|send|produce)\b.{0,20}\bstdout\b",
        r"\bcut never (?:writes|sends|produces)\b.{0,20}\bstdout\b",
        r"\bcut (?:writes|sends|produces) (?:no|not) stdout\b",
        r"\bcut(?:'s)? stdout\b.{0,12}\b(?:isn't|is not|never)\b.{0,12}\bpipe\b",
        r"\bcut(?:'s)? stdout\b.{0,12}\bdoes(?:n't| not) feed\b.{0,12}\bpipe\b",
        r"\bwc (?:doesn't|does not) (?:read|receive|get)\b.{0,20}\bstdin\b",
        r"\bwc never (?:reads|receives|gets)\b.{0,20}\bstdin\b",
        r"\bwc (?:reads|receives|gets) (?:no|not) stdin\b",
        r"\bwc(?:'s)? stdin\b.{0,12}\b(?:isn't|is not|never) connected\b.{0,12}\bcut\b",
        r"\bwc(?:'s)? stdin\b.{0,12}\bdoes(?:n't| not) receive\b.{0,12}\bcut\b",
    ),
)

_STDOUT_DESCRIPTOR_CONCEPT = AnswerConcept(
    id="stdout-descriptor",
    rubric=(
        "The answer must identify stdout as file descriptor 1. Assigning stdout descriptor 0 "
        "contradicts this concept."
    ),
    aliases=(
        r"\bstdout\s*[/=:]\s*1\b",
        r"\bstdout\s+is\s+(?:file\s+)?descriptor\s+1\b",
        r"\bstdout(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b1\b\)?",
        r"\bstdout\s+on\s+(?:file\s+)?descriptor\s+1\b",
        r"\bstdout\b[^.;]{0,40}[.;]\s*it is (?:file )?descriptor 1\b",
        r"(?:\bdescriptor\s+)?\b1\b\s+is\s+stdout\b",
        r"\b1\s*=\s*stdout\b",
    ),
    forbidden_patterns=(
        r"\bstdout\s*[/=:]\s*0\b",
        r"\bstdout\s+is\s+(?:file\s+)?descriptor\s+0\b",
        r"\bstdout(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b0\b\)?",
        r"\bstdout\s+on\s+(?:file\s+)?descriptor\s+0\b",
        r"(?:\bdescriptor\s+)?\b0\b\s+is\s+stdout\b",
        r"\b0\s*=\s*stdout\b",
    ),
)
_STDIN_DESCRIPTOR_CONCEPT = AnswerConcept(
    id="stdin-descriptor",
    rubric=(
        "The answer must identify stdin as file descriptor 0. Assigning stdin descriptor 1 "
        "contradicts this concept."
    ),
    aliases=(
        r"\bstdin\s*[/=:]\s*0\b",
        r"\bstdin\s+is\s+(?:file\s+)?descriptor\s+0\b",
        r"\bstdin(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b0\b\)?",
        r"\bstdin\s+on\s+(?:file\s+)?descriptor\s+0\b",
        r"\bstdin\b[^.;]{0,40}[.;]\s*it is (?:file )?descriptor 0\b",
        r"(?:\bdescriptor\s+)?\b0\b\s+is\s+stdin\b",
        r"\b0\s*=\s*stdin\b",
    ),
    forbidden_patterns=(
        r"\bstdin\s*[/=:]\s*1\b",
        r"\bstdin\s+is\s+(?:file\s+)?descriptor\s+1\b",
        r"\bstdin(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b1\b\)?",
        r"\bstdin\s+on\s+(?:file\s+)?descriptor\s+1\b",
        r"(?:\bdescriptor\s+)?\b1\b\s+is\s+stdin\b",
        r"\b1\s*=\s*stdin\b",
    ),
)
_STDERR_DESCRIPTOR_CONCEPT = AnswerConcept(
    id="stderr-descriptor",
    rubric=(
        "The answer must identify stderr as file descriptor 2. Assigning stderr descriptor 0 "
        "or 1 contradicts this concept."
    ),
    aliases=(
        r"^stderr$",
        r"\bstderr\s+is\s+(?:file\s+)?descriptor\s+2\b",
        r"\bstderr(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b2\b\)?",
        r"(?:\bdescriptor\s+)?\b2\b\s+(?:is|means|names)\s+stderr\b",
        r"\b2\s*=\s*stderr\b",
    ),
    forbidden_patterns=(
        r"\bstderr\s+is\s+(?:file\s+)?descriptor\s+[01]\b",
        r"\bstderr(?:(?:\s+|[,;:]\s*)descriptor)?\s*(?:\(|is\s+)?\b[01]\b\)?",
        r"(?:\bdescriptor\s+)?\b[01]\b\s+(?:is|means|names)\s+stderr\b",
        r"\b[01]\s*=\s*stderr\b",
        r"\bstderr\b.{0,12}\bis\s+\b2\b\s*(?:,?\s*(?:and|or)|/)\s*\b[01]\b",
    ),
)
_LEFT_TO_RIGHT_REDIRECTION_CONCEPT = AnswerConcept(
    id="left-to-right-redirection",
    rubric=(
        "The answer must state that the shell applies redirections from left to right. "
        "Claiming right-to-left evaluation contradicts this concept."
    ),
    aliases=(
        r"\bredirections?\b.{0,30}\bleft(?:-| )to(?:-| )right\b",
        r"\bleft(?:-| )to(?:-| )right\b.{0,30}\bredirections?\b",
    ),
    forbidden_patterns=(
        r"\bredirections?\b.{0,30}\bright(?:-| )to(?:-| )left\b",
        r"\bright(?:-| )to(?:-| )left\b.{0,30}\bredirections?\b",
        r"\bredirections?\b.{0,20}\b(?:not|never)\b.{0,20}\bleft[- ]to[- ]right\b",
    ),
)
_STDERR_TO_STDOUT_DESTINATION_CONCEPT = AnswerConcept(
    id="stderr-follows-stdout",
    rubric=(
        "The answer must explain that 2>&1 sends stderr to stdout's current destination. "
        "Reversing that direction or saying stderr does not follow stdout contradicts it."
    ),
    aliases=(
        "".join(  # noqa: FLY002
            (
                r"\b2>&1\b.{0,30}\b(?:stderr|descriptor\s+2)\b.{0,20}",
                r"\b(?:to|into|at|follows?|wherever)\b.{0,20}\bstdout\b",
            ),
        ),
    ),
    forbidden_patterns=(
        r"\b2>&1\b.{0,30}\bstdout\b.{0,20}\b(?:to|into|follows?)\b.{0,20}\bstderr\b",
        r"\b2>&1\b.{0,20}\b(?:not|never)\b.{0,20}\b(?:stderr|descriptor\s+2)\b",
        r"\b(?:stderr|descriptor\s+2)\b.{0,15}\b(?:not|never)\b.{0,15}\bstdout\b",
        "".join(  # noqa: FLY002
            (
                r"\b2>&1\b.{0,30}\b(?:stderr|descriptor\s+2)\b.{0,20}",
                r"\b(?:away\s+from|other\s+than|instead\s+of|opposite(?:\s+to)?)\b",
                r".{0,20}\bstdout\b",
            ),
        ),
        r"\bstdout(?:'s)?\s+current\s+destination\b.{0,20}\b(?:not|never)\b",
    ),
)
_EXECUTABLE_FILE_CONCEPT = AnswerConcept(
    id="executable-file",
    rubric=(
        "The answer must distinguish an executable as a program file stored on disk. Saying "
        "an executable is itself a running process or is not a file contradicts this concept."
    ),
    aliases=(
        "".join(  # noqa: FLY002
            (
                r"\b(?:executable|program|binary executable|binary)\b\s+",
                r"(?:is|means|remains)\s+(?:an?\s+)?",
                r"(?:binary\s+|executable\s+|program\s+)*file\b",
            ),
        ),
        "".join(  # noqa: FLY002
            (
                r"\b(?:executable|program|binary executable|binary)\b.{0,12}",
                r"\b(?:is\s+)?stored\s+(?:(?:as|in)\s+(?:an?\s+)?file\s+)?",
                r"(?:on|in)\s+(?:the\s+)?disk\b",
            ),
        ),
        "".join(  # noqa: FLY002
            (
                r"\bfile\b(?:\s+stored)?\s+on\s+(?:the\s+)?disk\b.{0,20}",
                r"\b(?:is\s+)?(?:an?\s+)?(?:executable|program|binary)\b",
            ),
        ),
    ),
    forbidden_patterns=(
        _EXECUTABLE_NOT_FILE_PATTERN,
        r"\bexecutable file (is|means) (a )?(running )?process\b",
        r"\bbinary executable (is|means) (a )?(running )?process\b",
        r"\bbinary file (is|means) (a )?(running )?process\b",
        r"\b(executable|binary) (is|means) (a )?(running )?process\b",
        r"\bprogram file\s+(is|means)\s+(a )?(running )?process\b",
    ),
)
_RUNNING_PROCESS_CONCEPT = AnswerConcept(
    id="running-process",
    rubric=(
        "The answer must describe a process as a running instance of a program. Saying a "
        "process is merely the file on disk or is not running contradicts this concept."
    ),
    aliases=(
        r"\bprocess\s+(?:is|means)\s+(?:a\s+)?running\s+instance\b",
        r"\bprocess\s+runs?\s+as\s+(?:an?\s+)?(?:running\s+)?instance\b",
        "".join(  # noqa: FLY002
            (
                r"\bprocess\s+(?:is|means)\s+(?:an?\s+)?instance\s+of\s+(?:a\s+)?",
                r"running\s+(?:program|executable)\b",
            ),
        ),
        "".join(  # noqa: FLY002
            (
                r"\bprocess\s+is\s+not\s+(?:a\s+)?file[,;:]?\s+",
                r"(?:(?:but|and)\s+)?(?:it\s+)?is\s+(?:a\s+)?running\s+instance\b",
            ),
        ),
        r"\brunning\s+instance\b.{0,20}\b(?:is\s+)?(?:a\s+)?process\b",
        r"\b(?:runs?|executes?|starts?)\b.{0,20}\bcreates?\s+(?:a\s+)?process\b",
    ),
    forbidden_patterns=(
        _PROCESS_NOT_RUNNING_PATTERN,
        r"\bprocess\b.{0,20}\b(is|means)\b(?!\s+(not|never)\b).{0,20}\b(file|disk)\b",
    ),
)
# ponytail: stdout is not captured, so this checks the reported pair's shape, not provenance.
_REPORTED_PROCESS_PAIR_CONCEPT = AnswerConcept(
    id="reported-process-pair",
    rubric=(
        "The answer must report one positive numeric PID together with its command name. "
        "Denying that the reported command belongs to the PID contradicts this concept."
    ),
    aliases=(
        r"\bpid\s+[1-9][0-9]*\b.{0,30}\bcommand\s+[a-z0-9_./+:-]+\b",
        r"\bcommand\s+[a-z0-9_./+:-]+\b.{0,30}\bpid\s+[1-9][0-9]*\b",
    ),
    forbidden_patterns=(r"\bpid\s+[1-9][0-9]*\b.{0,20}\b(?:not|never)\b.{0,20}\bcommand\b",),
)
_QUEST_SPECIFIC_FAILURE_REASONS_BY_VALIDATION_TYPE = MappingProxyType(
    {
        CommandHistoryValidation: ("missing-command",),
        IrcCtcpVersionValidation: (
            "missing-irc-ctcp-version",
            "unsupported-irc-client",
        ),
        LearnerHandleQuestionValidation: ("missing-answer", "wrong-answer"),
        PathExistsValidation: ("missing-path",),
        ExecutablePathValidation: ("missing-path", "not-executable", "wrong-owner"),
        OwnedPathValidation: ("missing-path", "wrong-owner"),
        FileMatchesPathValidation: ("missing-path", "file-content-mismatch"),
        SiteCheckValidation: ("missing-path",),
        GitTrackedPathValidation: (
            "missing-path",
            "git-path-not-committed",
            "git-path-modified",
            "git-repository-error",
        ),
        UserPortFileValidation: ("missing-path", "port-content-mismatch"),
    },
)
_FAILURE_FEEDBACK_TEXT_TEMPLATES = MappingProxyType(
    {
        "missing-command": "Run the required command evidence, then try again: {evidence}",
        "missing-answer": (
            "Use `guide answer 'your answer'` with the answer requested by this quest."
        ),
        "missing-concept": "Answer with the required idea for this quest: {evidence}",
        "contradicted-concept": (
            "Your answer contradicts the required idea. Review the evidence: {evidence}"
        ),
        "wrong-owner": "Answer with the learner or owner requested by this quest: {evidence}",
        "wrong-answer": "Answer with the learner or owner requested by this quest: {evidence}",
        "missing-path": "Create the required path or file evidence, then try again: {evidence}",
        "file-content-mismatch": (
            "Update the required file content so this evidence matches: {evidence}"
        ),
        "forbidden-content-present": (
            "Remove the forbidden file content, then try again: {evidence}"
        ),
        "not-executable": (
            "Set the owner executable bit on the required file, then try again: {evidence}"
        ),
        "port-content-mismatch": (
            "Update the service file with your computed port, then try again: {evidence}"
        ),
        "git-path-not-committed": "Commit the required Git path, then try again: {evidence}",
        "git-path-modified": "Commit or discard changes to the required Git path, then try again.",
        "git-repository-error": "Check that the required directory is a working Git repository.",
        "missing-irc-ctcp-version": (
            "Message the guide from terminal IRC so it can verify your IRC client."
        ),
        "unsupported-irc-client": ("Use WeeChat for this quest; browser IRC does not count."),
    },
)
_DEFAULT_FAILURE_FEEDBACK_TEXT_TEMPLATE = "Try again and make sure this evidence exists: {evidence}"


def _session_content(session_id: str, title: str) -> tuple[ContentReference, ...]:
    session_directory = f"S{int(session_id.removeprefix('S')):02d}"
    return (
        ContentReference(
            id=f"{session_id}-slides",
            title=f"{title} presenterm slides",
            path=f"content/{COURSE_ID}/sessions/{session_directory}/slides.md",
            audience="slides",
            purpose="slides",
        ),
        ContentReference(
            id=f"{session_id}-self-study",
            title=f"{title} self-study guide",
            path=f"content/{COURSE_ID}/sessions/{session_directory}/self-study.md",
            audience="learner",
            purpose="self-study",
        ),
        ContentReference(
            id=f"{session_id}-recap",
            title=f"{title} learner recap",
            path=f"content/{COURSE_ID}/sessions/{session_directory}/recap.md",
            audience="learner",
            purpose="recap",
        ),
    )


def _quest_documentation(quest_id: str, title: str) -> tuple[ContentReference, ...]:
    return (
        ContentReference(
            id=f"{quest_id}-quest-doc",
            title=f"{title} quest guide",
            path=f"content/{COURSE_ID}/quests/{quest_id}.md",
            audience="learner",
            purpose="quest",
        ),
    )


def _quest_failure_feedback(
    validation: QuestValidation,
    evidence: str,
) -> tuple[FailureFeedback, ...]:
    return tuple(
        FailureFeedback(
            reason=failure_reason,
            text=_failure_feedback_text(failure_reason, evidence),
        )
        for failure_reason in _quest_specific_failure_reasons(validation)
    )


def _quest_specific_failure_reasons(validation: QuestValidation) -> tuple[str, ...]:
    if isinstance(validation, AllOfValidation):
        return _deduplicated_failure_reasons(
            failure_reason
            for child_validation in validation.validations
            for failure_reason in _quest_specific_failure_reasons(child_validation)
        )
    if isinstance(validation, InteractiveQuestionValidation):
        return (
            "missing-answer",
            "missing-concept",
            *_contradicted_concept_failure_reason(validation),
        )
    if isinstance(validation, FileCheckValidation):
        return (
            "missing-path",
            "file-content-mismatch",
            *_forbidden_content_failure_reason(validation),
        )
    return _QUEST_SPECIFIC_FAILURE_REASONS_BY_VALIDATION_TYPE.get(type(validation), ())


def _contradicted_concept_failure_reason(
    validation: InteractiveQuestionValidation,
) -> tuple[str, ...]:
    if any(concept.forbidden_patterns for concept in validation.required_concepts):
        return ("contradicted-concept",)
    return ()


def _forbidden_content_failure_reason(validation: FileCheckValidation) -> tuple[str, ...]:
    if validation.forbidden_regex is not None:
        return ("forbidden-content-present",)
    return ()


def _deduplicated_failure_reasons(failure_reasons: Iterable[str]) -> tuple[str, ...]:
    deduplicated_failure_reasons: list[str] = []
    for failure_reason in failure_reasons:
        if failure_reason not in deduplicated_failure_reasons:
            deduplicated_failure_reasons.append(failure_reason)
    return tuple(deduplicated_failure_reasons)


def _failure_feedback_text(failure_reason: str, evidence: str) -> str:
    return _FAILURE_FEEDBACK_TEXT_TEMPLATES.get(
        failure_reason,
        _DEFAULT_FAILURE_FEEDBACK_TEXT_TEMPLATE,
    ).format(evidence=evidence)


def _quest(  # noqa: PLR0913
    quest_id: str,
    title: str,
    sequence: int,
    available_after_session: str,
    prompt: str,
    required_commands: tuple[str, ...],
    practiced_skills: tuple[str, ...],
    validation: QuestValidation,
    goal: str,
    evidence: str,
) -> Quest:
    return Quest(
        id=quest_id,
        title=title,
        sequence=sequence,
        available_after_session=available_after_session,
        story=f"This quest turns session {available_after_session} tools into durable practice.",
        learner_goal=goal,
        prompt=prompt,
        autonomy_checklist=(
            "Use the quest guide if you need a reference.",
            prompt,
            evidence,
            "Ask the guide to check your work.",
        ),
        hints=(
            Hint(
                level=1,
                text="Open the quest guide above and run its smallest command step first.",
            ),
            Hint(level=2, text="Run the smallest command that proves one part of the task."),
            Hint(level=3, text=evidence),
        ),
        failure_feedback=_quest_failure_feedback(validation, evidence),
        docs=_quest_documentation(quest_id, title),
        required_commands=required_commands,
        practiced_skills=practiced_skills,
        score=25,
        validation=validation,
    )


LINUX_FOUNDATIONS_2026_07 = Course(
    id=COURSE_ID,
    title="Linux Foundations",
    tutor_system_prompt=textwrap.dedent(
        """
        You are a Linux expert teaching Linux Foundations to novice makers.
        Use the provided learner snapshot, taught commands, quest prompt, and first hint
        as your source of truth.
        Teach with the Socratic method: ask one or two short guiding questions before
        giving direct steps, unless safety or syntax requires direct correction.
        Do not do the work for the learner. Help them reason from shell fundamentals:
        files, permissions, processes, networking, user services, Git, and publishing.
        The Bash hook records every successful learner command automatically; you can see
        recent commands in the snapshot. Never ask the learner to copy or paste command
        output as evidence. When required evidence is missing, name the exact command to
        run in their terminal; validation happens automatically after they run it.
        """,
    ).strip(),
    timezone="Asia/Singapore",
    starts_on=date(2026, 7, 18),
    ends_on=date(2026, 10, 24),
    sessions=(
        Session(
            id="S1",
            title="First contact: SSH and the lay of the land",
            date=date(2026, 7, 18),
            starts_at=datetime(2026, 7, 18, 9, tzinfo=UTC),
            introduced_commands=(
                "ssh",
                "whoami",
                "hostname",
                "date",
                "uptime",
                "pwd",
                "cd",
                "ls",
                "tree",
                "find",
                "cat",
                "bat",
                "less",
                "head",
                "tail",
                "man",
                "tldr",
                "history",
                "build-website",
                "clear",
                "exit",
            ),
            introduced_skills=(
                "linux",
                "unix",
                "filesystem",
                "path",
                "file",
                "directory",
                "io",
                "server",
                "client",
                "ssh-login",
                "terminal",
                "shell",
                "readline",
                "shell-basics",
                "filesystem-navigation",
                "reading-files",
                "manual-pages",
                "first-site-build",
                "filesystem-as-cms",
            ),
            enrichment_skills=(
                "kernel",
                "userspace",
                "syscall",
                "cpu",
                "memory",
                "time-zones",
            ),
            learning_objectives=(
                "SSH into your account.",
                "Understand the shell as text in and text out.",
                "Navigate the filesystem.",
                "Read files and manual pages.",
                "Ship your first page.",
            ),
            content=_session_content("S1", "First contact"),
            objectives=(
                SessionObjective(
                    id="join-course-irc",
                    title="Join the course IRC channel",
                    prompt="Join `#lf2607` at the classroom IRC page.",
                    validation=IrcChannelJoinObservedValidation(channel="#lf2607"),
                ),
                SessionObjective(
                    id="prove-shell-alive",
                    title="Confirm that your shell is working",
                    prompt="Run `whoami`, `date`, and `uptime` separately.",
                    validation=CommandHistoryValidation(
                        required_patterns=(r"^whoami$", r"^date$", r"^uptime$"),
                        observed_commands=("whoami", "date", "uptime"),
                    ),
                ),
                SessionObjective(
                    id="count-home-entries",
                    title="Navigate and inspect your home directory",
                    prompt="Run `ls`.",
                    validation=CommandHistoryValidation(
                        required_patterns=(r"^ls(?:\s|$)",), observed_commands=("ls",)
                    ),
                ),
                SessionObjective(
                    id="read-man-ls",
                    title="Read a manual page",
                    prompt="Run `man ls`, then press `q` to return to the shell.",
                    validation=CommandHistoryValidation(
                        required_patterns=(r"^man ls$",), observed_commands=("man",)
                    ),
                ),
                SessionObjective(
                    id="build-first-site",
                    title="Ship your first page",
                    prompt="Run `build-website` and confirm `~/public_html/index.html` exists.",
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(
                                    r"^(?:build-website|maker-guide-build-personal-website)$",
                                ),
                                observed_commands=("build-website",),
                            ),
                            PathExistsValidation(paths=("~/public_html/index.html",)),
                        ),
                    ),
                ),
            ),
        ),
        Session(
            id="S2",
            title="Files, editing, identity",
            date=date(2026, 7, 25),
            starts_at=datetime(2026, 7, 25, 9, tzinfo=UTC),
            introduced_commands=(
                "touch",
                "mkdir",
                "rmdir",
                "cp",
                "mv",
                "rm",
                "rm -i",
                "rm -rf",
                "micro",
                "echo",
                ">",
                ">>",
                "ssh-keygen",
                "ssh-copy-id",
                "Get-Content",
                "chmod",
                "ls -l",
            ),
            introduced_skills=(
                "file-creation",
                "file-editing",
                "file-manipulation",
                "ssh-keys",
                "markdown-basics",
                "site-source-ownership",
            ),
            learning_objectives=(
                "Set up SSH keys.",
                "Create files and directories.",
                "Edit text with micro.",
                "Move and remove files safely.",
                "Make the homepage your own.",
            ),
            content=_session_content("S2", "Files, editing, identity"),
            objectives=(
                SessionObjective(
                    id="ssh-public-key",
                    title="Connect with an SSH public key",
                    prompt=(
                        "Install your public key on your account, reconnect without entering your "
                        "password, then run a command. The guide records this automatically."
                    ),
                    validation=SshPublicKeyObservedValidation(),
                ),
            ),
        ),
        Session(
            id="S3",
            title="Streams, pipes, processes",
            date=date(2026, 8, 1),
            starts_at=datetime(2026, 8, 1, 9, tzinfo=UTC),
            introduced_commands=(
                "grep",
                "wc",
                "sort",
                "uniq",
                "cut",
                "tee",
                "2>",
                "2>&1",
                "ps",
            ),
            introduced_skills=(
                "pipes",
                "text-search",
                "stream-redirection",
                "file-descriptor",
                "dev-null",
                "process",
                "process-basics",
            ),
            enrichment_skills=("signal", "job-control"),
            learning_objectives=(
                "Name stdin, stdout, and stderr and their file descriptors.",
                "Read redirection left to right, including 2>&1 and /dev/null.",
                "Build useful pipelines and keep a copy with tee.",
                "Explain the difference between an executable file and a running process.",
                "Inspect processes owned by your account.",
            ),
            content=_session_content("S3", "Streams, pipes, processes"),
            objectives=(
                SessionObjective(
                    id="separate-standard-streams",
                    title="Separate stdout and stderr",
                    prompt=(
                        "As a quick preflight, run `mkdir -p ~/playground`. Then run "
                        "`ls /etc/hostname /no/such/path >~/playground/stdout.txt "
                        "2>~/playground/stderr.txt`, inspect both files, and run "
                        "`cat /etc/hostname >/dev/null`."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/playground/stdout.txt",
                                required_regex=r"(?m)^/etc/hostname$",
                                forbidden_regex=r"no/such/path",
                            ),
                            FileCheckValidation(
                                path="~/playground/stderr.txt",
                                required_regex=r"no/such/path",
                                forbidden_regex=r"/etc/hostname",
                            ),
                            CommandHistoryValidation(
                                required_patterns=(r"^cat /etc/hostname\s*>\s*/dev/null$",),
                                observed_commands=("cat /etc/hostname > /dev/null",),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="make-first-pipe",
                    title="Explain a pipe connection",
                    prompt=(
                        "Run `cut -d: -f1 /etc/passwd | wc -l`, then use `guide answer` to "
                        "describe the connection between the stream leaving `cut` and the stream "
                        "that `wc` reads."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r"^cut -d: -f1 /etc/passwd\s*\|\s*wc -l$",),
                                observed_commands=("cut -d: -f1 /etc/passwd | wc -l",),
                            ),
                            InteractiveQuestionValidation(
                                question=(
                                    "How does the pipe connect the stream leaving `cut` to the "
                                    "stream that `wc` reads?"
                                ),
                                required_concepts=(_PIPE_RELATION_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="name-stdout-descriptor",
                    title="Name the stdout descriptor",
                    prompt=(
                        "Run `cut -d: -f1 /etc/passwd | wc -l`, then use `guide answer` to name "
                        "stdout's file descriptor number."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r"^cut -d: -f1 /etc/passwd\s*\|\s*wc -l$",),
                                observed_commands=("cut -d: -f1 /etc/passwd | wc -l",),
                            ),
                            InteractiveQuestionValidation(
                                question="What is stdout's file descriptor number?",
                                required_concepts=(_STDOUT_DESCRIPTOR_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="name-stdin-descriptor",
                    title="Name the stdin descriptor",
                    prompt=(
                        "Run `cut -d: -f1 /etc/passwd | wc -l`, then use `guide answer` to name "
                        "stdin's file descriptor number."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r"^cut -d: -f1 /etc/passwd\s*\|\s*wc -l$",),
                                observed_commands=("cut -d: -f1 /etc/passwd | wc -l",),
                            ),
                            InteractiveQuestionValidation(
                                question="What is stdin's file descriptor number?",
                                required_concepts=(_STDIN_DESCRIPTOR_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="combine-and-copy-streams",
                    title="Identify descriptor 2's stream",
                    prompt=(
                        "Run `date --debug +%F 2>&1 | tee "
                        "~/playground/combined.txt | wc -l`, then use `guide answer` to name the "
                        "stream represented by descriptor 2."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(_COMBINE_STANDARD_STREAMS_PATTERN,),
                                observed_commands=(
                                    "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",
                                ),
                            ),
                            FileCheckValidation(
                                path="~/playground/combined.txt",
                                required_regex=(
                                    r"(?ms)(?=.*^date:[^\n]*%F[^\n]*$)"
                                    r"(?=.*^[0-9]{4}-[0-9]{2}-[0-9]{2}$).+"
                                ),
                            ),
                            InteractiveQuestionValidation(
                                question="What stream is represented by descriptor 2?",
                                required_concepts=(_STDERR_DESCRIPTOR_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="read-redirections-left-to-right",
                    title="Explain redirection order",
                    prompt=(
                        "Run `date --debug +%F 2>&1 | tee "
                        "~/playground/combined.txt | wc -l`, then use `guide answer` to state the "
                        "order in which the shell applies redirections."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(_COMBINE_STANDARD_STREAMS_PATTERN,),
                                observed_commands=(
                                    "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",
                                ),
                            ),
                            FileCheckValidation(
                                path="~/playground/combined.txt",
                                required_regex=(
                                    r"(?ms)(?=.*^date:[^\n]*%F[^\n]*$)"
                                    r"(?=.*^[0-9]{4}-[0-9]{2}-[0-9]{2}$).+"
                                ),
                            ),
                            InteractiveQuestionValidation(
                                question="In what order does the shell apply redirections?",
                                required_concepts=(_LEFT_TO_RIGHT_REDIRECTION_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="route-stderr-to-stdout-destination",
                    title="Trace descriptor duplication",
                    prompt=(
                        "Run `date --debug +%F 2>&1 | tee "
                        "~/playground/combined.txt | wc -l`, then use `guide answer` to explain "
                        "where `2>&1` sends stderr."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(_COMBINE_STANDARD_STREAMS_PATTERN,),
                                observed_commands=(
                                    "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",
                                ),
                            ),
                            FileCheckValidation(
                                path="~/playground/combined.txt",
                                required_regex=(
                                    r"(?ms)(?=.*^date:[^\n]*%F[^\n]*$)"
                                    r"(?=.*^[0-9]{4}-[0-9]{2}-[0-9]{2}$).+"
                                ),
                            ),
                            InteractiveQuestionValidation(
                                question="Where does `2>&1` send stderr?",
                                required_concepts=(_STDERR_TO_STDOUT_DESTINATION_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="read-process-table",
                    title="Inspect your own processes",
                    prompt=(
                        'Run `ps -u "$USER" -o pid,comm,args`, then use `guide answer` to explain '
                        "what an executable program file is."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r'^ps -u "\$USER" -o pid,comm,args$',),
                                observed_commands=("ps",),
                            ),
                            InteractiveQuestionValidation(
                                question="What is an executable program file?",
                                required_concepts=(_EXECUTABLE_FILE_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="describe-running-process",
                    title="Describe a running process",
                    prompt=(
                        'Run `ps -u "$USER" -o pid,comm,args`, then use `guide answer` to describe '
                        "a process."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r'^ps -u "\$USER" -o pid,comm,args$',),
                                observed_commands=("ps",),
                            ),
                            InteractiveQuestionValidation(
                                question="What is a process?",
                                required_concepts=(_RUNNING_PROCESS_CONCEPT,),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="report-process-pair",
                    title="Report a process ID and command",
                    prompt=(
                        'Run `ps -u "$USER" -o pid,comm,args`, then use `guide answer` to report '
                        "one labeled numeric PID and command pair you read."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            CommandHistoryValidation(
                                required_patterns=(r'^ps -u "\$USER" -o pid,comm,args$',),
                                observed_commands=("ps",),
                            ),
                            InteractiveQuestionValidation(
                                question="What labeled numeric PID and command pair did you read?",
                                required_concepts=(_REPORTED_PROCESS_PAIR_CONCEPT,),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        Session(
            id="S4",
            title="Permissions, Git, Forgejo",
            date=date(2026, 8, 8),
            starts_at=datetime(2026, 8, 8, 9, tzinfo=UTC),
            introduced_commands=(
                "git init",
                "git add",
                "git commit",
                "git log",
                "git status",
                "git diff",
                "git remote",
                "git push",
                "fj",
            ),
            introduced_skills=(
                "permissions",
                "git-basics",
                "forgejo-publishing",
                "multi-user-filesystems",
            ),
            learning_objectives=(
                "Read and change file permissions.",
                "Version site source with git.",
                "Create and push the source repository to Forgejo.",
            ),
            content=_session_content("S4", "Permissions, Git, Forgejo"),
            objectives=(
                SessionObjective(
                    id="read-permissions",
                    title="Read and change file permissions",
                    prompt=(
                        "If `~/playground` is missing, run `mkdir -p ~/playground`. Then run "
                        "`cd ~/playground`. Run `touch permission-demo.txt`, then "
                        "`ls -l permission-demo.txt`, use `chmod u+x permission-demo.txt`, "
                        "then inspect it and read the owner permission letters."
                    ),
                    next_steps=(
                        "touch permission-demo.txt",
                        "ls -l permission-demo.txt",
                        "chmod u+x permission-demo.txt",
                    ),
                    next_step_explanations=(
                        "Let's make a harmless file that belongs to you for this exercise.",
                        "Read the file type and its owner, group, and other permission triplets.",
                        "Add execute permission for yourself, then compare what changed.",
                    ),
                    working_directory="~/playground",
                    working_directory_creation_step="mkdir -p ~/playground",
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^touch permission-demo\.txt$",
                            r"^ls -l permission-demo\.txt$",
                            r"^chmod u\+x permission-demo\.txt$",
                        ),
                        observed_commands=("touch", "ls -l", "chmod"),
                    ),
                ),
                SessionObjective(
                    id="initialize-source-repo",
                    title="Initialize the source repository",
                    prompt=(
                        "From `~/src`, run `git init` and inspect `git status`. Then stage with "
                        "`git add --all`, then create its first commit with `git commit -m`."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^git init$",
                            r"^git status$",
                            r"^git add --all$",
                            r"^git commit -m .+",
                        ),
                        observed_commands=("git init", "git status", "git add", "git commit"),
                    ),
                ),
                SessionObjective(
                    id="push-source-to-forgejo",
                    title="Create and push the source repository to Forgejo",
                    prompt=(
                        "From `~/src`, run `fj repo create src`. Your configured class token "
                        "creates an empty repository. "
                        "Then add its HTTPS URL as `origin` and push `main`."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^fj repo create src$",
                            r"^git remote ",
                            r"^git push -u origin main$",
                        ),
                        observed_commands=("fj", "git remote", "git push"),
                    ),
                ),
            ),
        ),
        Session(
            id="S5",
            title="Scripting begins",
            date=date(2026, 8, 29),
            starts_at=datetime(2026, 8, 29, 5, tzinfo=UTC),
            introduced_commands=(
                "bash",
                "printf",
            ),
            introduced_skills=(
                "shell-scripting",
                "shebang",
                "script-permissions",
                "variables",
                "quoting",
                "script-arguments",
            ),
            learning_objectives=(
                "Save familiar commands in a script and run it with Bash.",
                "Run a script directly using a shebang and executable permission.",
                "Use one quoted argument to personalize a script.",
                "Generate and publish a useful Markdown report.",
            ),
            content=_session_content("S5", "Scripting begins"),
            objectives=(
                SessionObjective(
                    id="create-maker-report",
                    title="Save familiar commands in a script",
                    prompt=(
                        "Create `~/scripts/maker-report.sh` with `#!/bin/bash` first, then "
                        "`whoami`, `hostname`, and `date` on separate command lines. From "
                        "`~/scripts`, run it with `bash maker-report.sh`."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_KNOWN_COMMANDS_SCRIPT_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_SHEBANG_PATTERN,
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="run-maker-report-directly",
                    title="Turn the script into an executable command",
                    prompt=(
                        "From `~/scripts`, try `./maker-report.sh` before changing permissions "
                        "and observe `Permission denied`. Inspect with `ls -l`, run "
                        "`chmod u+x maker-report.sh`, verify `#!/bin/bash` with "
                        "`head -n 1 maker-report.sh`, then run `./maker-report.sh`."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_KNOWN_COMMANDS_SCRIPT_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_SHEBANG_PATTERN,
                            ),
                            ExecutablePathValidation(paths=("~/scripts/maker-report.sh",)),
                        ),
                    ),
                ),
                SessionObjective(
                    id="personalize-maker-report",
                    title="Personalize the report with one argument",
                    prompt=(
                        'Assign the first argument with `report_title="$1"`, print it with '
                        '`printf` as `"$report_title"`, compare an unquoted multi-word title '
                        "with one quoted title, and leave the quoted form working."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_KNOWN_COMMANDS_SCRIPT_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_SHEBANG_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_REPORT_TITLE_SCRIPT_PATTERN,
                            ),
                            ExecutablePathValidation(paths=("~/scripts/maker-report.sh",)),
                        ),
                    ),
                ),
                SessionObjective(
                    id="publish-maker-report",
                    title="Generate and publish a useful report",
                    prompt=(
                        "Generate `~/src/pages/maker-report.md` with a `#` title, User, Host, "
                        "and Date information, then `## Shell fields in /etc/passwd` and a fenced "
                        "shell list from `cut -d: -f7 /etc/passwd | sort -u`. Group commands so "
                        'the script writes the file. Run `./maker-report.sh "Your report title"` '
                        "before inspecting it. Then run `build-website`. Open the generated page."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_REPORT_PIPELINE_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/scripts/maker-report.sh",
                                required_regex=_S5_REPORT_DESTINATION_SCRIPT_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/src/pages/maker-report.md",
                                required_regex=_S5_MARKDOWN_REPORT_PATTERN,
                            ),
                            FileCheckValidation(
                                path="~/public_html/maker-report.html",
                                required_regex=_S5_HTML_REPORT_PATTERN,
                            ),
                        ),
                    ),
                ),
            ),
        ),
        Session(
            id="S6",
            title="Is your site actually working?",
            date=date(2026, 9, 12),
            starts_at=datetime(2026, 9, 12, 9, tzinfo=UTC),
            introduced_commands=(
                "if",
                "then",
                "else",
                "fi",
                "[[ ]]",
                "for",
                "while",
                "ping",
                "traceroute",
                "host",
                "curl",
                "curl -I",
            ),
            introduced_skills=(
                "control-flow",
                "conditionals",
                "loops",
                "network-diagnostics",
                "dns",
                "ip-networking",
                "icmp",
                "http-basics",
                "http",
                "http-status-codes",
            ),
            learning_objectives=(
                "Distinguish the DNS, ICMP, and HTTP questions behind a website check.",
                "Inspect an HTTP response with curl.",
                (
                    "Use a for loop and if statement to verify two personal website pages "
                    "return HTTP 200. Grading accepts equivalent control flow."
                ),
            ),
            content=_session_content("S6", "Is your site actually working?"),
            objectives=(
                SessionObjective(
                    id="resolve-classroom-host",
                    title="Resolve the classroom hostname",
                    prompt=(
                        "Run `host lf2607.kolamayermakers.org`. Identify one IP address "
                        "in the output."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(rf"^host {_CLASSROOM_HOSTNAME_PATTERN}$",),
                        observed_commands=("host",),
                    ),
                ),
                SessionObjective(
                    id="inspect-personal-site-headers",
                    title="Inspect your site response",
                    prompt=(
                        'Run `curl -I "https://lf2607.kolamayermakers.org/~$USER/"`. Find the '
                        "HTTP status code in the response headers."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(_STATIC_HOMEPAGE_COMMAND_PATTERN,),
                        observed_commands=("curl -I",),
                    ),
                ),
                SessionObjective(
                    id="check-personal-pages",
                    title="Check both personal pages",
                    prompt=_S6_SITE_CHECK_PROMPT,
                    validation=SiteCheckValidation(),
                ),
            ),
        ),
        Session(
            id="S7",
            title="Your page on the wire",
            date=date(2026, 9, 19),
            starts_at=datetime(2026, 9, 19, 9, tzinfo=UTC),
            introduced_commands=(
                "curl -v",
                "nc",
                "diff",
                "caddy",
            ),
            introduced_skills=(
                "http-inspection",
                "sockets",
                "html-on-the-wire",
                "reverse-proxy",
                "multi-page-sites",
            ),
            learning_objectives=(
                "Inspect HTTP requests and responses.",
                "Compare rendered HTML on disk and over the network.",
                "Distinguish static hosting from a proxy with no backend service.",
                "Add another page to the site.",
            ),
            content=_session_content("S7", "Your page on the wire"),
            objectives=(
                SessionObjective(
                    id="inspect-first-url-headers",
                    title="Inspect HTTP requests and responses",
                    prompt=(
                        'Run `curl -I "https://lf2607.kolamayermakers.org/~$USER/"` to inspect '
                        "your static homepage headers. Compare with the raw HTTP lab; the guide "
                        "records the curl command, not the returned status."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(_STATIC_HOMEPAGE_COMMAND_PATTERN,),
                        observed_commands=("curl -I",),
                    ),
                ),
                SessionObjective(
                    id="compare-source-and-output",
                    title="Compare rendered HTML on disk and over the network",
                    prompt=(
                        "Run `build-website`, then use `diff` to compare a generated page with a "
                        "fetched copy."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^(?:build-website|maker-guide-build-personal-website)$",
                            r"^diff ",
                        ),
                        observed_commands=("build-website", "diff"),
                    ),
                ),
                SessionObjective(
                    id="diagnose-second-url",
                    title="Diagnose the separate service URL",
                    prompt=(
                        'Run `curl -v "https://$USER.lf2607.kolamayermakers.org/"`. Inspect '
                        "the proxy response and explain the missing backend. This is a separate "
                        "serving route, not the report path checked in S6."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            _SERVICE_HOMEPAGE_COMMAND_PATTERN.replace("curl -I", "curl -v"),
                        ),
                        observed_commands=("curl -v",),
                    ),
                ),
                SessionObjective(
                    id="create-setup-page",
                    title="Add another page to the site",
                    prompt=(
                        "Write a headed `~/src/pages/setup.md`, link `setup.html` from `index.md`, "
                        "then run `build-website` and check the generated setup page."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/src/pages/setup.md", required_regex=r"(?s)# .+"
                            ),
                            FileCheckValidation(
                                path="~/src/pages/index.md", required_regex=r"setup\.html"
                            ),
                            FileCheckValidation(
                                path="~/public_html/setup.html", required_regex=r"(?is)setup"
                            ),
                            CommandHistoryValidation(
                                required_patterns=(
                                    r"^(?:build-website|maker-guide-build-personal-website)$",
                                ),
                                observed_commands=("build-website",),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        Session(
            id="S8",
            title="Your own web service",
            date=date(2026, 9, 26),
            starts_at=datetime(2026, 9, 26, 9, tzinfo=UTC),
            introduced_commands=(
                "tmux",
                "python3 -m http.server --bind 127.0.0.1",
                "id -u",
                "systemctl --user",
                "journalctl --user",
            ),
            introduced_skills=(
                "terminal-multiplexing",
                "manual-web-service",
                "service",
                "bash-functions",
                "systemd-user-services",
                "logging",
                "service-logs",
                "lingering",
            ),
            learning_objectives=(
                "Create, detach from, list, reattach to, and end a tmux session.",
                "Start a web server manually.",
                "Wrap service actions in shell functions.",
                "Run a user systemd service.",
                "Read service logs.",
                "Keep the service alive after logout.",
            ),
            content=_session_content("S8", "Your own web service"),
            objectives=(
                SessionObjective(
                    id="keep-tmux-workbench",
                    title="Keep work alive in tmux",
                    prompt=(
                        "Create a tmux session named `workbench`, detach with `Ctrl-b d`, list it, "
                        "attach, detach again, then run `tmux kill-session -t workbench`."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^tmux new -s workbench$",
                            r"^tmux ls$",
                            r"^tmux attach -t workbench$",
                            r"^tmux kill-session -t workbench$",
                        ),
                        observed_commands=("tmux",),
                        ordered=True,
                    ),
                ),
                SessionObjective(
                    id="serve-local-check-page",
                    title="Start a web server manually",
                    prompt=(
                        "Start `python3 -m http.server` for your site, then use "
                        "`curl` to request a page from it."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"python3 -m http\.server",
                            _LOCAL_SERVICE_COMMAND_PATTERN,
                        ),
                        observed_commands=("python3 -m http.server --bind 127.0.0.1", "curl"),
                    ),
                ),
                SessionObjective(
                    id="write-site-helper-functions",
                    title="Wrap service actions in shell functions",
                    prompt=(
                        "Create executable `~/bin/site.sh` with `site_port`, `serve`, "
                        "`status`, and `stop` functions for a localhost web server."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/bin/site.sh",
                                required_regex=(
                                    r"(?s)site_port\(\).+10000.+id -u.+serve\(\).+"
                                    r"python3 -m http\.server.+--bind 127\.0\.0\.1.+"
                                    r'--directory "\$HOME/public_html".+status\(\).+'
                                    r"systemctl --user status.+stop\(\).+systemctl --user stop"
                                ),
                            ),
                            ExecutablePathValidation(paths=("~/bin/site.sh",)),
                        ),
                    ),
                ),
                SessionObjective(
                    id="enable-site-service",
                    title="Run a user systemd service",
                    prompt=(
                        "Create `~/.config/systemd/user/site.service` to serve `~/public_html` on "
                        "localhost, enable it with `systemctl --user enable --now "
                        "site.service`, then check both its localhost port and public service "
                        "URL with `curl -I`. Read the statuses yourself; command evidence alone "
                        "does not prove a healthy response."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            UserPortFileValidation(
                                path="~/.config/systemd/user/site.service",
                                required_regex_template=(
                                    r"(?s)\[Unit\].+\[Service\].+WorkingDirectory=%h/public_html.+"
                                    r"ExecStart=/usr/bin/python3 -m http\.server {port} "
                                    r"--bind 127\.0\.0\.1.+\[Install\].+WantedBy=default\.target"
                                ),
                            ),
                            CommandHistoryValidation(
                                required_patterns=(
                                    r"^systemctl --user enable --now site\.service$",
                                    _LOCAL_SERVICE_COMMAND_PATTERN,
                                    _SERVICE_HOMEPAGE_COMMAND_PATTERN,
                                ),
                                observed_commands=("systemctl --user", "curl"),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="watch-service-logs",
                    title="Read service logs",
                    prompt=(
                        "Request your public service URL with `curl -I`, then run "
                        "`journalctl --user -u site.service` to read the service log."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(
                            r"^journalctl --user -u site\.service",
                            _SERVICE_HOMEPAGE_COMMAND_PATTERN,
                        ),
                        observed_commands=("journalctl --user", "curl"),
                    ),
                ),
            ),
        ),
        Session(
            id="S9",
            title="Polish: timers, markdown, vim, webring",
            date=date(2026, 10, 10),
            starts_at=datetime(2026, 10, 10, 9, tzinfo=UTC),
            introduced_commands=(
                "systemd timer",
                "systemctl --user list-timers",
                "cron",
                "crontab",
                "sed",
                "awk",
                "vim",
                "weechat",
            ),
            introduced_skills=(
                "automation-timers",
                "text-transforms",
                "regular-expression",
                "vim-survival",
                "readme-writing",
                "irc",
            ),
            learning_objectives=(
                "Schedule user-level site rebuilds.",
                "Use light sed and awk transforms with regular expressions.",
                "Survive basic vim editing.",
                "Publish a readable README.",
                "Enable the webring through source configuration.",
                "Preserve the working scripts and systemd units in the source repository.",
            ),
            content=_session_content("S9", "Polish"),
            objectives=(
                SessionObjective(
                    id="schedule-site-rebuilds",
                    title="Schedule user-level site rebuilds",
                    prompt=(
                        "Create the `site-build.service` and hourly `site-build.timer` user units, "
                        "reload systemd, enable the timer, and list your timers."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/.config/systemd/user/site-build.service",
                                required_regex=(
                                    r"(?s)\[Service\].+Type=oneshot.+WorkingDirectory=%h/src.+"
                                    r"ExecStart=/usr/local/bin/npm run build"
                                ),
                            ),
                            FileCheckValidation(
                                path="~/.config/systemd/user/site-build.timer",
                                required_regex=(
                                    r"(?s)\[Timer\].+OnBootSec=5min.+OnUnitActiveSec=1h.+"
                                    r"\[Install\].+WantedBy=timers\.target"
                                ),
                            ),
                            CommandHistoryValidation(
                                required_patterns=(
                                    r"^systemctl --user daemon-reload$",
                                    r"^systemctl --user enable --now site-build\.timer$",
                                    r"^systemctl --user list-timers$",
                                ),
                                observed_commands=(
                                    "systemctl --user",
                                    "systemctl --user enable --now",
                                    "systemctl --user list-timers",
                                ),
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="transform-heading-with-sed",
                    title="Use light sed transforms",
                    prompt=(
                        "Run a `sed` command that changes a heading in a text file or sample text."
                    ),
                    validation=CommandHistoryValidation(
                        required_patterns=(r"(?:^|\|\s*)sed ",), observed_commands=("sed",)
                    ),
                ),
                SessionObjective(
                    id="extract-fields-with-awk",
                    title="Use light awk transforms",
                    prompt="Run an `awk` command that prints a field from a line of text.",
                    validation=CommandHistoryValidation(
                        required_patterns=(r"^awk ",), observed_commands=("awk",)
                    ),
                ),
                SessionObjective(
                    id="survive-vim",
                    title="Survive basic vim editing",
                    prompt=(
                        "Use `vim` to create `~/playground/vim-note.txt`, add a line of text, then "
                        "save and quit."
                    ),
                    validation=FileCheckValidation(
                        path="~/playground/vim-note.txt", required_regex=r"(?s).+"
                    ),
                ),
                SessionObjective(
                    id="write-readme",
                    title="Publish a readable README",
                    prompt=(
                        "Write `~/src/README.md` with a heading that names your site "
                        "and explains how to run it."
                    ),
                    validation=FileCheckValidation(
                        path="~/src/README.md",
                        required_regex=(
                            r"(?ms)\A# \S[^\n]*\n"
                            r"(?=.*(?:build-website|npm run build))(?=.*systemctl --user).+"
                        ),
                    ),
                ),
                SessionObjective(
                    id="enable-webring",
                    title="Enable the site webring",
                    prompt=(
                        "Set `webring = true` in `~/src/site.toml`, rebuild the site, "
                        "and check that the homepage shows webring, previous, and next links."
                    ),
                    validation=AllOfValidation(
                        validations=(
                            FileCheckValidation(
                                path="~/src/site.toml", required_regex=r"(?m)^webring *= *true$"
                            ),
                            FileCheckValidation(
                                path="~/public_html/index.html",
                                required_regex=r"(?is)(?=.*\bwebring\b)(?=.*\bprevious\b)(?=.*\bnext\b).+",
                            ),
                        ),
                    ),
                ),
                SessionObjective(
                    id="prepare-source-handoff",
                    title="Preserve the working project",
                    prompt=(
                        "Copy the three working scripts into `~/src/scripts/` and the three "
                        "systemd units into `~/src/services/`, keeping active originals in place. "
                        "Commit those copies and `README.md`, then verify them in Forgejo. "
                        "The guide checks committed, unchanged local files; "
                        "verify the push yourself."
                    ),
                    validation=AllOfValidation(
                        validations=tuple(
                            GitTrackedPathValidation(repository_path="~/src", path=path)
                            for path in _SOURCE_HANDOFF_PATHS
                        ),
                    ),
                ),
            ),
        ),
        Session(
            id="S10",
            title="Boss fight, demos, graduation",
            date=date(2026, 10, 24),
            starts_at=datetime(2026, 10, 24, 9, tzinfo=UTC),
            introduced_commands=(
                "file",
                "strings",
                "xxd",
                "base64",
                "tar",
                "gzip",
                "bzip2",
            ),
            introduced_skills=(
                "shell-investigation",
                "file-compression",
                "file-encoding",
                "number-bases",
            ),
            learning_objectives=(
                "Solve Bandit levels in teams.",
                "Demonstrate the static site, report, backend, source repository, and README.",
                "Publish a concrete next Linux project with a recovery plan.",
                "Understand what to explore after graduation.",
            ),
            content=_session_content("S10", "Boss fight, demos, graduation"),
        ),
    ),
    quests=(
        Quest(
            id="prove-shell-alive",
            title="Prove the shell is alive",
            sequence=1,
            available_after_session="S1",
            story=(
                "The first proof that this is your machine is not a speech. It is three "
                "plain commands answering who you are, what time it is, and how long the "
                "server has been awake."
            ),
            learner_goal="Confirm that your account and shell are working.",
            prompt="Connect to your account and run `whoami`, `date`, and `uptime`.",
            autonomy_checklist=(
                "SSH into your personal account, not the induction account.",
                "Run `whoami` and check that the output is your handle.",
                "Run `date` to ask the system for current time.",
                "Run `uptime` to ask how long the server has been running.",
                "The commands provide evidence. Run `guide check` to complete the quest.",
            ),
            hints=(
                Hint(level=1, text="Start with `whoami` and check that it prints your handle."),
                Hint(
                    level=2,
                    text="Run each command separately so the bot can see them clearly.",
                ),
                Hint(level=3, text="The exact commands are `whoami`, `date`, and `uptime`."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-command",
                    text=(
                        "I have not seen all three commands yet. Run `whoami`, `date`, "
                        "and `uptime`."
                    ),
                ),
            ),
            docs=_quest_documentation("prove-shell-alive", "Prove the shell is alive"),
            required_commands=("whoami", "date", "uptime"),
            practiced_skills=("ssh-login", "shell-basics"),
            score=25,
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^whoami$",
                    r"^date$",
                    r"^uptime$",
                ),
                observed_commands=("whoami", "date", "uptime"),
            ),
        ),
        Quest(
            id="name-system",
            title="Name the system",
            sequence=2,
            available_after_session="S1",
            story=(
                "Linux systems describe themselves in ordinary files. Reading those files is "
                "more reliable than guessing from a logo or a prompt."
            ),
            learner_goal="Read a system information file and report the distribution name.",
            prompt="Run `cat /etc/os-release` and find the `PRETTY_NAME` value.",
            autonomy_checklist=(
                "Run `cat /etc/os-release`.",
                "Find the line that starts with `PRETTY_NAME=`.",
                "Read the value after the equals sign.",
                "Answer the guide using the distribution name from that line.",
            ),
            hints=(
                Hint(level=1, text="Use `cat` to print the file."),
                Hint(level=2, text="Look for a line that starts with `PRETTY_NAME=`."),
                Hint(level=3, text="Copy the words inside the quotes after `PRETTY_NAME=`."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-answer",
                    text=(
                        "Submit the `PRETTY_NAME` value with `guide answer 'your answer'` "
                        "after reading `/etc/os-release`."
                    ),
                ),
                FailureFeedback(
                    reason="missing-concept",
                    text="Read `/etc/os-release` again and answer with the `PRETTY_NAME` value.",
                ),
                FailureFeedback(
                    reason="contradicted-concept",
                    text=(
                        "Your answer contradicts the value in `/etc/os-release`; answer with "
                        "the `PRETTY_NAME` value."
                    ),
                ),
            ),
            docs=_quest_documentation("name-system", "Name the system"),
            required_commands=("cat",),
            practiced_skills=("reading-files",),
            score=25,
            validation=InteractiveQuestionValidation(
                question="What is the PRETTY_NAME value in `/etc/os-release`?",
                required_concepts=(
                    AnswerConcept(
                        id="debian-pretty-name",
                        aliases=(r"\bdebian\b",),
                        rubric=(
                            "The answer must identify the system's PRETTY_NAME as Debian. Saying "
                            "the system is not Debian contradicts this concept."
                        ),
                        forbidden_patterns=(r"\bnot\s+debian\b",),
                    ),
                ),
            ),
        ),
        Quest(
            id="count-home-entries",
            title="Count your home entries",
            sequence=3,
            available_after_session="S1",
            story=(
                "Your home directory is where your work starts. Hidden files count because "
                "Linux uses dotfiles for configuration."
            ),
            learner_goal="Inspect your home directory and count visible plus hidden entries.",
            prompt="Run `ls -la ~` and count entries excluding `.` and `..`.",
            autonomy_checklist=(
                "Run `ls -la ~`.",
                "Ignore the line ending with `.`.",
                "Ignore the line ending with `..`.",
                "Count every remaining entry.",
                "Answer the guide with the count and what you counted.",
            ),
            hints=(
                Hint(level=1, text="The `-a` flag shows hidden files."),
                Hint(level=2, text="Do not count the `.` and `..` entries."),
                Hint(
                    level=3,
                    text="Count the remaining lines after the permission and owner columns.",
                ),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-answer",
                    text=(
                        "Submit the count and what you counted with `guide answer 'your answer'` "
                        "after running `ls -la ~`."
                    ),
                ),
                FailureFeedback(
                    reason="missing-concept",
                    text="Run `ls -la ~` again and count every entry except `.` and `..`.",
                ),
            ),
            docs=_quest_documentation("count-home-entries", "Count your home entries"),
            required_commands=("ls",),
            practiced_skills=("filesystem-navigation",),
            score=25,
            validation=InteractiveQuestionValidation(
                question="How many entries are in your home directory, excluding `.` and `..`?",
                required_concepts=(
                    AnswerConcept(
                        id="numeric-count",
                        aliases=(r"\b[0-9]+\b",),
                        rubric=(
                            "The answer must give a numeric count of home entries after excluding "
                            "the special . and .. entries."
                        ),
                    ),
                ),
            ),
        ),
        Quest(
            id="explain-ls",
            title="Read `man ls`",
            sequence=4,
            available_after_session="S1",
            story=(
                "The manual is not homework. It is part of the operating system. When you "
                "read it, you are asking Linux to explain itself."
            ),
            learner_goal="Use a manual page to discover what an `ls` option does.",
            prompt="Read `man ls`, find what `-S` does, then quit the manual.",
            autonomy_checklist=(
                "Run `man ls`.",
                "Search the page for `-S` or scan the options list.",
                "Read the description beside `-S`.",
                "Quit the manual with `q`.",
                "Answer the guide in your own words.",
            ),
            hints=(
                Hint(level=1, text="Open the manual with `man ls`."),
                Hint(level=2, text="Search inside the manual for `-S`."),
                Hint(level=3, text="The answer uses the ideas of sorting and file size."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-answer",
                    text="Explain `-S` with `guide answer 'your answer'` after reading `man ls`.",
                ),
                FailureFeedback(
                    reason="missing-concept",
                    text="Open `man ls` again. The answer must explain sorting by file size.",
                ),
            ),
            docs=_quest_documentation("explain-ls", "Read man ls"),
            required_commands=("man", "ls"),
            practiced_skills=("manual-pages",),
            score=25,
            validation=InteractiveQuestionValidation(
                question="What does `ls -S` do?",
                required_concepts=(
                    AnswerConcept(
                        id="sorts-output",
                        aliases=(r"\bsort(s|ed|ing)?\b",),
                        rubric="The answer must state that ls -S sorts the directory listing.",
                    ),
                    AnswerConcept(
                        id="by-size",
                        aliases=(r"\bsize\b", r"\blargest\b", r"\bsmallest\b"),
                        rubric=(
                            "The answer must state that ls -S sorts by file size, largest first. "
                            "Claiming it sorts smallest first contradicts this concept."
                        ),
                    ),
                ),
            ),
        ),
        Quest(
            id="read-file-ends",
            title="Read both ends of a file",
            sequence=6,
            available_after_session="S1",
            story=(
                "Large files are not read from top to bottom every time. Unix gives you tools "
                "to inspect the front and the back without drowning in output."
            ),
            learner_goal="Use `head` and `tail` to inspect selected lines from a system file.",
            prompt="Use `head -n 5` and `tail -n 5` on `/etc/services`.",
            autonomy_checklist=(
                "Run `head -n 5 /etc/services`.",
                "Read the first five lines that appear.",
                "Run `tail -n 5 /etc/services`.",
                "Read the last five lines that appear.",
                "Ask the guide to check after both commands have run.",
            ),
            hints=(
                Hint(level=1, text="Use `head -n 5 /etc/services` first."),
                Hint(level=2, text="Use `tail -n 5 /etc/services` after that."),
                Hint(level=3, text="The `-5` means show five lines."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-command",
                    text=(
                        "I need to see both commands: `head -n 5 /etc/services` and "
                        "`tail -n 5 /etc/services`."
                    ),
                ),
            ),
            docs=_quest_documentation("read-file-ends", "Read both ends of a file"),
            required_commands=("head", "tail"),
            practiced_skills=("reading-files",),
            score=25,
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^head -n 5 /etc/services$",
                    r"^tail -n 5 /etc/services$",
                ),
                observed_commands=("head", "tail"),
            ),
        ),
        Quest(
            id="build-playground",
            title="Build a playground",
            sequence=7,
            available_after_session="S2",
            story=(
                "Reading the system is useful. Making a safe place for experiments is better. "
                "A playground directory gives you somewhere to create files without risking "
                "the rest of your home directory."
            ),
            learner_goal="Create a practice directory, create three files, and inspect them.",
            prompt=(
                "Create `~/playground/`, touch `one.txt`, `two.txt`, and `three.txt` inside it, "
                "and list them with `ls -l`."
            ),
            autonomy_checklist=(
                "Run `mkdir -p ~/playground`.",
                "Create `one.txt`, `two.txt`, and `three.txt` with `touch` inside `~/playground`.",
                "Run `ls -l ~/playground`.",
                "Check that the three files are visible in the listing.",
                "Ask the guide to check the quest.",
            ),
            hints=(
                Hint(level=1, text="Make the directory before making files inside it."),
                Hint(level=2, text="Use `touch ~/playground/one.txt` to create one file."),
                Hint(
                    level=3,
                    text=(
                        "Create `one.txt`, `two.txt`, and `three.txt`, then run "
                        "`ls -l ~/playground`."
                    ),
                ),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-path",
                    text=(
                        "I need to see `~/playground/one.txt`, `~/playground/two.txt`, "
                        "and `~/playground/three.txt`."
                    ),
                ),
                FailureFeedback(
                    reason="permission-denied",
                    text=(
                        "Allow the guide to traverse your home directory, then check again: "
                        "run `chmod 711 ~`."
                    ),
                ),
            ),
            docs=_quest_documentation("build-playground", "Build a playground"),
            required_commands=("mkdir", "touch", "ls -l"),
            practiced_skills=("file-creation",),
            score=25,
            validation=PathExistsValidation(
                paths=(
                    "~/playground",
                    "~/playground/one.txt",
                    "~/playground/two.txt",
                    "~/playground/three.txt",
                ),
            ),
        ),
        Quest(
            id="edit-with-micro",
            title="Edit with micro",
            sequence=8,
            available_after_session="S2",
            story=(
                "A file you can edit is a place to leave instructions for your future self. "
                "The editor is not magic. It just writes bytes into a path you choose."
            ),
            learner_goal="Create a text file with micro and verify it with cat.",
            prompt=(
                "Use `micro` to create `~/playground/micro-note.txt` containing "
                "`edited with micro`, then `cat` it back."
            ),
            autonomy_checklist=(
                "Open `micro ~/playground/micro-note.txt`.",
                "Type `edited with micro` on the first line.",
                "Save and quit micro.",
                "Run `cat ~/playground/micro-note.txt`.",
                "Ask the guide to check the file.",
            ),
            hints=(
                Hint(level=1, text="Open the file path directly with `micro`."),
                Hint(level=2, text="Save before quitting micro."),
                Hint(
                    level=3,
                    text="The file must contain the exact text `edited with micro`.",
                ),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-path",
                    text="Create `~/playground/micro-note.txt` before asking me to check it.",
                ),
                FailureFeedback(
                    reason="file-content-mismatch",
                    text="Open `~/playground/micro-note.txt` again and make the first line exact.",
                ),
            ),
            docs=_quest_documentation("edit-with-micro", "Edit with micro"),
            required_commands=("micro", "cat"),
            practiced_skills=("file-editing",),
            score=25,
            validation=FileCheckValidation(
                path="~/playground/micro-note.txt",
                required_regex=r"(?s)^edited with micro\n?$",
            ),
        ),
        Quest(
            id="redirect-and-append",
            title="Redirect and append",
            sequence=9,
            available_after_session="S2",
            story=(
                "The shell can send command output into files. One operator replaces a file. "
                "The other appends to it. Mixing them up is a classic beginner wound."
            ),
            learner_goal="Create a two-line file with output redirection and append redirection.",
            prompt=(
                'Run `echo "hello makers" > ~/playground/hi.txt`, append `again` with '
                "`>>`, then `cat` both lines."
            ),
            autonomy_checklist=(
                'Run `echo "hello makers" > ~/playground/hi.txt`.',
                "Run `echo again >> ~/playground/hi.txt`.",
                "Run `cat ~/playground/hi.txt`.",
                "Confirm that the file has exactly two lines.",
                "Ask the guide to check the file.",
            ),
            hints=(
                Hint(level=1, text="Use `>` only for the first line."),
                Hint(level=2, text="Use `>>` for the second line so it appends."),
                Hint(level=3, text="The final file should contain `hello makers` then `again`."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-path",
                    text="Create `~/playground/hi.txt` before asking me to check it.",
                ),
                FailureFeedback(
                    reason="file-content-mismatch",
                    text="Recreate `~/playground/hi.txt` with `>` first, then `>>` for `again`.",
                ),
            ),
            docs=_quest_documentation("redirect-and-append", "Redirect and append"),
            required_commands=("echo", ">", ">>", "cat"),
            practiced_skills=("file-creation",),
            score=25,
            validation=FileCheckValidation(
                path="~/playground/hi.txt",
                required_regex=r"(?s)^hello makers\nagain\n?$",
            ),
        ),
        Quest(
            id="copy-and-inspect-ownership",
            title="Copy and inspect ownership",
            sequence=10,
            available_after_session="S2",
            story=(
                "Copying a file does not teleport the original inode into your directory. It "
                "creates your own new file. Ownership tells that story if you read `ls -l`."
            ),
            learner_goal="Copy a system file into your playground as your own file.",
            prompt=(
                "Copy `/etc/hostname` to `~/playground/hostname`, inspect it with `ls -l`, "
                "and inspect it with `ls -l`."
            ),
            autonomy_checklist=(
                "Run `cp /etc/hostname ~/playground/hostname`.",
                "Run `ls -l ~/playground/hostname` to inspect your copy.",
                "Ask the guide to check the file.",
            ),
            hints=(
                Hint(level=1, text="Use `cp` with the source first and the destination second."),
                Hint(level=2, text="In `ls -l`, the owner appears after the link count."),
                Hint(level=3, text="Your copy must have the same contents as `/etc/hostname`."),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-path",
                    text=(
                        "Copy `/etc/hostname` to `~/playground/hostname` before asking me to "
                        "check it."
                    ),
                ),
                FailureFeedback(
                    reason="wrong-owner",
                    text=(
                        "Run `cp /etc/hostname ~/playground/hostname` yourself so your Unix "
                        "account owns the copy."
                    ),
                ),
                FailureFeedback(
                    reason="file-content-mismatch",
                    text=(
                        "Make `~/playground/hostname` an exact copy of `/etc/hostname`, then "
                        "try again."
                    ),
                ),
            ),
            docs=_quest_documentation("copy-and-inspect-ownership", "Copy and inspect ownership"),
            required_commands=("cp", "ls -l"),
            practiced_skills=("file-manipulation",),
            score=25,
            validation=AllOfValidation(
                validations=(
                    OwnedPathValidation(path="~/playground/hostname"),
                    FileMatchesPathValidation(
                        path="~/playground/hostname",
                        source_path="/etc/hostname",
                    ),
                ),
            ),
        ),
        Quest(
            id="personalize-homepage",
            title="Personalize your homepage",
            sequence=11,
            available_after_session="S2",
            story=(
                "Your homepage should not stay as starter output. The durable habit is to "
                "edit source, rebuild output, and check the public result."
            ),
            learner_goal=(
                "Edit homepage source, rebuild the site, and prove the generated page changed."
            ),
            prompt=(
                "Replace the starter heading in `~/src/pages/index.md`, run `build-website`, "
                "then check the generated homepage."
            ),
            autonomy_checklist=(
                "Open `~/src/pages/index.md` with `micro`.",
                "Replace `A Linux site under construction` with any text.",
                "Save the source file and run `build-website`.",
                "Run `cat ~/public_html/index.html` and find your new heading.",
                "Ask the guide to check the source and generated homepage.",
            ),
            hints=(
                Hint(level=1, text="Edit source under `~/src/pages/`, not generated output."),
                Hint(level=2, text="Run `build-website` after saving the Markdown source."),
                Hint(
                    level=3,
                    text=(
                        "Replace the starter heading in source, then rebuild so it also "
                        "changes in generated output."
                    ),
                ),
            ),
            failure_feedback=(
                FailureFeedback(
                    reason="missing-path",
                    text=(
                        "Check that both `~/src/pages/index.md` and "
                        "`~/public_html/index.html` exist."
                    ),
                ),
                FailureFeedback(
                    reason="forbidden-content-present",
                    text=(
                        "Replace the starter heading in `~/src/pages/index.md`, run "
                        "`build-website`, and check `~/public_html/index.html`."
                    ),
                ),
                FailureFeedback(
                    reason="file-content-mismatch",
                    text=(
                        "Make sure both `~/src/pages/index.md` and "
                        "`~/public_html/index.html` contain page content."
                    ),
                ),
                FailureFeedback(
                    reason="missing-command",
                    text=(
                        "Run `build-website` after editing the source, then ask me to check again."
                    ),
                ),
            ),
            docs=_quest_documentation("personalize-homepage", "Personalize your homepage"),
            required_commands=("micro", "build-website", "cat"),
            practiced_skills=("site-source-ownership", "markdown-basics", "first-site-build"),
            score=25,
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/src/pages/index.md",
                        required_regex=r"\S",
                        forbidden_regex=r"A Linux site under construction",
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^(?:build-website|maker-guide-build-personal-website)$",
                        ),
                        observed_commands=("build-website",),
                    ),
                    FileCheckValidation(
                        path="~/public_html/index.html",
                        required_regex=r"\S",
                        forbidden_regex=r"A Linux site under construction",
                    ),
                ),
            ),
        ),
        _quest(
            quest_id="count-stream",
            title="Count a stream",
            sequence=14,
            available_after_session="S3",
            prompt="Use a pipeline to count the distinct login shells in `/etc/passwd`.",
            required_commands=("cut", "sort", "wc"),
            practiced_skills=("pipes",),
            validation=CommandHistoryValidation(
                required_patterns=(r"^cut -d: -f7 /etc/passwd\s*\|\s*sort -u\s*\|\s*wc -l$",),
                observed_commands=("cut", "sort", "wc"),
            ),
            goal="Transform, deduplicate, and count a text stream without a temporary file.",
            evidence="Run `cut -d: -f7 /etc/passwd | sort -u | wc -l`.",
        ),
        _quest(
            quest_id="keep-pipeline-copy",
            title="Keep a pipeline copy",
            sequence=15,
            available_after_session="S3",
            prompt=(
                "Run `cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l`, "
                "then inspect the saved stream."
            ),
            required_commands=("mkdir", "cut", "tee", "wc", "cat"),
            practiced_skills=("pipes", "stream-redirection"),
            validation=AllOfValidation(
                validations=(
                    CommandHistoryValidation(
                        required_patterns=(_KEEP_PIPELINE_COPY_PATTERN,),
                        observed_commands=("cut", "tee", "wc"),
                    ),
                    FileCheckValidation(
                        path="~/playground/login-shells.txt",
                        required_regex=r"(?m)^/",
                    ),
                ),
            ),
            goal="Save a useful stream without stopping the rest of its pipeline.",
            evidence=(
                "The guide needs the complete `tee` pipeline and shell paths in "
                "`~/playground/login-shells.txt`."
            ),
        ),
        _quest(
            quest_id="read-permissions",
            title="Read permissions",
            sequence=20,
            available_after_session="S4",
            prompt=(
                "From `~/playground`, run `chmod u+x permission-demo.txt`, then "
                "`ls -l permission-demo.txt` and explain its file type "
                "plus the owner, group, and other permission triplets."
            ),
            required_commands=("chmod", "ls -l"),
            practiced_skills=("permissions",),
            validation=InteractiveQuestionValidation(
                question=(
                    "What type of path is permission-demo.txt? What can its owner, group, "
                    "and other users do?"
                ),
                required_concepts=(
                    AnswerConcept(
                        id="regular-file",
                        aliases=(
                            r"\bregular\s+file\b",
                            r"\btype\s+is\s+(?:a\s+)?file\b",
                        ),
                        rubric="The answer must identify permission-demo.txt as a regular file.",
                    ),
                    AnswerConcept(
                        id="owner-permissions",
                        aliases=(
                            r"\bowner\b.*\bread\b.*\bwrite\b.*\bexecute\b",
                            r"\bowner\b.*\bis readable/writable/executable by me\b",
                        ),
                        rubric="The answer must state that the owner can read, write, and execute.",
                    ),
                    AnswerConcept(
                        id="group-permissions",
                        aliases=(
                            r"\bgroup\b.*\bread\b",
                            r"\bgroup is (?P<name>\S+)\b.*\b(?:is|and) readable by (?P=name)\b",
                        ),
                        rubric="The answer must state that the group can read.",
                    ),
                    AnswerConcept(
                        id="other-permissions",
                        aliases=(
                            r"\bothers?\b.*\bread\b",
                            r"(?:^|\b(?:is|are|and) )readable by (?:\S+ and )?others?\b",
                        ),
                        rubric="The answer must state that other users can read.",
                    ),
                ),
            ),
            goal="Read Unix permission text without guessing.",
            evidence="Answer with the file type and all three permission triplets from `ls -l`.",
        ),
        _quest(
            quest_id="make-file-executable",
            title="Make a file executable",
            sequence=21,
            available_after_session="S4",
            prompt=(
                "Create `~/playground/permission-test.txt`, run `chmod u+x` on it, "
                "and inspect the owner permission triplet."
            ),
            required_commands=("touch", "chmod", "ls -l"),
            practiced_skills=("permissions", "multi-user-filesystems"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/playground/permission-test.txt",
                        required_regex=r"(?s).*",
                    ),
                    ExecutablePathValidation(paths=("~/playground/permission-test.txt",)),
                ),
            ),
            goal="Change one permission bit deliberately and verify the result.",
            evidence="`~/playground/permission-test.txt` needs owner execute permission.",
        ),
        _quest(
            quest_id="recover-directory-traversal",
            title="Recover directory traversal",
            sequence=22,
            available_after_session="S4",
            prompt=(
                "Create `~/playground/no-enter-demo`, remove owner execute permission, restore it, "
                "and explain why entering the directory failed."
            ),
            required_commands=("mkdir", "chmod", "cd"),
            practiced_skills=("permissions", "multi-user-filesystems"),
            validation=AllOfValidation(
                validations=(
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^mkdir(?: -p)? (?:~/playground/)?no-enter-demo/?$",
                            r"^chmod u-x (?:~/playground/)?no-enter-demo/?$",
                            r"^chmod u\+x (?:~/playground/)?no-enter-demo/?$",
                            r"^cd (?:~/playground/)?no-enter-demo/?$",
                        ),
                        observed_commands=("mkdir", "chmod", "cd"),
                    ),
                    InteractiveQuestionValidation(
                        question="Why did entering no-enter-demo fail until you restored x?",
                        required_concepts=(
                            AnswerConcept(
                                id="directory-traversal",
                                aliases=(
                                    r"\b(?:directory|enter|travers\w*)\b.*\b(?:x|execut\w*)\b",
                                    r"\b(?:x|execut\w*)\b.*\b(?:directory|enter|travers\w*)\b",
                                ),
                                rubric="The answer must explain that x permits directory entry.",
                            ),
                        ),
                    ),
                ),
            ),
            goal="Experience that directory execute permission controls traversal.",
            evidence=(
                "The guide needs the remove-and-restore chmod commands and an explanation of "
                "directory traversal."
            ),
        ),
        _quest(
            quest_id="commit-source",
            title="Commit your source",
            sequence=23,
            available_after_session="S4",
            prompt=(
                "Run `cd ~/src`. Then run `git status`, `git diff`, `git add`, "
                "`git diff --staged`, `git commit`, and `git log`."
            ),
            required_commands=("git status", "git diff", "git add", "git commit", "git log"),
            practiced_skills=("git-basics",),
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^git status$",
                    r"^git diff$",
                    r"^git add ",
                    r"^git diff --staged$",
                    r"^git commit",
                    r"^git log",
                ),
                observed_commands=("git status", "git diff", "git add", "git commit", "git log"),
            ),
            goal="Review selected source changes before recording a commit.",
            evidence="The guide needs to see status, both diffs, add, commit, and log commands.",
        ),
        _quest(
            quest_id="ignore-scratch-files",
            title="Ignore scratch files",
            sequence=24,
            available_after_session="S4",
            prompt=(
                "Add `*.tmp` to `~/src/.gitignore` without removing its existing rules, run "
                "`touch scratch.tmp` from `~/src`, and confirm `git status` does not list it."
            ),
            required_commands=("micro", "touch", "git status"),
            practiced_skills=("git-basics",),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/src/.gitignore",
                        required_regex=(
                            r"(?ms)^(?=.*^node_modules/$)(?=.*^dist/$)(?=.*^\*\.tmp$).*$"
                        ),
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^touch (?:~/src/)?scratch\.tmp$",
                            r"^git status(?: --short)?$",
                        ),
                        observed_commands=("touch", "git status"),
                    ),
                ),
            ),
            goal="Ignore disposable files that actually live inside your source repository.",
            evidence=(
                "`~/src/.gitignore` needs its existing node_modules/ and dist/ rules plus `*.tmp`; "
                "the guide also needs `touch scratch.tmp` and `git status` commands."
            ),
        ),
        _quest(
            quest_id="explain-git-states",
            title="Explain Git states",
            sequence=25,
            available_after_session="S4",
            prompt=(
                "Run `git status` and `git diff`, then explain what unstaged, staged, committed, "
                "and pushed mean."
            ),
            required_commands=("git status", "git diff"),
            practiced_skills=("git-basics", "forgejo-publishing"),
            validation=AllOfValidation(
                validations=(
                    CommandHistoryValidation(
                        required_patterns=(r"^git status$", r"^git diff$"),
                        observed_commands=("git status", "git diff"),
                    ),
                    InteractiveQuestionValidation(
                        question="What do unstaged, staged, committed, and pushed mean?",
                        required_concepts=(
                            AnswerConcept(
                                id="unstaged",
                                aliases=(r"\bunstaged\b.*\b(work(ing)? tree|not.*commit)\b",),
                                rubric=(
                                    "The answer must explain that unstaged changes are not selected"
                                    " for a commit."
                                ),
                            ),
                            AnswerConcept(
                                id="staged",
                                aliases=(r"\bstaged\b.*\b(next commit|select)\b",),
                                rubric=(
                                    "The answer must explain that staged changes are selected for a"
                                    " commit."
                                ),
                            ),
                            AnswerConcept(
                                id="committed",
                                aliases=(r"\bcommitted\b.*\b(local|history|record)\b",),
                                rubric="The answer must identify committed changes as local.",
                            ),
                            AnswerConcept(
                                id="pushed",
                                aliases=(r"\bpushed\b.*\b(remote|forgejo|server)\b",),
                                rubric="The answer must identify pushed commits as remote.",
                            ),
                        ),
                    ),
                ),
            ),
            goal="Explain where a source change is in the Git workflow.",
            evidence="The guide needs status, diff, and all four state explanations.",
        ),
        _quest(
            quest_id="extend-maker-report",
            title="Add uptime to the report",
            sequence=33,
            available_after_session="S5",
            prompt=(
                "Add a labeled `uptime` line to `maker-report.sh`, regenerate "
                "`~/src/pages/maker-report.md`, and rebuild the site."
            ),
            required_commands=("micro", "uptime", "cat", "build-website"),
            practiced_skills=("shell-scripting", "filesystem-as-cms", "stream-redirection"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/scripts/maker-report.sh",
                        required_regex=_S5_REPORT_PIPELINE_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/scripts/maker-report.sh",
                        required_regex=_S5_REPORT_DESTINATION_SCRIPT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/scripts/maker-report.sh",
                        required_regex=_S5_UPTIME_SCRIPT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/src/pages/maker-report.md",
                        required_regex=_S5_MARKDOWN_REPORT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/src/pages/maker-report.md",
                        required_regex=_S5_UPTIME_REPORT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/public_html/maker-report.html",
                        required_regex=_S5_HTML_REPORT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/public_html/maker-report.html",
                        required_regex=_S5_UPTIME_HTML_PATTERN,
                    ),
                ),
            ),
            goal="Extend a useful script without replacing the working parts.",
            evidence="The script, Markdown page, and built HTML all need a labeled uptime value.",
        ),
        _quest(
            quest_id="run-scripts-from-elsewhere",
            title="Run scripts from elsewhere",
            sequence=34,
            available_after_session="S5",
            prompt=(
                "Change to `~/playground`, then run `maker-report.sh` with a quoted title using "
                "its home-anchored `~/...` path."
            ),
            required_commands=("cd",),
            practiced_skills=("path", "shell-scripting"),
            validation=CommandHistoryValidation(
                required_patterns=(r"^cd ~/playground$", _S5_HOME_TITLED_REPORT_COMMAND_PATTERN),
                observed_commands=("cd",),
                ordered=True,
            ),
            goal="Separate your current directory from the path to an executable file.",
            evidence=(
                "The guide needs `cd ~/playground`, then a titled "
                "`~/scripts/maker-report.sh ...` run."
            ),
        ),
        _quest(
            quest_id="preserve-maker-report",
            title="Preserve the report script in Git",
            sequence=35,
            available_after_session="S5",
            prompt="Commit `maker-report.sh` in `~/src/scripts/` with your normal Git workflow.",
            required_commands=("git log",),
            practiced_skills=("shell-scripting", "git-basics"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/src/scripts/maker-report.sh",
                        required_regex=_S5_SHEBANG_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/src/scripts/maker-report.sh",
                        required_regex=_S5_REPORT_PIPELINE_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/src/scripts/maker-report.sh",
                        required_regex=_S5_REPORT_DESTINATION_SCRIPT_PATTERN,
                    ),
                    FileCheckValidation(
                        path="~/src/scripts/maker-report.sh",
                        required_regex=_S5_UPTIME_SCRIPT_PATTERN,
                    ),
                    ExecutablePathValidation(paths=("~/src/scripts/maker-report.sh",)),
                    GitTrackedPathValidation(
                        repository_path="~/src",
                        path="scripts/maker-report.sh",
                    ),
                ),
            ),
            goal="Keep the useful script in the source history created during S4.",
            evidence="The final script must be executable, committed, and unchanged from HEAD.",
        ),
        _quest(
            quest_id="resolve-hostname",
            title="Resolve a hostname",
            sequence=46,
            available_after_session="S6",
            prompt="Run `host lf2607.kolamayermakers.org` and report one address or answer line.",
            required_commands=("host",),
            practiced_skills=("dns", "network-diagnostics"),
            validation=InteractiveQuestionValidation(
                question="What answer did `host lf2607.kolamayermakers.org` return?",
                required_concepts=(
                    AnswerConcept(
                        id="host-answer-line",
                        aliases=(
                            (
                                r"^(?:[a-z0-9.-]+ has address )?"
                                r"(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}"
                                r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$"
                            ),
                            (
                                r"^(?:[a-z0-9.-]+ has ipv6 address )?"
                                r"(?:(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}|"
                                r"(?=(?::*[0-9a-f]{1,4}){0,7}:*$)"
                                r"(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4})*)?::"
                                r"(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4})*)?)$"
                            ),
                            r"^[a-z0-9.-]+ is an alias for [a-z0-9-]+(?:\.[a-z0-9-]+)+\.?$",
                        ),
                        rubric=(
                            "The answer must report one returned IP address or a complete host "
                            "address or alias answer line for lf2607.kolamayermakers.org "
                            "or the development classroom lf-dev.kolamayermakers.org. "
                            "The words 'has' or 'address' without a record value are not enough."
                        ),
                    ),
                ),
            ),
            goal="Use DNS tools to ask how a name resolves before using it in a URL.",
            evidence=(
                "Answer with one returned IP address or complete `host` address or alias line."
            ),
        ),
        _quest(
            quest_id="measure-ping",
            title="Measure a ping",
            sequence=47,
            available_after_session="S6",
            prompt=(
                "Run `ping -c 3 1.1.1.1` and report the average round-trip time in ms, "
                "or the packet-loss percentage if no replies provide an average."
            ),
            required_commands=("ping",),
            practiced_skills=("network-diagnostics",),
            validation=InteractiveQuestionValidation(
                question=(
                    "What average time in ms did ping report, or what packet-loss percentage "
                    "did you observe when no average was available?"
                ),
                required_concepts=(
                    AnswerConcept(
                        id="milliseconds",
                        aliases=(
                            r"\b[0-9]+(?:\.[0-9]+)?\s*ms\b",
                            r"\b100(?:\.0+)?%\s+packet\s+loss\b",
                        ),
                        rubric=(
                            "The answer must report the observed average round-trip time as a "
                            "number with the ms unit, or honestly report 100% packet loss when "
                            "no replies provided an average. Failed ICMP does not prove HTTP fails."
                        ),
                    ),
                ),
            ),
            goal="Read ICMP latency or packet loss without treating ping as a website test.",
            evidence=(
                "Answer with the observed average in `ms`, or `100% packet loss` if no replies."
            ),
        ),
        _quest(
            quest_id="read-http-headers",
            title="Read HTTP headers",
            sequence=48,
            available_after_session="S6",
            prompt=(
                "Run `curl -I` on your personal homepage and report the status line "
                "or Server header."
            ),
            required_commands=("curl -I",),
            practiced_skills=("http-basics",),
            validation=InteractiveQuestionValidation(
                question=(
                    "What status or Server header did `curl -I` on your personal homepage show?"
                ),
                required_concepts=(
                    AnswerConcept(
                        id="http-header",
                        aliases=(
                            r"\bhttp/[0-9]+(?:\.[0-9]+)?\s+[1-5][0-9]{2}(?=\s|$)",
                            r"\bserver:\s*\S+",
                        ),
                        rubric=(
                            "The answer must quote either the observed HTTP status line or the "
                            "Server response header."
                        ),
                    ),
                ),
            ),
            goal="Inspect HTTP headers without downloading a page body.",
            evidence=(
                "Answer with an HTTP status line including its three-digit code, or Server header."
            ),
        ),
        _quest(
            quest_id="check-personal-pages",
            title="Check your personal pages",
            sequence=49,
            available_after_session="S6",
            prompt=_S6_SITE_CHECK_PROMPT,
            required_commands=("for", "if", "curl -I", "printf", "bash", "micro"),
            practiced_skills=("loops", "conditionals", "control-flow", "http-basics"),
            validation=SiteCheckValidation(),
            goal="Diagnose both pages correctly across simulated HTTP and connection failures.",
            evidence=(
                "Pass all simulated cases with `guide now` in the classroom shell: "
                "both pages OK, report missing, homepage missing, HTTP error, either page's "
                "connection failure, misleading 200 with a failed curl exit, an arbitrary "
                "missing page, and no-argument usage help. Check only supplied page arguments. "
                "Then check live HTTP results and browser access yourself."
            ),
        ),
        _quest(
            quest_id="create-setup-page",
            title="Create a setup page",
            sequence=59,
            available_after_session="S7",
            prompt="Create `~/src/pages/setup.md`, link to it from `index.md`, and rebuild.",
            required_commands=("micro", "build-website"),
            practiced_skills=("multi-page-sites", "html-on-the-wire"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/src/pages/setup.md",
                        required_regex=r"(?s)# .+",
                    ),
                    FileCheckValidation(
                        path="~/src/pages/index.md",
                        required_regex=r"setup\.html",
                    ),
                    FileCheckValidation(
                        path="~/public_html/setup.html",
                        required_regex=r"(?is)setup",
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^(?:build-website|maker-guide-build-personal-website)$",
                        ),
                        observed_commands=("build-website",),
                    ),
                ),
            ),
            goal="Add a new page to your website and link to it.",
            evidence="Source heading, index link, generated page, and build command must exist.",
        ),
        _quest(
            quest_id="inspect-first-url-headers",
            title="Inspect first URL headers",
            sequence=60,
            available_after_session="S7",
            prompt="Run `curl -I` against your public `~username` URL and report the status code.",
            required_commands=("curl -I",),
            practiced_skills=("http-inspection", "http-status-codes"),
            validation=InteractiveQuestionValidation(
                question="What HTTP status code did your public `~username` URL return?",
                required_concepts=(
                    AnswerConcept(
                        id="http-200",
                        aliases=(r"\b200\b", r"\bok\b"),
                        rubric=(
                            "The answer must report HTTP status 200 OK for the public username "
                            "URL. Reporting an error status contradicts this concept."
                        ),
                    ),
                ),
            ),
            goal="Inspect HTTP headers for your live site.",
            evidence="Answer with the HTTP status code.",
        ),
        _quest(
            quest_id="diagnose-second-url",
            title="Diagnose the second URL",
            sequence=61,
            available_after_session="S7",
            prompt="Run `curl -v` against your second URL and explain why it fails before S8.",
            required_commands=("curl -v",),
            practiced_skills=("http-inspection", "reverse-proxy"),
            validation=InteractiveQuestionValidation(
                question="Why does the second URL fail before your service exists?",
                required_concepts=(
                    AnswerConcept(
                        id="missing-service",
                        aliases=(r"\bservice\b", r"\bbackend\b"),
                        rubric=(
                            "The answer must identify the absent backend service as the reason the "
                            "second URL fails. Claiming the service exists and is available "
                            "contradicts this concept."
                        ),
                    ),
                    AnswerConcept(
                        id="not-listening",
                        aliases=(r"\b(no|nothing)\s+listening\b", r"\bnot\s+listening\b"),
                        rubric=(
                            "The answer must state that no process is listening on the backend "
                            "port. Claiming a process is listening contradicts this concept."
                        ),
                    ),
                ),
            ),
            goal="Explain the missing-backend failure mode.",
            evidence="Answer must mention that no service is listening yet.",
        ),
        _quest(
            quest_id="publish-ascii-art",
            title="Publish ASCII art",
            sequence=62,
            available_after_session="S7",
            prompt="Create `~/src/pages/art.md` with a fenced code block and rebuild.",
            required_commands=("micro", "build-website"),
            practiced_skills=("multi-page-sites", "html-on-the-wire"),
            validation=FileCheckValidation(
                path="~/src/pages/art.md",
                required_regex=r"(?s)# .+```.+```",
            ),
            goal="Publish preformatted text on your website.",
            evidence="`~/src/pages/art.md` needs a heading and fenced code block.",
        ),
        _quest(
            quest_id="explain-status-codes",
            title="Explain status codes",
            sequence=63,
            available_after_session="S7",
            prompt="Explain `200`, `404`, and `502` in one short answer.",
            required_commands=("curl -I",),
            practiced_skills=("http-status-codes",),
            validation=InteractiveQuestionValidation(
                question="What do HTTP status codes 200, 404, and 502 mean?",
                required_concepts=(
                    AnswerConcept(
                        id="http-200",
                        aliases=(r"\b200\b",),
                        rubric="The answer must explain that HTTP 200 means the request succeeded.",
                    ),
                    AnswerConcept(
                        id="http-404",
                        aliases=(r"\b404\b",),
                        rubric=(
                            "The answer must explain that HTTP 404 means the requested resource "
                            "was not found."
                        ),
                    ),
                    AnswerConcept(
                        id="http-502",
                        aliases=(r"\b502\b",),
                        rubric=(
                            "The answer must explain that HTTP 502 means a gateway or proxy got an "
                            "invalid response from its upstream service."
                        ),
                    ),
                ),
            ),
            goal="Describe common HTTP status codes without panic.",
            evidence="Answer with all three codes and their meanings.",
        ),
        _quest(
            quest_id="compare-source-and-output",
            title="Compare source and output",
            sequence=64,
            available_after_session="S7",
            prompt="Use `diff` to compare one source Markdown page with generated HTML output.",
            required_commands=("diff", "build-website"),
            practiced_skills=("html-on-the-wire", "multi-page-sites"),
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^(?:build-website|maker-guide-build-personal-website)$",
                    r"^diff ",
                ),
                observed_commands=("build-website", "diff"),
            ),
            goal="Notice that generated HTML is related to source, not identical to it.",
            evidence="The guide needs to see a build and a `diff` command.",
        ),
        _quest(
            quest_id="inspect-generated-html",
            title="Inspect generated HTML",
            sequence=65,
            available_after_session="S7",
            prompt="Inspect `~/public_html/setup.html` and find generated HTML tags.",
            required_commands=("cat", "grep"),
            practiced_skills=("html-on-the-wire", "text-search"),
            validation=FileCheckValidation(
                path="~/public_html/setup.html",
                required_regex=r"(?is)<html|<h1|setup",
            ),
            goal="Read generated output as the browser receives it.",
            evidence="`~/public_html/setup.html` must exist and contain generated HTML.",
        ),
        _quest(
            quest_id="probe-closed-port",
            title="Probe a closed port",
            sequence=66,
            available_after_session="S7",
            prompt="Use `nc` against a port with no service and describe the failure.",
            required_commands=("nc",),
            practiced_skills=("reverse-proxy", "sockets"),
            validation=InteractiveQuestionValidation(
                question="What happened when `nc` reached a port without a service?",
                required_concepts=(
                    AnswerConcept(
                        id="closed-port",
                        aliases=(r"\b(refused|closed|failed)\b",),
                        rubric=(
                            "The answer must report that the connection was refused or failed "
                            "because no service accepted it on the port."
                        ),
                    ),
                ),
            ),
            goal="Recognize a missing backend before systemd enters the story.",
            evidence="Answer with the failure mode from `nc`.",
        ),
        _quest(
            quest_id="record-http-headers",
            title="Record HTTP headers",
            sequence=67,
            available_after_session="S7",
            prompt="Save response headers from your public URL into `~/playground/headers.txt`.",
            required_commands=("curl -I", ">", "cat"),
            practiced_skills=("http-inspection", "http-status-codes"),
            validation=FileCheckValidation(
                path="~/playground/headers.txt",
                required_regex=r"(?im)^HTTP/",
            ),
            goal="Keep HTTP evidence that can be compared later.",
            evidence="`~/playground/headers.txt` needs an HTTP status line.",
        ),
        _quest(
            quest_id="create-links-page",
            title="Create a links page",
            sequence=68,
            available_after_session="S7",
            prompt="Create `~/src/pages/links.md`, link it from `index.md`, and rebuild.",
            required_commands=("micro", "build-website"),
            practiced_skills=("multi-page-sites", "html-on-the-wire"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(path="~/src/pages/links.md", required_regex=r"(?s)# .+"),
                    FileCheckValidation(path="~/src/pages/index.md", required_regex=r"links\.html"),
                ),
            ),
            goal="Make navigation between your own pages explicit.",
            evidence="The source page and an index link to `links.html` must exist.",
        ),
        _quest(
            quest_id="compare-page-fetches",
            title="Compare two page fetches",
            sequence=69,
            available_after_session="S7",
            prompt="Fetch two site pages with `curl`, save them, and compare them with `diff`.",
            required_commands=("curl", "diff", ">"),
            practiced_skills=("http-inspection", "html-on-the-wire"),
            validation=CommandHistoryValidation(
                required_patterns=(r"^curl ", r"^diff "),
                observed_commands=("curl", "diff"),
            ),
            goal="Use command-line evidence to compare what the web server returns.",
            evidence="The guide needs to see `curl` and `diff` commands.",
        ),
        _quest(
            quest_id="explain-502",
            title="Explain a 502",
            sequence=70,
            available_after_session="S7",
            prompt="Explain why a reverse proxy returns 502 when the backend service is missing.",
            required_commands=("curl -v",),
            practiced_skills=("reverse-proxy", "http-status-codes"),
            validation=InteractiveQuestionValidation(
                question="Why does a reverse proxy return 502 for a missing backend service?",
                required_concepts=(
                    AnswerConcept(
                        id="missing-backend",
                        aliases=(r"\bbackend\b",),
                        rubric=(
                            "The answer must identify the reverse proxy's unavailable backend. "
                            "Blaming the requested page alone contradicts this concept."
                        ),
                    ),
                    AnswerConcept(
                        id="missing-service",
                        aliases=(r"\bservice\b",),
                        rubric=(
                            "The answer must explain that the backend service is absent or not "
                            "running, so the proxy cannot obtain a response."
                        ),
                    ),
                ),
            ),
            goal="Name the proxy-versus-backend boundary before you run your own service.",
            evidence="Answer must mention the backend service.",
        ),
        _quest(
            quest_id="publish-http-troubleshooting",
            title="Publish troubleshooting notes",
            sequence=71,
            available_after_session="S7",
            prompt="Create `~/src/pages/troubleshooting.md` with notes on 200, 404, and 502.",
            required_commands=("micro", "build-website"),
            practiced_skills=("multi-page-sites", "reverse-proxy"),
            validation=FileCheckValidation(
                path="~/src/pages/troubleshooting.md",
                required_regex=r"(?s)200.+404.+502|502.+404.+200",
            ),
            goal="Turn HTTP failure modes into notes you can use during service work.",
            evidence="`~/src/pages/troubleshooting.md` needs notes on 200, 404, and 502.",
        ),
        _quest(
            quest_id="keep-tmux-workbench",
            title="Keep a tmux workbench",
            sequence=72,
            available_after_session="S8",
            prompt=(
                "Create `quest-workbench`, detach, list, reattach, detach again, then end it with "
                "`tmux kill-session -t quest-workbench`."
            ),
            required_commands=("tmux",),
            practiced_skills=("terminal-multiplexing",),
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^tmux new -s quest-workbench$",
                    r"^tmux ls$",
                    r"^tmux attach -t quest-workbench$",
                    r"^tmux kill-session -t quest-workbench$",
                ),
                observed_commands=("tmux",),
                ordered=True,
            ),
            goal="Keep terminal work alive when SSH disconnects.",
            evidence=(
                "The guide needs `tmux new -s quest-workbench`, `tmux ls`, and "
                "`tmux attach -t quest-workbench`, then `tmux kill-session -t quest-workbench`."
            ),
        ),
        _quest(
            quest_id="write-site-helper-functions",
            title="Write site helper functions",
            sequence=73,
            available_after_session="S8",
            prompt="Create executable `~/bin/site.sh` with subcommands for your local site server.",
            required_commands=(
                "mkdir",
                "micro",
                "chmod",
                "python3 -m http.server --bind 127.0.0.1",
                "id -u",
                "systemctl --user",
            ),
            practiced_skills=("bash-functions", "manual-web-service"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/bin/site.sh",
                        required_regex=(
                            r"(?s)site_port\(\).+10000.+id -u.+serve\(\).+"
                            r"python3 -m http\.server.+--bind 127\.0\.0\.1.+"
                            r'--directory "\$HOME/public_html".+status\(\).+'
                            r"systemctl --user status.+stop\(\).+systemctl --user stop"
                        ),
                    ),
                    ExecutablePathValidation(paths=("~/bin/site.sh",)),
                ),
            ),
            goal="Turn repeated site-server operations into one reusable command.",
            evidence=(
                "`~/bin/site.sh` needs site_port, serve, status, and stop subcommands, "
                "plus executable permission."
            ),
        ),
        _quest(
            quest_id="enable-site-service",
            title="Enable site.service",
            sequence=74,
            available_after_session="S8",
            prompt="Create and enable your user `site.service` for the second URL.",
            required_commands=("id -u", "mkdir", "micro", "systemctl --user", "curl"),
            practiced_skills=("systemd-user-services", "manual-web-service"),
            validation=AllOfValidation(
                validations=(
                    UserPortFileValidation(
                        path="~/.config/systemd/user/site.service",
                        required_regex_template=(
                            r"(?s)\[Unit\].+\[Service\].+WorkingDirectory=%h/public_html.+"
                            r"ExecStart=/usr/bin/python3 -m http\.server {port} "
                            r"--bind 127\.0\.0\.1.+\[Install\].+WantedBy=default\.target"
                        ),
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^systemctl --user enable --now site\.service$",
                            _LOCAL_SERVICE_COMMAND_PATTERN,
                            _SERVICE_HOMEPAGE_COMMAND_PATTERN,
                        ),
                        observed_commands=("systemctl --user", "curl"),
                    ),
                ),
            ),
            goal="Make your second URL work using a user service.",
            evidence=(
                "`site.service` must use your computed port, with enable and local/public curl "
                "observations. Inspect actual responses and browser access yourself."
            ),
        ),
        _quest(
            quest_id="watch-service-logs",
            title="Watch service logs",
            sequence=75,
            available_after_session="S8",
            prompt=(
                "Follow `site.service` logs in a tmux session, detach, make a request with `curl`, "
                "reattach, stop the log follower, and end the tmux session."
            ),
            required_commands=("tmux", "journalctl --user", "curl"),
            practiced_skills=("service-logs", "terminal-multiplexing"),
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^tmux new -s logs$",
                    r"^curl ",
                    r"^journalctl --user -u site\.service -f$",
                    r"^tmux attach -t logs$",
                    r"^tmux kill-session -t logs$",
                ),
                observed_commands=("tmux", "journalctl --user", "curl"),
                ordered=True,
            ),
            goal="Watch your service logs while traffic arrives.",
            evidence=(
                "The guide needs the complete named tmux workflow: create, curl, reattach, stop "
                "journalctl, and kill the session."
            ),
        ),
        _quest(
            quest_id="break-and-read-error",
            title="Break and read the error",
            sequence=76,
            available_after_session="S8",
            prompt=(
                "Temporarily break `site.service`, read the journal error, then restore "
                "and verify it."
            ),
            required_commands=("systemctl --user", "journalctl --user", "micro", "curl"),
            practiced_skills=("service-logs", "systemd-user-services"),
            validation=AllOfValidation(
                validations=(
                    InteractiveQuestionValidation(
                        question="What error did journalctl show for the broken service?",
                        required_concepts=(
                            AnswerConcept(
                                id="journal-error",
                                aliases=(r"\berror\b", r"\bfailed\b"),
                                rubric=(
                                    "The answer must report the specific failure or error message "
                                    "observed in journalctl for the deliberately broken service."
                                ),
                            ),
                        ),
                    ),
                    CommandHistoryValidation(
                        required_patterns=(r"^systemctl --user restart site\.service$", r"^curl "),
                        observed_commands=("systemctl --user", "curl"),
                    ),
                ),
            ),
            goal="Use logs instead of guessing, then prove the service was restored.",
            evidence="Answer with the journal error and verify the repaired service with curl.",
        ),
        _quest(
            quest_id="fix-and-restart-service",
            title="Fix and restart service",
            sequence=77,
            available_after_session="S8",
            prompt="Fix `site.service`, restart it, and verify both site URLs with `curl`.",
            required_commands=("systemctl --user", "curl", "journalctl --user"),
            practiced_skills=("systemd-user-services", "service-logs"),
            validation=CommandHistoryValidation(
                required_patterns=(r"^systemctl --user restart", r"^curl "),
                observed_commands=("systemctl --user", "curl"),
            ),
            goal="Recover your service after a configuration mistake.",
            evidence="The guide needs to see a restart and a curl verification.",
        ),
        _quest(
            quest_id="check-service-status",
            title="Check service status",
            sequence=78,
            available_after_session="S8",
            prompt="Run `systemctl --user status site.service` and report the state you observe.",
            required_commands=("systemctl --user",),
            practiced_skills=("systemd-user-services", "service"),
            validation=InteractiveQuestionValidation(
                question="What state did `systemctl --user status site.service` report?",
                required_concepts=(
                    AnswerConcept(
                        id="service-state",
                        aliases=(
                            r"\b(?:active|inactive|failed|activating|deactivating|running|dead)\b",
                        ),
                        rubric=(
                            "The answer must report the observed state of site.service. "
                            "Inactive, failed, or transitional states are valid observations; "
                            "do not require the learner to claim the service is running."
                        ),
                    ),
                    AnswerConcept(
                        id="site-service",
                        aliases=(r"\bservice\b", r"\bsite\.service\b"),
                        rubric=(
                            "The answer must make clear that the reported state belongs to "
                            "site.service, not an unrelated process."
                        ),
                    ),
                ),
            ),
            goal="Read service state from systemd instead of guessing from the browser.",
            evidence="Answer with the reported service state.",
        ),
        _quest(
            quest_id="restart-service-cleanly",
            title="Restart service cleanly",
            sequence=79,
            available_after_session="S8",
            prompt="Restart `site.service` and verify the local endpoint with `curl`.",
            required_commands=("systemctl --user", "curl"),
            practiced_skills=("systemd-user-services", "manual-web-service"),
            validation=CommandHistoryValidation(
                required_patterns=(r"^systemctl --user restart site\.service$", r"^curl "),
                observed_commands=("systemctl --user", "curl"),
            ),
            goal="Restart a service deliberately and verify behavior afterward.",
            evidence="The guide needs to see a restart and a curl verification.",
        ),
        _quest(
            quest_id="document-service-port",
            title="Document your service port",
            sequence=80,
            available_after_session="S8",
            prompt="Create `~/src/pages/service.md` explaining how your user port is computed.",
            required_commands=("id -u", "micro", "build-website"),
            practiced_skills=("manual-web-service", "multi-page-sites"),
            validation=FileCheckValidation(
                path="~/src/pages/service.md",
                required_regex=r"(?s)10000.+uid|uid.+10000|port",
            ),
            goal="Make the per-user port rule explicit enough to debug later.",
            evidence="`~/src/pages/service.md` must mention the port or `10000 + uid` rule.",
        ),
        _quest(
            quest_id="read-recent-logs",
            title="Read recent logs",
            sequence=81,
            available_after_session="S8",
            prompt="Read recent `site.service` logs after making a request with `curl`.",
            required_commands=("journalctl --user", "curl"),
            practiced_skills=("service-logs", "logging"),
            validation=CommandHistoryValidation(
                required_patterns=(r"^curl ", r"^journalctl --user -u site\.service"),
                observed_commands=("curl", "journalctl --user"),
            ),
            goal="Tie one web request to evidence in the service journal.",
            evidence="The guide needs to see curl and journalctl for `site.service`.",
        ),
        _quest(
            quest_id="serve-local-check-page",
            title="Serve a local check page",
            sequence=82,
            available_after_session="S8",
            prompt=(
                "Stop `site.service`, run a temporary Python HTTP server in tmux, fetch it with "
                "`curl`, stop it, then restart `site.service`."
            ),
            required_commands=(
                "systemctl --user",
                "tmux",
                "python3 -m http.server --bind 127.0.0.1",
                "curl",
            ),
            practiced_skills=(
                "systemd-user-services",
                "terminal-multiplexing",
                "manual-web-service",
                "sockets",
            ),
            validation=CommandHistoryValidation(
                required_patterns=(
                    r"^systemctl --user stop site\.service$",
                    r"^tmux new -s local-server$",
                    r"^tmux ls$",
                    r"^curl ",
                    r"python3 -m http\.server",
                    r"^tmux attach -t local-server$",
                    r"^tmux kill-session -t local-server$",
                    r"^systemctl --user start site\.service$",
                ),
                observed_commands=(
                    "systemctl --user",
                    "tmux",
                    "python3 -m http.server --bind 127.0.0.1",
                    "curl",
                ),
                ordered=True,
            ),
            goal="Temporarily replace the managed service with a foreground server and restore it.",
            evidence=(
                "The guide needs the ordered service stop, tmux server, curl, cleanup, and service "
                "start commands."
            ),
        ),
        _quest(
            quest_id="add-health-page",
            title="Add a health page",
            sequence=83,
            available_after_session="S8",
            prompt="Create `~/src/pages/health.md`, rebuild, and fetch the generated page.",
            required_commands=("micro", "build-website", "curl"),
            practiced_skills=("multi-page-sites", "http"),
            validation=FileCheckValidation(
                path="~/src/pages/health.md",
                required_regex=r"(?s)# .+health|Health",
            ),
            goal="Publish a simple page that can be used for service checks.",
            evidence="`~/src/pages/health.md` needs a health heading or note.",
        ),
        _quest(
            quest_id="explain-user-services",
            title="Explain user services",
            sequence=84,
            available_after_session="S8",
            prompt="Explain the difference between a user service and a system service.",
            required_commands=("systemctl --user",),
            practiced_skills=("systemd-user-services", "service"),
            validation=InteractiveQuestionValidation(
                question="What makes `site.service` a user service?",
                required_concepts=(
                    AnswerConcept(
                        id="user-scope",
                        aliases=(r"\buser\b", r"\b--user\b"),
                        rubric=(
                            "The answer must explain that site.service runs under the learner's "
                            "per-user systemd manager. Calling it a system-wide service "
                            "contradicts this concept."
                        ),
                    ),
                    AnswerConcept(
                        id="service",
                        aliases=(r"\bservice\b",),
                        rubric="The answer must identify site.service as a managed service unit.",
                    ),
                ),
            ),
            goal="Know which service manager owns your process.",
            evidence="Answer must mention user service scope.",
        ),
        _quest(
            quest_id="preflight-both-urls",
            title="Preflight both URLs",
            sequence=85,
            available_after_session="S8",
            prompt="Check both public URLs with `curl -I` and inspect service status.",
            required_commands=("curl -I", "systemctl --user"),
            practiced_skills=("http-inspection", "systemd-user-services"),
            validation=CommandHistoryValidation(
                required_patterns=(
                    _STATIC_HOMEPAGE_COMMAND_PATTERN,
                    _SERVICE_HOMEPAGE_COMMAND_PATTERN,
                    r"^systemctl --user show site\.service -p ActiveState -p SubState$",
                ),
                observed_commands=("curl -I", "systemctl --user"),
            ),
            goal="Collect URL and service evidence to discuss in the polish session.",
            evidence="The guide needs to see header checks and service status.",
        ),
        _quest(
            quest_id="try-cron-and-remove-it",
            title="Try cron and remove it",
            sequence=86,
            available_after_session="S9",
            prompt=(
                "Create a temporary cron job that appends `date` to `~/cron.log`, then remove it."
            ),
            required_commands=("cron", "crontab", "date", ">>", ">", "2>", "cat"),
            practiced_skills=("automation-timers",),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(path="~/cron.log", required_regex=r"(?s).+"),
                    FileCheckValidation(
                        path="~/crontab.after",
                        required_regex=r"(?s)^.*$",
                        forbidden_regex=r"(?m)^[ \t]*[^#\s][^\n]*#[ \t]*cron-demo\b",
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^crontab -l > ~/crontab\.after 2>/dev/null \|\| true$",
                        ),
                        observed_commands=("crontab",),
                    ),
                ),
            ),
            goal="Recognize cron and remove a scheduled job safely.",
            evidence="`~/cron.log` needs date output and `~/crontab.after` must omit the job.",
        ),
        _quest(
            quest_id="transform-heading-with-sed",
            title="Transform a heading with sed",
            sequence=87,
            available_after_session="S9",
            prompt="Use one `sed` command to turn `# heading` into `<h1>heading</h1>`.",
            required_commands=("sed",),
            practiced_skills=("text-transforms", "regular-expression"),
            validation=InteractiveQuestionValidation(
                question="Paste the `sed` command that converts `# heading` to `<h1>heading</h1>`.",
                required_concepts=(
                    AnswerConcept(
                        id="sed-command",
                        aliases=(r"\bsed\b",),
                        rubric=(
                            "The answer must provide a sed substitution command that transforms "
                            "the supplied Markdown heading."
                        ),
                    ),
                    AnswerConcept(
                        id="h1-output",
                        aliases=(r"<h1>", r"\bh1\b"),
                        rubric=(
                            "The command must produce an h1 element containing heading, including "
                            "both opening and closing tags."
                        ),
                    ),
                ),
            ),
            goal="Reshape text with a simple substitution rule.",
            evidence="Answer with a `sed` substitution that emits an `h1` tag.",
        ),
        _quest(
            quest_id="extract-fields-with-awk",
            title="Extract fields with awk",
            sequence=88,
            available_after_session="S9",
            prompt="Use `awk` to print the first field from each `/etc/passwd` line.",
            required_commands=("awk", "cat"),
            practiced_skills=("text-transforms",),
            validation=InteractiveQuestionValidation(
                question="Which command printed the first `/etc/passwd` field?",
                required_concepts=(
                    AnswerConcept(
                        id="awk-command",
                        aliases=(r"\bawk\b",),
                        rubric="The answer must provide the awk command used on /etc/passwd.",
                    ),
                    AnswerConcept(
                        id="print-action",
                        aliases=(r"\bprint\b", r"\$1"),
                        rubric=(
                            "The awk program must print the first field, represented by $1, from "
                            "each input line."
                        ),
                    ),
                ),
            ),
            goal="Extract fields from structured text.",
            evidence="Answer with the `awk` command you used.",
        ),
        _quest(
            quest_id="survive-vim",
            title="Survive vim",
            sequence=89,
            available_after_session="S9",
            prompt="Use vim to create `~/playground/vim-note.txt`, then save and quit with `:wq`.",
            required_commands=("vim", "cat"),
            practiced_skills=("vim-survival",),
            validation=FileCheckValidation(
                path="~/playground/vim-note.txt",
                required_regex=r"(?s).+",
            ),
            goal="Enter text, save, and quit vim without panic.",
            evidence="`~/playground/vim-note.txt` must contain text saved from vim.",
        ),
        _quest(
            quest_id="write-readme",
            title="Write your README",
            sequence=90,
            available_after_session="S9",
            prompt="Write a useful `~/src/README.md`, commit it, and push it.",
            required_commands=("micro", "vim", "git add", "git commit", "git push"),
            practiced_skills=("readme-writing", "forgejo-publishing"),
            validation=FileCheckValidation(
                path="~/src/README.md",
                required_regex=(
                    r"(?ms)\A# \S[^\n]*\n"
                    r"(?=.*(?:build-website|npm run build))(?=.*systemctl --user).+"
                ),
            ),
            goal="Make your source repository understandable to another human.",
            evidence=(
                "`~/src/README.md` needs a title, site description, and actual "
                "build and `systemctl --user` commands."
            ),
        ),
        _quest(
            quest_id="enable-webring",
            title="Enable the webring",
            sequence=91,
            available_after_session="S9",
            prompt="Set `webring = true` in `~/src/site.toml` and verify generated output.",
            required_commands=("micro", "build-website", "grep", "curl"),
            practiced_skills=("site-source-ownership", "text-search"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/src/site.toml",
                        required_regex=r"(?m)^webring *= *true$",
                    ),
                    FileCheckValidation(
                        path="~/public_html/index.html",
                        required_regex=r"(?is)(?=.*\bwebring\b)(?=.*\bprevious\b)(?=.*\bnext\b).+",
                    ),
                ),
            ),
            goal="Join the cohort site ring through source configuration, not output edits.",
            evidence="`~/src/site.toml` must set `webring = true` and output needs ring links.",
        ),
        _quest(
            quest_id="schedule-site-rebuilds",
            title="Schedule site rebuilds",
            sequence=92,
            available_after_session="S9",
            prompt="Create a user systemd timer that runs your site build service on a schedule.",
            required_commands=(
                "mkdir",
                "micro",
                "systemd timer",
                "systemctl --user",
                "systemctl --user list-timers",
                "journalctl --user",
            ),
            practiced_skills=("automation-timers", "systemd-user-services", "service-logs"),
            validation=AllOfValidation(
                validations=(
                    FileCheckValidation(
                        path="~/.config/systemd/user/site-build.service",
                        required_regex=(
                            r"(?s)\[Service\].+Type=oneshot.+WorkingDirectory=%h/src.+"
                            r"ExecStart=/usr/local/bin/npm run build"
                        ),
                    ),
                    FileCheckValidation(
                        path="~/.config/systemd/user/site-build.timer",
                        required_regex=(
                            r"(?s)\[Timer\].+OnBootSec=5min.+OnUnitActiveSec=1h.+"
                            r"\[Install\].+WantedBy=timers\.target"
                        ),
                    ),
                    CommandHistoryValidation(
                        required_patterns=(
                            r"^systemctl --user daemon-reload$",
                            r"^systemctl --user enable --now site-build\.timer$",
                            r"^systemctl --user list-timers$",
                            r"^systemctl --user start site-build\.service$",
                            r"^journalctl --user -u site-build\.service",
                        ),
                        observed_commands=(
                            "systemctl --user",
                            "systemctl --user list-timers",
                            "journalctl --user",
                        ),
                    ),
                ),
            ),
            goal="Automate site rebuilds with a user timer you can inspect and debug.",
            evidence="The timer unit must be enabled, inspected, manually triggered, and logged.",
        ),
        _quest(
            quest_id="refresh-pipes-for-bandit",
            title="Refresh pipes for Bandit",
            sequence=93,
            available_after_session="S9",
            prompt="Run one pipeline using `grep`, `sort`, and `uniq`, then redirect errors away.",
            required_commands=("grep", "sort", "uniq", "2>"),
            practiced_skills=("pipes", "stream-redirection", "dev-null"),
            validation=CommandHistoryValidation(
                required_patterns=(r"grep .+\s*\|\s*sort\s*\|\s*uniq", r"2> ?/dev/null"),
                observed_commands=("grep", "sort", "uniq", "2>"),
            ),
            goal="Refresh the shell mechanics Bandit will punish you for forgetting.",
            evidence="The guide needs to see a grep-sort-uniq pipeline and stderr redirection.",
        ),
        _quest(
            quest_id="prepare-bandit-approach",
            title="Prepare a Bandit approach",
            sequence=94,
            available_after_session="S9",
            prompt="Write a short Bandit checklist using commands you already know.",
            required_commands=("ssh", "cat", "ls", "find", "grep"),
            practiced_skills=("text-search", "filesystem-navigation"),
            validation=InteractiveQuestionValidation(
                question="Which commands will you try first when a Bandit level looks unfamiliar?",
                required_concepts=(
                    AnswerConcept(
                        id="ssh-command",
                        aliases=(r"\bssh\b",),
                        rubric="The checklist must include ssh for connecting to the Bandit host.",
                    ),
                    AnswerConcept(
                        id="grep-command",
                        aliases=(r"\bgrep\b",),
                        rubric="The checklist must include grep for searching unfamiliar evidence.",
                    ),
                ),
            ),
            goal="Enter the boss fight with a method, not random commands.",
            evidence="Answer with at least `ssh` and `grep` in your plan.",
        ),
        _quest(
            quest_id="demo-site",
            title="Demo your site",
            sequence=95,
            available_after_session="S9",
            prompt="Show your public site, source repo, service, and README to another person.",
            required_commands=("curl", "git log", "systemctl --user"),
            practiced_skills=("multi-page-sites", "systemd-user-services", "readme-writing"),
            validation=InteractiveQuestionValidation(
                question=(
                    "What did you demonstrate for the static site, report, public service URL, "
                    "source repo, and README? Include one recovery and the feedback you received."
                ),
                required_concepts=(
                    AnswerConcept(
                        id="demoed-site",
                        aliases=(r"\bsite\b", r"\bwebsite\b"),
                        rubric=(
                            "The answer must state that the learner demonstrated the public site "
                            "and report page to another person."
                        ),
                    ),
                    AnswerConcept(
                        id="demoed-service",
                        aliases=(r"\bservice\b", r"\bbackend\b"),
                        rubric=(
                            "The answer must describe a working public service endpoint, not only "
                            "systemctl status or the independently hosted static site."
                        ),
                    ),
                    AnswerConcept(
                        id="demoed-source",
                        aliases=(r"\brepo(?:sitory)?\b", r"\bforgejo\b"),
                        rubric="The answer must describe showing the source repository and commit.",
                    ),
                    AnswerConcept(
                        id="demoed-readme",
                        aliases=(r"\breadme\b",),
                        rubric=(
                            "The answer must describe showing the README and its run instructions."
                        ),
                    ),
                ),
            ),
            goal="Turn your work into a short technical explanation.",
            evidence="Answer with what you demoed and what feedback you got.",
        ),
        _quest(
            quest_id="write-next-path",
            title="Write the next path",
            sequence=96,
            available_after_session="S9",
            prompt="Create `~/src/pages/next.md` describing what you will learn after S10.",
            required_commands=("micro", "build-website", "git add", "git commit", "git push"),
            practiced_skills=("multi-page-sites", "readme-writing"),
            validation=FileCheckValidation(
                path="~/src/pages/next.md",
                required_regex=(
                    r"(?im)\A(?=#[ \t]+[^\n]*\bLinux\b)"
                    r"(?=[\s\S]*^Next action:[ \t]*\S)[\s\S]+\Z"
                ),
            ),
            goal="Arrive at graduation with a concrete next step already written down.",
            evidence="`~/src/pages/next.md` needs a Linux heading and a non-empty `Next action:`.",
        ),
        _quest(
            quest_id="prepare-source-handoff",
            title="Prepare a source handoff",
            sequence=97,
            available_after_session="S9",
            prompt=(
                "Preserve and commit the working scripts, systemd units, and README in `~/src`; "
                "verify the pushed copies in Forgejo."
            ),
            required_commands=("cp", "git add", "git commit", "git push", "git log", "git status"),
            practiced_skills=("git-basics", "readme-writing"),
            validation=AllOfValidation(
                validations=tuple(
                    GitTrackedPathValidation(repository_path="~/src", path=path)
                    for path in _SOURCE_HANDOFF_PATHS
                ),
            ),
            goal="Preserve a recoverable project with its working scripts and service units.",
            evidence=(
                "The six script/unit copies and README must be committed and unchanged. "
                "Verify the remote copies in Forgejo yourself."
            ),
        ),
        _quest(
            quest_id="use-terminal-irc",
            title="Use IRC from the terminal",
            sequence=98,
            available_after_session="S9",
            prompt="Connect with WeeChat and message the guide from IRC.",
            required_commands=("weechat",),
            practiced_skills=("irc",),
            validation=IrcCtcpVersionValidation(
                accepted_clients=("WeeChat", "irssi", "BitchX"),
            ),
            goal="Prove you can use WeeChat from a terminal, not only the web frontend.",
            evidence="The guide needs to see that you are using a terminal IRC client.",
        ),
    ),
    tiers=(
        Tier(id="newcomer", minimum_score=0, title="Newcomer"),
        Tier(id="apprentice", minimum_score=500, title="Apprentice"),
        Tier(id="builder", minimum_score=1000, title="Builder"),
        Tier(id="maker", minimum_score=2000, title="Maker"),
    ),
)

"""Tests for the Linux Foundations July 2026 catalog."""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
from datetime import UTC, date, datetime
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import cast

from rich.markdown import Markdown

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.documentation import command_card_slug
from maker_guide.curriculum.linux_foundations_2026_07 import (
    COURSE_ID,
    LINUX_FOUNDATIONS_2026_07,
)
from maker_guide.curriculum.models import (
    AllOfValidation,
    CommandHistoryValidation,
    FileCheckValidation,
    FileMatchesPathValidation,
    GitTrackedPathValidation,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    IrcCtcpVersionValidation,
    OwnedPathValidation,
    PathExistsValidation,
    SiteCheckValidation,
    SshPublicKeyObservedValidation,
    UserPortFileValidation,
    validate_courses,
)

MARKDOWN_LINK_PATTERN = re.compile(
    r"(?<!!)\[(?P<label>[^\[\]\n]+)\]\((?P<target>[^)]+)\)",
)
RELATED_READING_LINK_PATTERN = re.compile(r"^- \[[^\]]+\]\((?P<target>[^)]+)\)$")
DOCS_PATH_PREFIX = "/docs/"


def test_linux_foundations_catalog_is_valid() -> None:
    """The production Linux Foundations catalog passes semantic validation."""
    validate_courses((LINUX_FOUNDATIONS_2026_07,))


def test_s6_site_check_uses_outcomes_for_objective_and_quest() -> None:
    """Both S6 tasks require local simulated outcomes, never reference source shape."""
    for validation in (
        next(
            objective.validation
            for objective in CATALOG.session("S6").objectives
            if objective.id == "check-personal-pages"
        ),
        CATALOG.quest("check-personal-pages").validation,
    ):
        assert isinstance(validation, SiteCheckValidation)


def test_static_homepage_history_accepts_quoting_but_not_subpaths() -> None:
    """The documented homepage command accepts shell quoting, not other resources."""
    validation = CATALOG.session("S6").objectives[1].validation
    assert isinstance(validation, CommandHistoryValidation)
    for hostname in ("lf2607.kolamayermakers.org", "lf-dev.kolamayermakers.org"):
        for command in (
            f'curl -I "https://{hostname}/~$USER/"',
            f'curl -I "https://{hostname}/~${{USER}}/"',
            f'curl -I "https://{hostname}/~learner/"',
            f"curl -I 'https://{hostname}/~learner/'",
            f"curl -I https://{hostname}/~learner/",
        ):
            assert re.search(validation.required_patterns[0], command)
        for command in (
            f'curl -I "https://{hostname}/~$USER/maker-report.html"',
            f'curl -I "https://{hostname}/~$USER/subpath/"',
            f'curl -I "https://{hostname}/~$USER/"/',
            f'curl -I "https://{hostname}/~$USER/',
            f"curl -I 'https://{hostname}/~$USER/'",
            f'curl -I "https://$USER.{hostname}/"',
        ):
            assert not re.search(validation.required_patterns[0], command)


def test_reported_results_need_values_not_just_keywords() -> None:
    """Reported evidence includes actual results, including loss and failed services."""
    for quest_id, accepted, rejected in (
        (
            "resolve-hostname",
            (
                "203.0.113.10",
                "2001:db8::10",
                "2001:db8:0:0:0:0:0:10",
                "lf2607.kolamayermakers.org has address 203.0.113.10",
                "lf2607.kolamayermakers.org has IPv6 address 2001:db8::10",
                "lf2607.kolamayermakers.org is an alias for classroom.example.org.",
            ),
            (
                "address",
                "has address",
                "has ipv6",
                "no address found",
                "999.999.999.999",
                "2001:db8:::10",
                "2001:db8:0:0:0:0:0::10",
            ),
        ),
        (
            "read-http-headers",
            ("HTTP/2 200", "HTTP/1.1 404 Not Found", "Server: Caddy"),
            ("HTTP/2", "HTTP/1.1", "HTTP/2 20", "HTTP/2 2000", "HTTP/2 200.5", "Server:"),
        ),
        (
            "measure-ping",
            ("12.3 ms", "100% packet loss", "3 transmitted, 0 received, 100% packet loss"),
            ("ms", "packet loss", "ping failed so the website is down"),
        ),
        (
            "check-service-status",
            (
                "site.service is active (running)",
                "site.service is inactive (dead)",
                "site.service failed with an exit-code result",
                "site.service is activating (auto-restart)",
                "Unit site.service could not be found",
            ),
            ("site.service", "I ran systemctl", "The website loaded in my browser"),
        ),
        (
            "inspect-first-url-headers",
            ("200", "HTTP/1.1 404 NotFound", "HTTP/2 502", "100", "599"),
            (
                "20",
                "2000",
                "200.5",
                "HTTP/2 20",
                "HTTP/2 2000",
                "HTTP/2 200.5",
                "099",
                "600",
                "OK",
                "HTTP",
                "DNS failed before HTTP",
                "TLS failed; no HTTP response",
            ),
        ),
        (
            "probe-closed-port",
            (
                "Connection refused because no listener was on my assigned port.",
                "nc timed out; the listener state is unknown.",
                "Timeout does not prove the port is closed.",
                "nc unexpectedly connected, so another listener accepted it.",
                "The connection succeeded, so the port is not closed.",
            ),
            (
                "failed",
                "closed",
                "Connection refused",
                "nc timed out",
                "nc connected",
                "Timeout proves the port is closed.",
                "Connected means the port is closed.",
                "Connection refused because no listener was present. Refused means HTTP 502.",
                "Timeout does not prove closed. Timeout proves the port is closed.",
            ),
        ),
        (
            "explain-status-codes",
            (
                (
                    "200 means success; 404 means the resource was not found; "
                    "502 means the proxy could not obtain a usable upstream response."
                ),
                (
                    "200 OK, 404 not found, 502 means the backend is unavailable. "
                    "502 does not prove the process stopped."
                ),
                (
                    "200 means the request succeeded; 404 means the requested path is missing; "
                    "502 means the gateway got an invalid response from its upstream."
                ),
            ),
            (
                "200 404 502",
                "200 means not found; 404 means success; 502 means the backend is unavailable.",
                "200 is not success; 404 is not missing; 502 is not an unavailable backend.",
                (
                    "200 means success; 404 means not found; 502 means the backend is unavailable. "
                    "200 does not mean success."
                ),
                (
                    "200 means success; 404 means not found; 502 means the backend is unavailable. "
                    "404 means success."
                ),
                (
                    "200 means success; 404 means not found; 502 means the backend is unavailable. "
                    "502 means a missing page."
                ),
            ),
        ),
        (
            "S7/diagnose-second-url",
            (
                (
                    "Localhost refused because personal Caddy stopped. "
                    "Shared Caddy returns 502 when its backend is unavailable. "
                    "Shared Caddy serves public_html directly, independently of personal Caddy."
                ),
                (
                    "Local curl was refused because no listener remained. "
                    "I expected 502 because the backend is unavailable, but DNS failed before "
                    "HTTP. The static route does not depend on personal Caddy; TLS failed there, "
                    "so I did not observe a static HTTP response."
                ),
            ),
            (
                "refused 502 static",
                (
                    "Localhost was not refused because personal Caddy stopped. "
                    "502 means the backend is unavailable. "
                    "The static route bypasses personal Caddy."
                ),
                (
                    "Localhost refused because personal Caddy stopped. "
                    "502 does not mean the backend is unavailable. "
                    "The static route bypasses personal Caddy."
                ),
                (
                    "Localhost refused because personal Caddy stopped. "
                    "502 means the backend is unavailable. "
                    "The static route bypasses personal Caddy. "
                    "The static route requires personal Caddy."
                ),
            ),
        ),
    ):
        validation = (
            CATALOG.session("S7").objectives[1].validation
            if quest_id == "S7/diagnose-second-url"
            else CATALOG.quest(quest_id).validation
        )
        assert isinstance(validation, InteractiveQuestionValidation)
        for answer in accepted:
            assert all(
                any(re.search(alias, answer.casefold()) for alias in concept.aliases)
                and not any(
                    re.search(pattern, answer.casefold()) for pattern in concept.forbidden_patterns
                )
                for concept in validation.required_concepts
            ), (quest_id, answer)
        for answer in rejected:
            assert not all(
                any(re.search(alias, answer.casefold()) for alias in concept.aliases)
                and not any(
                    re.search(pattern, answer.casefold()) for pattern in concept.forbidden_patterns
                )
                for concept in validation.required_concepts
            ), (quest_id, answer)


def test_sessions_expose_independent_objective_validators() -> None:
    """Objective gates own validators instead of borrowing quest definitions."""
    objective_validation_types_by_session = {
        session.id: tuple(type(objective.validation) for objective in session.objectives)
        for session in LINUX_FOUNDATIONS_2026_07.sessions
    }

    assert objective_validation_types_by_session == {
        "S1": (
            IrcChannelJoinObservedValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            AllOfValidation,
        ),
        "S2": (SshPublicKeyObservedValidation,),
        "S3": (
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
        ),
        "S4": (
            CommandHistoryValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
        ),
        "S5": (
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
        ),
        "S6": (
            CommandHistoryValidation,
            CommandHistoryValidation,
            SiteCheckValidation,
        ),
        "S7": (
            CommandHistoryValidation,
            InteractiveQuestionValidation,
        ),
        "S8": (
            AllOfValidation,
            CommandHistoryValidation,
            AllOfValidation,
            InteractiveQuestionValidation,
        ),
        "S9": (
            AllOfValidation,
            FileCheckValidation,
            AllOfValidation,
        ),
        "S10": (),
    }
    assert all(
        not hasattr(objective, "quest_id")
        for session in LINUX_FOUNDATIONS_2026_07.sessions
        for objective in session.objectives
    )


def test_s4_initializes_source_history() -> None:
    """S4 learners create their source repository."""
    session = CATALOG.session("S4")
    objective = next(
        objective for objective in session.objectives if objective.id == "initialize-source-repo"
    )

    assert "git init" in session.introduced_commands
    assert isinstance(objective.validation, CommandHistoryValidation)
    assert r"^git init$" in objective.validation.required_patterns


def test_s4_creates_the_forgejo_repository_with_fj() -> None:
    """S4 creates the empty remote without browser-only setup."""
    session = CATALOG.session("S4")
    objective = next(
        objective for objective in session.objectives if objective.id == "push-source-to-forgejo"
    )

    assert "fj" in session.introduced_commands
    assert isinstance(objective.validation, CommandHistoryValidation)
    assert objective.validation.required_patterns == (
        r"^fj repo create src$",
        r"^git remote ",
        r"^git push -u origin main$",
    )
    assert objective.validation.observed_commands == ("fj", "git remote", "git push")


def test_s4_quests_cover_permission_recovery_and_git_states() -> None:
    """S4 reinforcement covers the live labs without duplicating objectives."""
    quest_ids = {quest.id for quest in CATALOG.course.quests}

    assert "recover-directory-traversal" in quest_ids
    assert "explain-git-states" in quest_ids
    assert "initialize-source-repo" not in quest_ids
    assert "push-source-to-forgejo" not in quest_ids


def test_s4_path_validators_accept_relative_commands() -> None:
    """S4 accepts the short path forms taught after changing directory."""
    permission_objective = next(
        objective
        for objective in CATALOG.session("S4").objectives
        if objective.id == "read-permissions"
    )
    assert isinstance(permission_objective.validation, CommandHistoryValidation)
    for command in (
        "touch permission-demo.txt",
        "ls -l permission-demo.txt",
        "chmod u+x permission-demo.txt",
    ):
        assert any(
            re.fullmatch(pattern, command)
            for pattern in permission_objective.validation.required_patterns
        )

    directory_validation = CATALOG.quest("recover-directory-traversal").validation
    assert isinstance(directory_validation, AllOfValidation)
    directory_history = next(
        validation
        for validation in directory_validation.validations
        if isinstance(validation, CommandHistoryValidation)
    )
    for command in (
        "mkdir -p ~/playground/no-enter-demo",
        "mkdir -p no-enter-demo",
        "chmod u-x no-enter-demo",
        "chmod u+x no-enter-demo",
        "cd no-enter-demo",
    ):
        assert any(
            re.fullmatch(pattern, command) for pattern in directory_history.required_patterns
        )

    ignore_validation = CATALOG.quest("ignore-scratch-files").validation
    assert isinstance(ignore_validation, AllOfValidation)
    ignore_history = next(
        validation
        for validation in ignore_validation.validations
        if isinstance(validation, CommandHistoryValidation)
    )
    assert any(
        re.fullmatch(pattern, "touch scratch.tmp") for pattern in ignore_history.required_patterns
    )


def test_s5_builds_one_cumulative_report_script(temporary_path: Path) -> None:
    """S5 objectives and reinforcement converge on one runnable report."""
    session = CATALOG.session("S5")
    objectives = {objective.id: objective for objective in session.objectives}

    assert tuple(objectives) == (
        "create-maker-report",
        "run-maker-report-directly",
        "personalize-maker-report",
        "publish-maker-report",
    )
    assert session.introduced_commands == ("bash", "printf")
    assert "set -euo pipefail" not in session.introduced_commands
    assert "environment-variables" not in session.introduced_skills
    assert [quest.id for quest in CATALOG.quests_available_after("S5")] == [
        "extend-maker-report",
        "run-scripts-from-elsewhere",
        "preserve-maker-report",
    ]

    final_validation = objectives["publish-maker-report"].validation
    assert isinstance(final_validation, AllOfValidation)
    assert [
        validation.path
        for validation in final_validation.validations
        if isinstance(validation, FileCheckValidation)
    ] == [
        "~/scripts/maker-report.sh",
        "~/scripts/maker-report.sh",
        "~/src/pages/maker-report.md",
        "~/public_html/maker-report.html",
    ]
    for objective in objectives.values():
        objective_validation = objective.validation
        assert isinstance(objective_validation, AllOfValidation)
        assert not any(
            isinstance(validation, CommandHistoryValidation)
            for validation in objective_validation.validations
        )

    incomplete_sources_by_objective = {
        "run-maker-report-directly": (
            "#!/bin/bash\n",
            "whoami\nhostname\ndate\n",
        ),
        "personalize-maker-report": (
            '#!/bin/bash\nreport_title="$1"\nprintf \'<%s>\\n\' "$report_title"\n',
            "#!/bin/bash\nwhoami\nhostname\ndate\n",
            (
                "#!/bin/bash\n"
                'report_title="$1"\n'
                "printf '%%s\\n' \"$report_title\"\n"
                "whoami\nhostname\ndate\n"
            ),
        ),
    }
    for objective_id, incomplete_sources in incomplete_sources_by_objective.items():
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        source_validations = tuple(
            validation
            for validation in objective_validation.validations
            if isinstance(validation, FileCheckValidation)
        )
        assert source_validations
        for incomplete_source in incomplete_sources:
            assert not all(
                re.search(validation.required_regex, incomplete_source)
                for validation in source_validations
            )
    reference_text = (
        _content_root()
        .joinpath(
            "guides",
            "resources",
            "maker-report.sh",
        )
        .read_text(encoding="utf-8")
    )
    personalize_validation = objectives["personalize-maker-report"].validation
    assert isinstance(personalize_validation, AllOfValidation)
    assert all(
        re.search(validation.required_regex, reference_text)
        for validation in personalize_validation.validations
        if isinstance(validation, FileCheckValidation)
    )
    reference_path = temporary_path / "maker-report.sh"
    reference_path.write_text(reference_text, encoding="utf-8")
    reference_path.chmod(0o755)
    temporary_path.joinpath("src", "pages").mkdir(parents=True)

    completed_process = subprocess.run(
        [str(reference_path), "My Maker Report"],
        cwd=temporary_path,
        check=False,
        capture_output=True,
        env=os.environ | {"HOME": str(temporary_path), "LC_ALL": "C", "TZ": "UTC"},
        text=True,
    )
    assert completed_process.returncode == 0, completed_process.stderr
    assert completed_process.stderr == ""
    assert completed_process.stdout == ""
    generated_report_text = temporary_path.joinpath("src", "pages", "maker-report.md").read_text(
        encoding="utf-8"
    )
    assert generated_report_text.startswith("# My Maker Report\n\n* User: ")
    assert "```text\n" in generated_report_text
    assert generated_report_text.endswith("```\n")

    markdown_validation = next(
        validation
        for validation in final_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/maker-report.md"
    )
    assert re.search(markdown_validation.required_regex, generated_report_text)
    assert not re.search(
        markdown_validation.required_regex,
        generated_report_text.replace("# My Maker Report", "#"),
    )
    assert re.search(
        markdown_validation.required_regex,
        generated_report_text.replace("```text", "```"),
    )
    assert re.search(
        markdown_validation.required_regex,
        generated_report_text.replace(
            "## Shell fields in /etc/passwd",
            "## Shell fields in /etc/passwd:",
        ),
    )
    assert re.search(
        markdown_validation.required_regex,
        """# My Super Title
* User: ```
learner
```
* Host: ```
classroom
```
* Date: ```
today
```
## Shell fields in /etc/passwd:
```
/bin/bash
```
""",
    )
    html_validation = next(
        validation
        for validation in final_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/public_html/maker-report.html"
    )
    assert re.search(
        html_validation.required_regex,
        "<h1>Title</h1>User: Host: Date: <h2>Shell fields in /etc/passwd:</h2>",
    )
    assert not re.search(
        markdown_validation.required_regex,
        generated_report_text.replace("```", "~~~"),
    )


def test_s5_source_checks_accept_beginner_and_atomic_report_writes() -> None:
    """The supplied atomic writer must not invalidate the direct redirection taught in S5."""
    validation = CATALOG.session("S5").objectives[3].validation
    assert isinstance(validation, AllOfValidation)
    source_checks = tuple(
        child_validation
        for child_validation in validation.validations
        if isinstance(child_validation, FileCheckValidation)
        and child_validation.path == "~/scripts/maker-report.sh"
    )
    beginner_match = re.search(
        r"(?ms)^````bash\n(?P<script>#!/bin/bash\n.*?)^````$",
        _content_text(f"content/{COURSE_ID}/sessions/S05/self-study.md"),
    )
    assert beginner_match is not None
    for source_text in (
        beginner_match["script"],
        _content_root().joinpath("guides/resources/maker-report.sh").read_text(encoding="utf-8"),
        beginner_match["script"]
        .replace(
            "\n{\n",
            '\ntemporary_report=$(mktemp "$HOME/src/pages/.maker-report.XXXXXX")\n{\n',
        )
        .replace(
            "} > ~/src/pages/maker-report.md",
            (
                '} > "$temporary_report"\nchmod 644 "$temporary_report"\n'
                'mv -T -- "$temporary_report" "$HOME/src/pages/maker-report.md"'
            ),
        ),
    ):
        assert all(re.search(check.required_regex, source_text) for check in source_checks)
        assert all(
            re.search(
                check.required_regex,
                source_text.replace("{\n", "(\n").replace("} > ", ") > "),
            )
            for check in source_checks
        )
        for incomplete_source in (
            source_text.replace("  cut -d: -f7 /etc/passwd | sort -u\n", ""),
            re.sub(r"(?m)^\} >[^\n]+$", "}", source_text),
            source_text.replace("maker-report.md", "wrong-report.md"),
            re.sub(r"(?m)^(?:\} > ~/src/pages/maker-report\.md|mv -T --[^\n]+)$", "", source_text),
        ):
            assert not all(
                re.search(check.required_regex, incomplete_source) for check in source_checks
            )


def test_s5_personalize_accepts_direct_printf_variable() -> None:
    """A quoted first argument can be printed without the percent-s formatter."""
    validation = CATALOG.session("S5").objectives[2].validation
    assert isinstance(validation, AllOfValidation)
    assert all(
        re.search(
            file_validation.required_regex,
            """#!/bin/bash
report_title="$1"
whoami
hostname
date
printf "$report_title\\n"
""",
        )
        for file_validation in validation.validations
        if isinstance(file_validation, FileCheckValidation)
    )
    publish_validation = CATALOG.session("S5").objectives[3].validation
    assert isinstance(publish_validation, AllOfValidation)
    markdown_validation = next(
        file_validation
        for file_validation in publish_validation.validations
        if isinstance(file_validation, FileCheckValidation)
        and file_validation.path == "~/src/pages/maker-report.md"
    )
    assert re.search(
        markdown_validation.required_regex,
        """# foo bar
* User: ss79
* Hostname: lf-dev
* Date: Fri Aug 28 13:51:34 UTC 2026
## Shell fields in /etc/passwd
```
/bin/bash
```
""",
    )


def test_s5_reinforcement_preserves_the_cumulative_script(temporary_path: Path) -> None:
    """S5 extensions cannot replace the useful report with isolated syntax."""
    extension_validation = CATALOG.quest("extend-maker-report").validation
    preserve_validation = CATALOG.quest("preserve-maker-report").validation
    assert isinstance(extension_validation, AllOfValidation)
    assert isinstance(preserve_validation, AllOfValidation)

    uptime_reference_text = (
        _content_root()
        .joinpath(
            "mentors",
            "s05-solutions",
            "maker-report-with-uptime.sh",
        )
        .read_text(encoding="utf-8")
    )
    extension_source_validations = tuple(
        validation
        for validation in extension_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/scripts/maker-report.sh"
    )
    assert all(
        re.search(validation.required_regex, uptime_reference_text)
        for validation in extension_source_validations
    )
    assert not all(
        re.search(
            validation.required_regex,
            uptime_reference_text.replace("  uptime\n", ""),
        )
        for validation in extension_source_validations
    )

    preserve_source_validations = tuple(
        validation
        for validation in preserve_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/scripts/maker-report.sh"
    )
    assert all(
        re.search(validation.required_regex, uptime_reference_text)
        for validation in preserve_source_validations
    )
    git_validation = next(
        validation
        for validation in preserve_validation.validations
        if isinstance(validation, GitTrackedPathValidation)
    )
    assert git_validation.repository_path == "~/src"
    assert git_validation.path == "scripts/maker-report.sh"

    uptime_reference_path = temporary_path / "maker-report-with-uptime.sh"
    uptime_reference_path.write_text(uptime_reference_text, encoding="utf-8")
    uptime_reference_path.chmod(0o755)
    temporary_path.joinpath("src", "pages").mkdir(parents=True)
    uptime_process = subprocess.run(
        [str(uptime_reference_path), "Uptime Report"],
        cwd=temporary_path,
        check=False,
        capture_output=True,
        env=os.environ | {"HOME": str(temporary_path), "LC_ALL": "C", "TZ": "UTC"},
        text=True,
    )
    assert uptime_process.returncode == 0, uptime_process.stderr
    assert uptime_process.stdout == ""
    assert uptime_process.stderr == ""
    uptime_report_text = temporary_path.joinpath("src", "pages", "maker-report.md").read_text(
        encoding="utf-8"
    )
    assert "* Uptime: " in uptime_report_text
    assert uptime_report_text.endswith("```\n")
    assert all(
        re.search(
            validation.required_regex,
            """# Title
* User:
learner
* Host:
classroom
* Date:
today
* Uptime:
 14:25:07 up 36 days
## Shell fields in /etc/passwd:
```
/bin/bash
```
""",
        )
        for validation in extension_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/maker-report.md"
    )
    assert all(
        re.search(
            validation.required_regex,
            """<h1>Title</h1>User: Host: Date: <h2>Shell fields in /etc/passwd:</h2> \
<li>Uptime:
14:25:07 up 36 days</li>""",
        )
        for validation in extension_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/public_html/maker-report.html"
    )
    assert not all(
        re.search(
            validation.required_regex,
            """# Title
* User: learner
* Host: classroom
* Date: today
* Uptime:
## Shell fields in /etc/passwd:
```
/bin/bash
```
""",
        )
        for validation in extension_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/maker-report.md"
    )
    assert not all(
        re.search(
            validation.required_regex,
            """<h1>Title</h1>User: Host: Date: <h2>Shell fields in /etc/passwd:</h2> \
Uptime: unavailable, sign up today""",
        )
        for validation in extension_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.path == "~/public_html/maker-report.html"
    )
    assert not all(
        re.search(validation.required_regex, uptime_reference_text.replace("  uptime\n", ""))
        for validation in preserve_source_validations
    )

    elsewhere_validation = CATALOG.quest("run-scripts-from-elsewhere").validation
    assert isinstance(elsewhere_validation, CommandHistoryValidation)
    assert elsewhere_validation.ordered is True
    for documented_command in (
        '~/scripts/maker-report.sh "Elsewhere Report"',
        'bash ~/scripts/maker-report.sh "Elsewhere Report"',
    ):
        assert all(
            re.search(pattern, command)
            for pattern, command in zip(
                elsewhere_validation.required_patterns,
                ("cd ~/playground", documented_command),
                strict=True,
            )
        )
        assert not all(
            re.search(pattern, documented_command)
            for pattern in elsewhere_validation.required_patterns
        )


def test_catalog_exposes_course_identity_and_tiers() -> None:
    """Course ids and tiers line up with repository state ids."""
    assert LINUX_FOUNDATIONS_2026_07.id == COURSE_ID
    assert LINUX_FOUNDATIONS_2026_07.timezone == "Asia/Singapore"
    assert "Linux expert" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert "Socratic method" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert "provided learner snapshot" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert [(tier.id, tier.minimum_score) for tier in LINUX_FOUNDATIONS_2026_07.tiers] == [
        ("newcomer", 0),
        ("apprentice", 500),
        ("builder", 1000),
        ("maker", 2000),
    ]


def test_catalog_exposes_july_18_session_schedule() -> None:
    """Sessions keep explicit dates for the live course schedule."""
    assert LINUX_FOUNDATIONS_2026_07.starts_on == date(2026, 7, 18)
    assert LINUX_FOUNDATIONS_2026_07.ends_on == date(2026, 10, 24)
    assert [(session.id, session.date) for session in LINUX_FOUNDATIONS_2026_07.sessions] == [
        ("S1", date(2026, 7, 18)),
        ("S2", date(2026, 7, 25)),
        ("S3", date(2026, 8, 1)),
        ("S4", date(2026, 8, 8)),
        ("S5", date(2026, 8, 29)),
        ("S6", date(2026, 9, 12)),
        ("S7", date(2026, 9, 19)),
        ("S8", date(2026, 9, 26)),
        ("S9", date(2026, 10, 10)),
        ("S10", date(2026, 10, 24)),
    ]
    assert [(session.id, session.starts_at) for session in LINUX_FOUNDATIONS_2026_07.sessions] == [
        ("S1", datetime(2026, 7, 18, 9, tzinfo=UTC)),
        ("S2", datetime(2026, 7, 25, 9, tzinfo=UTC)),
        ("S3", datetime(2026, 8, 1, 9, tzinfo=UTC)),
        ("S4", datetime(2026, 8, 8, 9, tzinfo=UTC)),
        ("S5", datetime(2026, 8, 29, 5, tzinfo=UTC)),
        ("S6", datetime(2026, 9, 12, 9, tzinfo=UTC)),
        ("S7", datetime(2026, 9, 19, 9, tzinfo=UTC)),
        ("S8", datetime(2026, 9, 26, 9, tzinfo=UTC)),
        ("S9", datetime(2026, 10, 10, 9, tzinfo=UTC)),
        ("S10", datetime(2026, 10, 24, 9, tzinfo=UTC)),
    ]


def test_catalog_exposes_taught_commands_and_skills_by_session() -> None:
    """Lookup helpers return deterministic teaching gates."""
    assert "ssh" in CATALOG.commands_available_through("S1")
    assert "bat" in CATALOG.commands_available_through("S1")
    assert "touch" in CATALOG.commands_available_through("S2")
    assert "Get-Content" in CATALOG.commands_available_through("S2")
    assert "grep" not in CATALOG.commands_available_through("S2")
    assert "2>>" not in CATALOG.commands_available_through("S10")
    assert "uniq" in CATALOG.commands_available_through("S3")
    assert "pipes" in CATALOG.skills_available_through("S3")
    assert "text-search" in CATALOG.skills_available_through("S3")
    assert "regular-expression" not in CATALOG.skills_available_through("S8")
    assert "regular-expression" in CATALOG.skills_available_through("S9")
    assert "devices" not in CATALOG.all_skills_available_through("S10")
    assert "tmux" not in CATALOG.commands_available_through("S7")
    assert "tmux" in CATALOG.commands_available_through("S8")
    assert "terminal-multiplexing" not in CATALOG.skills_available_through("S7")
    assert "terminal-multiplexing" in CATALOG.skills_available_through("S8")
    assert "systemd-user-services" not in CATALOG.skills_available_through("S3")
    assert "kernel" not in CATALOG.skills_available_through("S1")
    assert "kernel" in CATALOG.enrichment_skills_available_through("S1")
    assert "kernel" in CATALOG.all_skills_available_through("S1")
    assert "http" in CATALOG.skills_available_through("S6")
    assert "oneliner" not in CATALOG.skills_available_through("S6")
    assert "sockets" not in CATALOG.skills_available_through("S6")
    assert "sockets" in CATALOG.skills_available_through("S7")


def test_catalog_exposes_ordered_quest_lookup() -> None:
    """Quest helpers use sequence order for deterministic selection."""
    assert [quest.id for quest in CATALOG.quests_available_after("S1")] == [
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
    ]
    assert [quest.id for quest in CATALOG.quests_available_after("S2")] == [
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
    ]
    assert [quest.id for quest in CATALOG.quests_available_after("S3")] == [
        "count-stream",
        "keep-pipeline-copy",
    ]
    assert [
        quest.id for quest in CATALOG.course.quests if quest.available_after_session == "S6"
    ] == ["resolve-hostname", "measure-ping", "read-http-headers", "check-personal-pages"]
    assert CATALOG.quests_available_after("S8")[0].id == "keep-tmux-workbench"
    quest_index = _content_text(f"content/{COURSE_ID}/quests/README.md")
    for session in CATALOG.course.sessions:
        section_match = re.search(
            (
                rf"(?ms)^## S{int(session.id[1:]):02d} Reinforcement\n"
                r"(?P<section>.*?)(?=^## |\Z)"
            ),
            quest_index,
        )
        assert tuple(quest.id for quest in CATALOG.quests_available_after(session.id)) == (
            tuple(re.findall(r"(?m)^- \[(?P<quest_id>[^]]+)\]\(", section_match["section"]))
            if section_match is not None
            else ()
        )
    assert [quest.id for quest in CATALOG.quests_available_through("S2")] == [
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
    ]
    assert CATALOG.next_quest_after(None, "S1") == CATALOG.quest("prove-shell-alive")
    assert CATALOG.next_quest_after("prove-shell-alive", "S1") == CATALOG.quest("name-system")
    assert CATALOG.next_quest_after("explain-ls", "S1") == CATALOG.quest("read-file-ends")
    assert CATALOG.next_quest_after("copy-and-inspect-ownership", "S2") == CATALOG.quest(
        "personalize-homepage",
    )
    assert CATALOG.next_quest_after("personalize-homepage", "S2") is None
    assert CATALOG.next_quest_after("write-next-path", "S9") == CATALOG.quest(
        "prepare-source-handoff",
    )
    assert CATALOG.next_quest_after("prepare-source-handoff", "S9") == CATALOG.quest(
        "use-terminal-irc",
    )
    assert CATALOG.next_quest_after("use-terminal-irc", "S9") is None
    assert CATALOG.next_assignable_quest("S1", frozenset()) == CATALOG.quest("prove-shell-alive")
    assert CATALOG.next_assignable_quest(
        "S1",
        frozenset(
            {
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
            },
        ),
    ) == CATALOG.quest("read-file-ends")
    assert CATALOG.next_assignable_quest("S2", frozenset()) == CATALOG.quest(
        "build-playground",
    )
    assert CATALOG.next_assignable_quest(
        "S2",
        frozenset(
            {
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
                "read-file-ends",
                "build-playground",
                "edit-with-micro",
                "redirect-and-append",
                "copy-and-inspect-ownership",
            },
        ),
    ) == CATALOG.quest("personalize-homepage")
    assert CATALOG.next_assignable_quest(
        "S2",
        frozenset(quest.id for quest in CATALOG.quests_available_after("S2")),
    ) == CATALOG.quest("prove-shell-alive")
    assert [
        quest.id
        for quest in CATALOG.prioritized_quests(
            "S2",
            CATALOG.quests_available_through("S2"),
        )
    ] == [
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
    ]


def test_prove_shell_alive_requires_explicit_guide_check() -> None:
    """Both quest surfaces distinguish command evidence from completion."""
    expected_instruction = "The commands provide evidence. Run `guide check` to complete the quest."
    quest_document = _content_text(f"content/{COURSE_ID}/quests/prove-shell-alive.md")

    assert expected_instruction in CATALOG.quest("prove-shell-alive").autonomy_checklist
    assert expected_instruction in quest_document
    assert "Progress records automatically" not in quest_document


def test_s2_quests_use_file_and_identity_validation() -> None:
    """S2 exercises cover file checks and ownership proof checks."""
    assert isinstance(CATALOG.quest("build-playground").validation, PathExistsValidation)
    assert isinstance(CATALOG.quest("edit-with-micro").validation, FileCheckValidation)
    assert isinstance(CATALOG.quest("redirect-and-append").validation, FileCheckValidation)
    ownership_validation = CATALOG.quest("copy-and-inspect-ownership").validation
    assert isinstance(ownership_validation, AllOfValidation)
    assert isinstance(ownership_validation.validations[0], OwnedPathValidation)
    assert isinstance(ownership_validation.validations[1], FileMatchesPathValidation)
    homepage_validation = CATALOG.quest("personalize-homepage").validation
    assert isinstance(homepage_validation, AllOfValidation)
    assert {
        validation.path
        for validation in homepage_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.forbidden_regex == r"A Linux site under construction"
    } == {"~/src/pages/index.md", "~/public_html/index.html"}
    assert CATALOG.session("S2").objectives[0].id == "ssh-public-key"


def test_s1_site_build_is_not_repeated_as_a_quest() -> None:
    """The first site build is a live objective, not a reinforcement quest."""
    assert "build-first-site" not in {quest.id for quest in CATALOG.course.quests}
    assert all(
        "build-website" not in quest.required_commands
        for quest in CATALOG.quests_available_after("S1")
    )


def test_s7_optional_setup_page_requires_linked_rebuild_evidence() -> None:
    """The optional setup quest retains linked publication evidence."""
    setup_validation = CATALOG.quest("create-setup-page").validation

    assert isinstance(setup_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/setup.md"
        and "#" in validation.required_regex
        for validation in setup_validation.validations
    )
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/index.md"
        and "setup" in validation.required_regex
        for validation in setup_validation.validations
    )
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^(?:build-website|maker-guide-build-personal-website)$"
        in validation.required_patterns
        for validation in setup_validation.validations
    )


def test_s7_manual_server_checks_do_not_require_foreground_or_failed_commands() -> None:
    """Successful HTTP history checks requests, not foreground lifecycle or response output."""
    assert tuple(objective.id for objective in CATALOG.session("S7").objectives) == (
        "inspect-first-url-headers",
        "diagnose-second-url",
    )
    assert CATALOG.quest("serve-local-check-page") in CATALOG.quests_available_after("S7")
    assert "manual-web-service" in CATALOG.skills_available_through("S7")
    for validation in (
        CATALOG.session("S7").objectives[0].validation,
        CATALOG.quest("serve-local-check-page").validation,
    ):
        assert isinstance(validation, CommandHistoryValidation)
        for document_name in ("slides.md", "self-study.md"):
            commands = _content_text(
                f"content/{COURSE_ID}/sessions/S07/{document_name}"
            ).splitlines()
            assert all(
                any(re.search(pattern, command) for command in commands)
                for pattern in validation.required_patterns
            )
        assert not any("caddy" in pattern for pattern in validation.required_patterns)
        assert not validation.ordered
    local_validation = CATALOG.session("S7").objectives[0].validation
    assert isinstance(local_validation, CommandHistoryValidation)
    assert len(local_validation.required_patterns) == 1
    for command in (
        'curl -i --max-time 10 "http://127.0.0.1:$PORT/"',
        'curl -I "http://127.0.0.1:${PORT}/"',
        "curl -i http://127.0.0.1:11234/",
        "curl -I localhost:11234",
        "curl -i http://localhost:11234/",
        "curl -i http://[::1]:11234/",
    ):
        assert re.search(local_validation.required_patterns[0], command)
    for command in (
        'curl -I "https://lf2607.kolamayermakers.org/~$USER/"',
        'curl -i "https://$USER.lf2607.kolamayermakers.org/"',
        'curl -i "http://127.0.0.1:$PORT/missing.html"',
    ):
        assert not re.search(local_validation.required_patterns[0], command)
    diagnosis_validation = CATALOG.session("S7").objectives[-1].validation
    assert isinstance(diagnosis_validation, InteractiveQuestionValidation)
    assert len(diagnosis_validation.required_concepts) == 3


def test_s7_companion_notes_reuse_setup() -> None:
    """Companion quests accept shared notes instead of requiring separate pages."""
    for quest_id, notes in (
        ("publish-http-troubleshooting", "200 works; 502 needs a backend check; 404 is missing"),
        ("publish-http-troubleshooting", "[Existing diagnosis](troubleshooting.html)"),
        ("document-service-port", "My UID is 1234; 10000 + UID gives port 11234."),
        ("document-service-port", "[My port explanation](service.html)"),
    ):
        quest = CATALOG.quest(quest_id)
        assert quest.available_after_session == "S7"
        assert isinstance(quest.validation, FileCheckValidation)
        assert quest.validation.path == "~/src/pages/setup.md"
        assert re.search(quest.validation.required_regex, notes)
        assert not re.search(quest.validation.required_regex, "# My setup\n")


def test_s3_objectives_and_reinforcement_require_lesson_evidence() -> None:
    """S3 checks cover streams, useful pipelines, and processes."""
    objectives = {objective.id: objective for objective in CATALOG.session("S3").objectives}
    combined_stream_validation = objectives["combine-and-copy-streams"].validation
    stream_validation = objectives["separate-standard-streams"].validation
    process_validation = objectives["read-process-table"].validation
    count_stream_validation = CATALOG.quest("count-stream").validation
    pipeline_copy_validation = CATALOG.quest("keep-pipeline-copy").validation

    assert isinstance(combined_stream_validation, AllOfValidation)
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns
        == (r"^date --debug \+%F 2>&1\s*\|\s*tee ~/playground/combined\.txt\s*\|\s*wc -l$",)
        and validation.observed_commands
        == ("date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",)
        for validation in combined_stream_validation.validations
    )
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/playground/combined.txt"
        and validation.required_regex
        == (
            r"(?ms)(?=.*^date:[^\n]*%F[^\n]*$)"
            r"(?=.*^[0-9]{4}-[0-9]{2}-[0-9]{2}$).+"
        )
        for validation in combined_stream_validation.validations
    )
    assert isinstance(stream_validation, AllOfValidation)
    stream_file_checks = {
        validation.path: validation
        for validation in stream_validation.validations
        if isinstance(validation, FileCheckValidation)
    }
    assert set(stream_file_checks) == {"~/playground/stdout.txt", "~/playground/stderr.txt"}
    assert stream_file_checks["~/playground/stdout.txt"].required_regex == r"(?m)^/etc/hostname$"
    assert stream_file_checks["~/playground/stdout.txt"].forbidden_regex == r"no/such/path"
    assert stream_file_checks["~/playground/stderr.txt"].required_regex == r"no/such/path"
    assert stream_file_checks["~/playground/stderr.txt"].forbidden_regex == r"/etc/hostname"
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns == (r"^cat /etc/hostname\s*>\s*/dev/null$",)
        and validation.observed_commands == ("cat /etc/hostname > /dev/null",)
        for validation in stream_validation.validations
    )
    assert all(
        not any("no/such/path" in pattern for pattern in validation.required_patterns)
        for validation in stream_validation.validations
        if isinstance(validation, CommandHistoryValidation)
    )
    assert objectives["separate-standard-streams"].prompt.count("mkdir -p ~/playground") == 1
    assert tuple(objectives) == (
        "separate-standard-streams",
        "make-first-pipe",
        "name-stdout-descriptor",
        "name-stdin-descriptor",
        "combine-and-copy-streams",
        "read-redirections-left-to-right",
        "route-stderr-to-stdout-destination",
        "read-process-table",
        "describe-running-process",
        "report-process-pair",
    )
    interactive_validations = tuple(
        validation
        for objective in objectives.values()
        if isinstance(objective.validation, AllOfValidation)
        for validation in objective.validation.validations
        if isinstance(validation, InteractiveQuestionValidation)
    )
    assert len(interactive_validations) == 9
    assert all(len(validation.required_concepts) == 1 for validation in interactive_validations)
    for objective_id in (
        "make-first-pipe",
        "name-stdout-descriptor",
        "name-stdin-descriptor",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, CommandHistoryValidation)
            and validation.required_patterns == (r"^cut -d: -f1 /etc/passwd\s*\|\s*wc -l$",)
            for validation in objective_validation.validations
        )
    for objective_id in (
        "combine-and-copy-streams",
        "read-redirections-left-to-right",
        "route-stderr-to-stdout-destination",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, FileCheckValidation)
            and validation.path == "~/playground/combined.txt"
            for validation in objective_validation.validations
        )
    for objective_id in (
        "read-process-table",
        "describe-running-process",
        "report-process-pair",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, CommandHistoryValidation)
            and validation.required_patterns == (r'^ps -u "\$USER" -o pid,comm,args$',)
            for validation in objective_validation.validations
        )
    assert isinstance(process_validation, AllOfValidation)
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns == (r'^ps -u "\$USER" -o pid,comm,args$',)
        for validation in process_validation.validations
    )
    assert isinstance(count_stream_validation, CommandHistoryValidation)
    assert count_stream_validation.required_patterns == (
        r"^cut -d: -f7 /etc/passwd\s*\|\s*sort -u\s*\|\s*wc -l$",
    )
    assert isinstance(pipeline_copy_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/playground/login-shells.txt"
        for validation in pipeline_copy_validation.validations
    )
    assert (
        "report one labeled numeric PID and command pair you read"
        in objectives["report-process-pair"].prompt
    )


def test_s3_combined_stream_pipeline_succeeds_with_pipefail(
    temporary_path: Path,
) -> None:
    """The documented GNU date pipeline preserves both streams and exits zero."""
    combined_output_path = temporary_path / "playground" / "combined.txt"
    combined_output_path.parent.mkdir()
    documented_pipeline = "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l"
    bash_path = shutil.which("bash")
    assert bash_path is not None

    completed_process = subprocess.run(
        [
            bash_path,
            "--noprofile",
            "--norc",
            "-c",
            f"set -o pipefail\n{documented_pipeline}",
        ],
        check=False,
        capture_output=True,
        env=os.environ | {"HOME": str(temporary_path)},
        text=True,
    )
    combined_output = combined_output_path.read_text(encoding="utf-8")

    assert completed_process.returncode == 0, completed_process.stderr
    assert completed_process.stdout.strip() == "2"
    assert len(combined_output.splitlines()) == 2
    assert re.search(r"(?m)^date:[^\n]*%F[^\n]*$", combined_output)
    assert re.search(r"(?m)^[0-9]{4}-[0-9]{2}-[0-9]{2}$", combined_output)


def test_open_concept_index_preserves_authored_skill_ownership() -> None:
    """The complete index keeps S3 core, enrichment, and later regex visibly distinct."""
    concept_index = _content_text(f"content/{COURSE_ID}/concepts/README.md")

    assert concept_index.index("(text-search.md)") < concept_index.index("### Go Deeper After S03")
    assert concept_index.index("### Go Deeper After S03") < concept_index.index("(signal.md)")
    assert concept_index.index("## S09 ") < concept_index.index("(regular-expression.md)")


def test_s3_cards_keep_later_syntax_out_of_completion_criteria() -> None:
    """Open cards identify read-ahead syntax without expanding the S3 proof scope."""
    stream_redirection = _content_text(f"content/{COURSE_ID}/concepts/stream-redirection.md")

    assert "`2>>` is optional exploration for later" in stream_redirection
    assert (
        "`2>>`"
        not in stream_redirection.split("## Done When", maxsplit=1)[1].split(
            "## Go Deeper", maxsplit=1
        )[0]
    )
    assert "Regex anchors are optional exploration for later" in _content_text(
        f"content/{COURSE_ID}/commands/grep.md"
    )
    assert "`2>>` is optional exploration for later" in _content_text(
        f"content/{COURSE_ID}/commands/stderr-redirect.md"
    )


def test_guide_answer_commands_quote_shell_payloads() -> None:
    """Support and quest answer examples survive shell parsing without lesson bot snippets."""
    answer_commands = [
        f"guide answer {answer_match.group('payload')}"
        for document_path in (
            f"content/{COURSE_ID}/README.md",
            f"content/{COURSE_ID}/guides/platform-reference.md",
            f"content/{COURSE_ID}/quests/README.md",
            *(
                content.path
                for quest in CATALOG.quests_available_after("S3")
                for content in quest.docs
            ),
        )
        for answer_match in re.finditer(
            r"`guide answer (?P<payload>[^`]+)`",
            _content_text(document_path),
        )
    ]

    assert answer_commands
    bash_path = shutil.which("bash")
    assert bash_path is not None
    for answer_command in answer_commands:
        assert answer_command.startswith("guide answer '")
        assert answer_command.endswith("'")
        completed_process = subprocess.run(
            [
                bash_path,
                "--noprofile",
                "--norc",
                "-c",
                f"set -- {answer_command}\nprintf '%s\\0' \"$@\"",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed_process.returncode == 0, completed_process.stderr
        assert completed_process.stdout.split("\0") == [
            "guide",
            "answer",
            answer_command.removeprefix("guide answer '").removesuffix("'"),
            "",
        ]


def test_s3_material_uses_one_quick_preflight_and_does_not_supply_answers() -> None:
    """S3 restores its work directory once and asks learners to explain concepts themselves."""
    session_documents = tuple(
        _content_text(content.path) for content in CATALOG.session("S3").content
    )
    session_text = "\n".join(session_documents)
    objectives = {objective.id: objective for objective in CATALOG.session("S3").objectives}
    pipe_objective = objectives["make-first-pipe"]

    assert all(document.count("mkdir -p ~/playground") == 1 for document in session_documents)
    assert "guide answer 'cut writes stdout (1); wc reads stdin (0)'" not in session_text
    assert (
        "guide answer 'A binary executable is a program file; a process is a running instance.'"
        not in session_text
    )
    assert "The file can exist for years." not in session_text
    assert "Bash" not in session_text
    assert "`cut` writes stdout" not in pipe_objective.prompt
    assert "`wc` reads stdin" not in pipe_objective.prompt
    assert "stdout" not in pipe_objective.title.casefold()
    assert "stdin" not in pipe_objective.title.casefold()
    assert "left to right" not in objectives["read-redirections-left-to-right"].title.casefold()
    assert "stdout" not in objectives["route-stderr-to-stdout-destination"].title.casefold()
    assert "answer payload" not in session_text


def test_early_session_docs_do_not_require_bot_checkpoints() -> None:
    """Live S1-S6 exercises do not require optional recorded-progress commands."""
    for session in CATALOG.sessions_through("S6"):
        for content in session.content:
            assert not re.search(r"`guide (?:now|check|answer)\b", _content_text(content.path))


def test_curriculum_avoids_shell_redirection_as_answer_placeholder() -> None:
    """Terminal answer placeholders are quoted instead of parsed as redirections."""
    for markdown_resource in _markdown_resources(_content_root()):
        assert "guide answer <" not in markdown_resource.read_text(encoding="utf-8"), (
            f"shell-unsafe guide answer placeholder in {markdown_resource}"
        )
    assert all(
        "guide answer <" not in hint.text for quest in CATALOG.course.quests for hint in quest.hints
    )
    assert all(
        "guide answer <" not in feedback.text
        for quest in CATALOG.course.quests
        for feedback in quest.failure_feedback
    )


def test_s8_tmux_and_service_quests_require_real_evidence() -> None:
    """Core service gates are safe; tmux and the helper remain optional quests."""
    objectives = {objective.id: objective for objective in CATALOG.session("S8").objectives}
    tmux_validation = CATALOG.quest("keep-tmux-workbench").validation
    log_validation = CATALOG.quest("watch-service-logs").validation

    assert set(objectives) == {
        "enable-site-service",
        "watch-service-logs",
        "break-and-read-error",
        "test-logout-survival",
    }
    assert isinstance(tmux_validation, CommandHistoryValidation)
    assert tmux_validation.ordered is True
    assert tmux_validation.required_patterns == (
        r"^tmux new -s quest-workbench$",
        r"^tmux ls$",
        r"^tmux attach -t quest-workbench$",
        r"^tmux kill-session -t quest-workbench$",
    )
    assert isinstance(log_validation, InteractiveQuestionValidation)
    assert all(
        any(
            re.search(
                alias,
                (
                    '{"ts":1790400000,"request":{"method":"get","uri":"/missing-page.html"},'
                    '"status":404}; '
                    "journalctl stopped, personal caddy kept serving"
                ),
            )
            for alias in concept.aliases
        )
        for concept in log_validation.required_concepts
    )
    self_study = _content_text(f"content/{COURSE_ID}/sessions/S08/self-study.md")
    reference_unit = next(
        unit_match["unit"]
        for unit_match in re.finditer(r"(?ms)^```ini\n(?P<unit>.*?)^```$", self_study)
        if "ExecStart=/usr/bin/caddy file-server" in unit_match["unit"]
    )
    service_commands = self_study.splitlines()
    for service_validation in (
        objectives["enable-site-service"].validation,
        CATALOG.quest("enable-site-service").validation,
    ):
        assert isinstance(service_validation, AllOfValidation)
        port_validation = next(
            validation
            for validation in service_validation.validations
            if isinstance(validation, UserPortFileValidation)
        )
        required_regex = port_validation.required_regex_template.replace("{port}", "11234")
        assert re.search(required_regex, reference_unit.replace("12345", "11234"))
        assert re.search(
            required_regex,
            reference_unit.replace("--listen :12345", "--listen 127.0.0.1:11234"),
        )
        for invalid_port in ("12345", "11235", "$PORT", "$((10000 + $(id -u)))"):
            assert not re.search(required_regex, reference_unit.replace("12345", invalid_port))
        for unsafe_unit in (
            reference_unit.replace(" --root %h/public_html", ""),
            reference_unit.replace(" --root %h/public_html", " --root %h"),
            reference_unit.replace("WorkingDirectory=%h\n", "WorkingDirectory=%h/public_html\n"),
            reference_unit.replace(" --access-log", ""),
            reference_unit.replace("/usr/bin/caddy", "/no/such/caddy"),
        ):
            assert not re.search(required_regex, unsafe_unit.replace("12345", "11234"))
        history_validation = next(
            validation
            for validation in service_validation.validations
            if isinstance(validation, CommandHistoryValidation)
        )
        assert all(
            any(re.search(pattern, command) for command in service_commands)
            for pattern in history_validation.required_patterns
        )
        for omitted_text in ("systemctl --user enable", "http://", "https://"):
            assert not all(
                any(
                    re.search(pattern, command)
                    for command in service_commands
                    if omitted_text not in command
                )
                for pattern in history_validation.required_patterns
            ), omitted_text

    helper_validation = CATALOG.quest("write-site-helper-functions").validation
    assert isinstance(helper_validation, InteractiveQuestionValidation)
    assert all(
        any(
            re.search(alias, "calling site_logs reads the journal; source only trusted definitions")
            for alias in concept.aliases
        )
        for concept in helper_validation.required_concepts
    )

    preflight_validation = CATALOG.quest("preflight-both-urls").validation
    assert isinstance(preflight_validation, CommandHistoryValidation)
    preflight_commands = _content_text(
        f"content/{COURSE_ID}/quests/preflight-both-urls.md"
    ).splitlines()
    for username, quote, accepted in (
        ("$USER", '"', True),
        ("${USER}", '"', True),
        ("$USER", "", True),
        ("${USER}", "", True),
        ("learner", '"', True),
        ("learner", "'", True),
        ("learner", "", True),
        ("$USER", "'", False),
        ("${USER}", "'", False),
    ):
        assert (
            all(
                any(
                    re.search(pattern, command.replace("$USER", username).replace('"', quote))
                    for command in preflight_commands
                )
                for pattern in preflight_validation.required_patterns
            )
            is accepted
        ), (username, quote)
    for omitted_text in (
        "https://lf2607.",
        "https://$USER.",
        "systemctl --user show site.service",
    ):
        assert not all(
            any(
                re.search(pattern, command)
                for command in preflight_commands
                if omitted_text not in command
            )
            for pattern in preflight_validation.required_patterns
        ), omitted_text


def test_s8_repair_and_logout_checks_accept_reported_observations() -> None:
    """Consent-based observation counts without requiring failed commands or claimed uptime."""
    objectives = {objective.id: objective for objective in CATALOG.session("S8").objectives}
    enable_validation = objectives["enable-site-service"].validation
    assert isinstance(enable_validation, AllOfValidation)
    for repair_validation in (
        objectives["break-and-read-error"].validation,
        CATALOG.quest("break-and-read-error").validation,
    ):
        assert isinstance(repair_validation, AllOfValidation)
        assert any(
            isinstance(validation, UserPortFileValidation)
            and validation in enable_validation.validations
            for validation in repair_validation.validations
        )
        assert not any(
            isinstance(validation, CommandHistoryValidation)
            for validation in repair_validation.validations
        )
        explanation = next(
            validation
            for validation in repair_validation.validations
            if isinstance(validation, InteractiveQuestionValidation)
        )
        assert all(
            any(
                re.search(
                    alias,
                    (
                        "i observed staff get 203/exec from the bad executable path, then restored "
                        "the backup, reloaded, restarted, and checked the page response"
                    ),
                )
                for alias in concept.aliases
            )
            for concept in explanation.required_concepts
        )
    logout_validation = objectives["test-logout-survival"].validation
    assert isinstance(logout_validation, InteractiveQuestionValidation)
    for answer in (
        "linger=yes; the browser worked while logged out; pid and start time were unchanged",
        "linger=no; the browser failed while logged out; the pid and start time changed on login",
        "lingering was unknown; another login remained so the browser and pid were inconclusive",
    ):
        assert all(
            any(re.search(alias, answer) for alias in concept.aliases)
            for concept in logout_validation.required_concepts
        )
    assert not all(
        any(re.search(alias, "the service is active after login") for alias in concept.aliases)
        for concept in logout_validation.required_concepts
    )
    content_repair = CATALOG.quest("fix-and-restart-service").validation
    assert isinstance(content_repair, InteractiveQuestionValidation)
    assert all(
        any(
            re.search(
                alias,
                (
                    "the page returned 404; i fixed its source path, built, and reloaded the "
                    "browser. the response contained the right page without restarting "
                    "personal caddy."
                ),
            )
            for alias in concept.aliases
        )
        for concept in content_repair.required_concepts
    )


def test_s9_optional_automation_quests_require_cleanup_and_output() -> None:
    """Optional cron and webring quests retain their cleanup and generated-output checks."""
    cron_validation = CATALOG.quest("try-cron-and-remove-it").validation
    webring_validation = CATALOG.quest("enable-webring").validation

    assert isinstance(cron_validation, AllOfValidation)
    cleanup_validation = next(
        validation
        for validation in cron_validation.validations
        if isinstance(validation, FileCheckValidation) and validation.path == "~/crontab.after"
    )
    assert cleanup_validation.forbidden_regex is not None
    cron_demo = (
        _content_text(f"content/{COURSE_ID}/quests/try-cron-and-remove-it.md")
        .split("```text\n", 1)[1]
        .split("\n```", 1)[0]
    )
    unrelated_job = "0 3 * * * /home/learner/bin/backup >> /home/learner/cron.log 2>&1\n"
    for remaining_crontab in ("", unrelated_job, f"{unrelated_job}  # {cron_demo}\n"):
        assert re.search(cleanup_validation.required_regex, remaining_crontab)
        assert not re.search(cleanup_validation.forbidden_regex, remaining_crontab)
    for active_demo in (cron_demo, f"  {cron_demo}", cron_demo.replace("cron.log", "demo.log")):
        assert re.search(cleanup_validation.forbidden_regex, f"{unrelated_job}{active_demo}\n")
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^crontab -l > ~/crontab\.after 2>/dev/null \|\| true$" in validation.required_patterns
        for validation in cron_validation.validations
    )
    assert isinstance(webring_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and "(?=.*\\bprevious\\b)" in validation.required_regex
        and "(?=.*\\bnext\\b)" in validation.required_regex
        for validation in webring_validation.validations
    )


def test_s9_automation_requires_report_before_build_and_hourly_schedule() -> None:
    """Automation cannot omit report generation or leave the short demonstration schedule."""
    for timer_validation in (
        next(
            objective.validation
            for objective in CATALOG.session("S9").objectives
            if objective.id == "schedule-site-rebuilds"
        ),
        CATALOG.quest("schedule-site-rebuilds").validation,
    ):
        assert isinstance(timer_validation, AllOfValidation)
        for validation in timer_validation.validations:
            if isinstance(validation, FileCheckValidation):
                reference_unit = next(
                    unit_match["unit"]
                    for unit_match in re.finditer(
                        r"(?ms)^```ini\n(?P<unit>.*?)^```$",
                        _content_text(f"content/{COURSE_ID}/sessions/S09/self-study.md"),
                    )
                    if (
                        "Type=oneshot" in unit_match["unit"]
                        if validation.path.endswith(".service")
                        else "OnActiveSec=1h" in unit_match["unit"]
                    )
                )
                assert re.search(validation.required_regex, reference_unit)
                if validation.path.endswith(".timer"):
                    assert validation.forbidden_regex is not None
                    assert not re.search(validation.forbidden_regex, reference_unit)
                    for extra_schedule in (
                        "OnActiveSec=30s",
                        "OnUnitInactiveSec=2min",
                        "OnUnitActiveSec=1h",
                        "OnBootSec=5min",
                        "OnCalendar=minutely",
                    ):
                        assert re.search(
                            validation.forbidden_regex,
                            reference_unit.replace("[Timer]", f"[Timer]\n{extra_schedule}"),
                        )
                for required_line in reference_unit.splitlines():
                    if required_line.startswith(
                        (
                            "OnActiveSec=",
                            "OnUnitInactiveSec=",
                            "WorkingDirectory=",
                            "ExecStartPre=",
                            "ExecStart=",
                        )
                    ):
                        assert not re.search(
                            validation.required_regex,
                            reference_unit.replace(required_line, ""),
                        )
                if validation.path.endswith(".service"):
                    for invalid_pre_start in (
                        'ExecStartPost=/bin/bash %h/scripts/maker-report.sh "System Report"',
                        'ExecStartPre=-/bin/bash %h/scripts/maker-report.sh "System Report"',
                        "ExecStartPre=/bin/bash %h/scripts/maker-report.sh",
                    ):
                        assert not re.search(
                            validation.required_regex,
                            reference_unit.replace(
                                'ExecStartPre=/bin/bash %h/scripts/maker-report.sh "System Report"',
                                invalid_pre_start,
                            ),
                        )
        assert any(
            isinstance(validation, CommandHistoryValidation)
            and r"^systemctl --user enable --now site-build\.timer$" in validation.required_patterns
            for validation in timer_validation.validations
        )

    assert {objective.id for objective in CATALOG.session("S9").objectives} == {
        "schedule-site-rebuilds",
        "write-readme",
        "prepare-source-handoff",
    }
    assert {
        "transform-heading-with-sed",
        "extract-fields-with-awk",
        "survive-vim",
        "enable-webring",
    } <= {quest.id for quest in CATALOG.quests_available_after("S9")}


def test_final_handoff_requires_committed_files_without_prescribing_next_page_wording() -> None:
    """The handoff preserves core files; optional next-page checks accept learner wording."""
    readme_text = (
        "# My Homepage\n\nBuild: `build-website`.\n"
        "Service: `systemctl --user start site.service`.\n"
    )
    for readme_validation in (
        next(
            objective.validation
            for objective in CATALOG.session("S9").objectives
            if objective.id == "write-readme"
        ),
        CATALOG.quest("write-readme").validation,
    ):
        assert isinstance(readme_validation, FileCheckValidation)
        assert re.search(readme_validation.required_regex, readme_text)
        assert re.search(
            readme_validation.required_regex,
            readme_text.replace("build-website", "systemctl --user start site-build.service"),
        )
        for required_text in ("# My Homepage", "build-website", "systemctl --user"):
            assert not re.search(
                readme_validation.required_regex, readme_text.replace(required_text, "")
            )

    for handoff_validation in (
        next(
            objective.validation
            for objective in CATALOG.session("S9").objectives
            if objective.id == "prepare-source-handoff"
        ),
        CATALOG.quest("prepare-source-handoff").validation,
    ):
        assert isinstance(handoff_validation, AllOfValidation)
        assert {
            (validation.repository_path, validation.path)
            for validation in handoff_validation.validations
            if isinstance(validation, GitTrackedPathValidation)
        } == {
            ("~/src", path)
            for path in (
                "README.md",
                "scripts/maker-report.sh",
                "scripts/site-check.sh",
                "services/site.service",
                "services/site-build.service",
                "services/site-build.timer",
            )
        }

    next_validation = CATALOG.quest("write-next-path").validation
    assert isinstance(next_validation, InteractiveQuestionValidation)
    for answer in (
        "Tomorrow I will add a page and check it from my laptop.",
        "On 2026-10-31 I will read the manual, try an experiment, and record the result.",
    ):
        assert all(
            any(re.search(alias, answer.casefold()) for alias in concept.aliases)
            for concept in next_validation.required_concepts
        )
    for incomplete_plan in ("", "Linux", "I will learn more", "Tomorrow I will learn more"):
        assert not all(
            any(re.search(alias, incomplete_plan.casefold()) for alias in concept.aliases)
            for concept in next_validation.required_concepts
        )
    assert CATALOG.session("S10").objectives == ()


def test_s10_terminal_irc_quest_uses_ctcp_version_validation() -> None:
    """The terminal IRC challenge accepts only terminal IRC clients."""
    quest = CATALOG.quest("use-terminal-irc")
    validation = CATALOG.quest("use-terminal-irc").validation

    assert quest.required_commands == ("weechat",)
    assert isinstance(validation, IrcCtcpVersionValidation)
    assert validation.accepted_clients == ("WeeChat", "irssi", "BitchX")


def test_demo_accepts_learner_selected_evidence_without_an_artifact_tour() -> None:
    """A script demonstration does not require claiming a service or repository demo."""
    validation = CATALOG.quest("demo-site").validation
    assert isinstance(validation, InteractiveQuestionValidation)
    assert all(
        any(
            re.search(
                alias,
                (
                    "i showed my checker output and explained how i fixed its quoting error. "
                    "the repeated request succeeded; my peer suggested clearer usage instructions."
                ),
            )
            for alias in concept.aliases
        )
        for concept in validation.required_concepts
    )


def test_packaged_content_references_exist_and_are_non_empty() -> None:
    """Catalog content references point at packaged Markdown resources."""
    for content_reference in CATALOG.content_references():
        assert _content_text(content_reference.path).strip() != ""


def test_course_has_top_level_start_page() -> None:
    """Autonomous learners have a deterministic entry point."""
    start_text = _content_text(f"content/{COURSE_ID}/README.md")

    assert "Start here" in start_text
    assert "## Optional Quest Map" in start_text
    assert "## Quest Calendar" in start_text
    assert "They are not prerequisites for attending the next live session." in start_text


def test_open_reference_indexes_link_every_card() -> None:
    """Every open command and concept card is discoverable from its authored index."""
    for directory_name in ("commands", "concepts"):
        card_directory = _content_root().joinpath(directory_name)
        indexed_card_names = {
            Path(link_target.partition("#")[0]).name
            for link_target in _markdown_link_targets(
                card_directory.joinpath("README.md").read_text(encoding="utf-8")
            )
        }

        assert indexed_card_names == {
            child_resource.name
            for child_resource in card_directory.iterdir()
            if child_resource.is_file()
            and child_resource.name.endswith(".md")
            and child_resource.name != "README.md"
        }


def test_content_link_labels_close_inline_code_spans() -> None:
    """Every Markdown link label has balanced inline-code delimiters."""
    for markdown_resource in _markdown_resources(_content_root()):
        for link_match in MARKDOWN_LINK_PATTERN.finditer(
            markdown_resource.read_text(encoding="utf-8"),
        ):
            assert link_match.group("label").count("`") % 2 == 0, (
                f"unbalanced inline code in {markdown_resource}: {link_match.group()}"
            )


def test_local_markdown_links_resolve() -> None:
    """Only actual local links, not code examples, must resolve to packaged resources."""
    for markdown_resource in _markdown_resources(_content_root()):
        for link_target in _markdown_link_targets(markdown_resource.read_text(encoding="utf-8")):
            if _is_external_or_page_anchor(link_target):
                continue
            assert _linked_resource_path(markdown_resource, link_target).exists(), (
                f"broken link in {markdown_resource}: {link_target}"
            )


def test_quest_related_reading_entries_are_clickable_links() -> None:
    """Quest reading lists must be links, not inert path text."""
    for markdown_resource in _markdown_resources(_content_root().joinpath("quests")):
        for related_reading_entry in _related_reading_entries(
            markdown_resource.read_text(encoding="utf-8"),
        ):
            assert RELATED_READING_LINK_PATTERN.fullmatch(related_reading_entry), (
                f"non-link related reading in {markdown_resource}: {related_reading_entry}"
            )


def test_quest_command_sections_match_catalog() -> None:
    """Quest command lists, when present, agree with catalog availability metadata."""
    for quest in LINUX_FOUNDATIONS_2026_07.quests:
        quest_text = _content_text(f"content/{COURSE_ID}/quests/{quest.id}.md")

        if "## Commands You Will Use" in quest_text:
            assert _quest_command_entries(quest_text) == quest.required_commands


def test_sessions_have_presenterm_slides_self_study_and_recaps() -> None:
    """Every live session has cataloged live and autonomous learner content."""
    for session in LINUX_FOUNDATIONS_2026_07.sessions:
        content_by_purpose = {
            content_reference.purpose: content_reference for content_reference in session.content
        }
        assert set(content_by_purpose) == {"slides", "self-study", "recap"}
        assert content_by_purpose["slides"].path.endswith(
            f"sessions/{_session_directory(session.id)}/slides.md",
        )
        assert content_by_purpose["self-study"].path.endswith(
            f"sessions/{_session_directory(session.id)}/self-study.md",
        )
        slides_text = _content_text(content_by_purpose["slides"].path)
        assert f"Session: {session.id}" in slides_text
        assert "<!-- end_slide -->" in slides_text
        assert "---" not in slides_text.splitlines()


def test_full_course_autonomous_content_covers_commands_skills_and_quests() -> None:
    """Every session has enough packaged content for autonomous learner progress."""
    for session in LINUX_FOUNDATIONS_2026_07.sessions:
        _assert_autonomous_content_through(session.id)


def test_high_friction_command_cards_have_docs_pointers() -> None:
    """Troubleshooting-heavy commands point learners to authoritative references."""
    for command in (
        "bat",
        "chmod",
        "chmod +x",
        "journalctl --user",
        "systemd timer",
        "cron",
        "crontab",
        "rm -rf",
        "set -euo pipefail",
        "sed",
        "awk",
        "vim",
    ):
        assert "## Docs Pointers" in _content_text(_command_document_path(command))


def test_git_command_index_exists() -> None:
    """The git command family has an index page for learner navigation."""
    assert _content_text(f"content/{COURSE_ID}/commands/git.md").strip() != ""


def _assert_autonomous_content_through(session_id: str) -> None:
    for command in CATALOG.commands_available_through(session_id):
        assert _content_text(_command_document_path(command)).strip() != ""

    for skill in CATALOG.all_skills_available_through(session_id):
        assert _content_text(f"content/{COURSE_ID}/concepts/{skill}.md").strip() != ""

    for quest in CATALOG.quests_available_after(session_id):
        quest_text = _content_text(f"content/{COURSE_ID}/quests/{quest.id}.md")
        assert f"Quest: {quest.id}" in quest_text
        assert "## Mission" in quest_text or "## Optional Mission" in quest_text
        assert len(quest.hints) >= 3
        assert quest.failure_feedback
        assert quest.story.strip() != ""
        assert quest.learner_goal.strip() != ""
        assert quest.autonomy_checklist


def test_curriculum_content_uses_current_course_hosts_and_day_language() -> None:
    """Packaged teaching content uses current domain names and daytime session language."""
    all_content_text = "\n".join(
        markdown_resource.read_text(encoding="utf-8")
        for markdown_resource in _markdown_resources(_content_root())
    )

    assert "kolammakers.cc" not in all_content_text
    assert "genesis.kolammakers.cc" not in all_content_text
    assert "$fqdn" not in all_content_text
    assert "hello kolam" not in all_content_text.lower()
    assert "tonight" not in all_content_text.lower()
    assert "learner service" not in all_content_text.lower()
    assert "learner-managed service" not in all_content_text.lower()
    assert "Allowed Commands" not in all_content_text
    assert "TheGuide" not in all_content_text
    assert "lf2607.kolamayermakers.org" in all_content_text
    assert "https://lf2607.kolamayermakers.org/git/" in all_content_text
    assert "https://lf2607.kolamayermakers.org/irc/" in all_content_text
    assert "git.kolamayermakers.org" not in all_content_text
    assert "irc.kolamayermakers.org" not in all_content_text
    assert "lf2607.kolamayermakers.org/~username" in all_content_text
    assert "ssh-copy-id <handle>@lf2607.kolamayermakers.org" in all_content_text
    assert "Get-Content ~/.ssh/id_ed25519.pub" in all_content_text
    assert "preview-only command" in all_content_text
    assert "ssh-copy-id" in all_content_text
    assert "cat >> ~/.ssh/authorized_keys" in all_content_text
    assert "chmod 700 ~/.ssh" in all_content_text
    assert "current objective or quest" not in all_content_text
    assert "current session objective" in all_content_text


def test_webring_uses_the_deployed_course_group() -> None:
    """Webring membership follows the deployed Linux Foundations group."""
    site_source = files("maker_guide.astro_starter").joinpath("template/app/lib/site.mjs")

    assert '["group", "linux-foundations"]' in site_source.read_text(encoding="utf-8")
    assert '["group", "lf2607"]' not in site_source.read_text(encoding="utf-8")


def test_curriculum_content_keeps_quests_optional_and_internals_hidden() -> None:
    """Learner content does not make quests into live-session gates or leak internals."""
    all_content_text = "\n".join(
        markdown_resource.read_text(encoding="utf-8")
        for markdown_resource in _markdown_resources(_content_root(), frozenset({"mentors"}))
    )

    for forbidden_phrase in (
        "Python catalog",
        "maker-guide",
        "validation logic",
        "Autonomous Quest Spine",
        "Run your daily quests",
        "Fix failures before the polish session",
        "before the live session starts",
        "complete quests before",
        "quests are required",
    ):
        assert forbidden_phrase not in all_content_text


def test_sqlite_schema_stores_catalog_ids_not_catalog_definitions(
    migrated_database_path: Path,
) -> None:
    """SQLite learner state stores catalog ids, not catalog-owned definition tables."""
    with sqlite3.connect(migrated_database_path) as database_connection:
        table_name_rows = cast(
            "list[tuple[str]]",
            database_connection.execute(
                "select name from sqlite_master where type = 'table'",
            ).fetchall(),
        )

    assert {"courses", "sessions", "quests", "tiers"}.isdisjoint(
        {table_name for (table_name,) in table_name_rows},
    )


def _content_root() -> Traversable:
    return files("maker_guide.curriculum").joinpath("content", COURSE_ID)


def _content_text(content_path: str) -> str:
    return files("maker_guide.curriculum").joinpath(content_path).read_text(encoding="utf-8")


def _markdown_link_targets(markdown_text: str) -> tuple[str, ...]:
    return tuple(
        link_target
        for inline_token in Markdown(markdown_text).parsed
        if inline_token.type == "inline"
        for child_token in inline_token.children or ()
        if child_token.type == "link_open"
        and isinstance(link_target := child_token.attrGet("href"), str)
    )


def _is_external_or_page_anchor(link_target: str) -> bool:
    return link_target.startswith(("#", "mailto:")) or "://" in link_target


def _linked_resource_path(markdown_resource: Traversable, link_target: str) -> Path:
    link_path = link_target.split("#", maxsplit=1)[0]
    if link_path.startswith(DOCS_PATH_PREFIX):
        return (Path(str(_content_root())) / link_path.removeprefix(DOCS_PATH_PREFIX)).resolve()
    return (Path(str(markdown_resource)).parent / link_path.removeprefix("./")).resolve()


def _related_reading_entries(markdown_text: str) -> tuple[str, ...]:
    related_reading_heading = "## Related Reading"
    if related_reading_heading not in markdown_text:
        return ()
    related_reading_text = markdown_text.split(related_reading_heading, maxsplit=1)[1]
    section_text = related_reading_text.split("\n## ", maxsplit=1)[0]
    return tuple(line for line in section_text.splitlines() if line.startswith("- "))


def _quest_command_entries(markdown_text: str) -> tuple[str, ...]:
    command_heading = "## Commands You Will Use"
    if command_heading not in markdown_text:
        return ()
    command_section_text = markdown_text.split(command_heading, maxsplit=1)[1]
    section_text = command_section_text.split("\n## ", maxsplit=1)[0]
    return tuple(
        line.removeprefix("- `").removesuffix("`")
        for line in section_text.splitlines()
        if line.startswith("- `") and line.endswith("`")
    )


def _command_document_path(command: str) -> str:
    return f"content/{COURSE_ID}/commands/{command_card_slug(command)}.md"


def _session_directory(session_id: str) -> str:
    return f"S{int(session_id.removeprefix('S')):02d}"


def _markdown_resources(
    root: Traversable,
    excluded_directory_names: frozenset[str] = frozenset(),
) -> tuple[Traversable, ...]:
    markdown_resources: list[Traversable] = []
    for child in root.iterdir():
        if child.is_dir():
            if child.name not in excluded_directory_names:
                markdown_resources.extend(
                    _markdown_resources(child, excluded_directory_names),
                )
        elif child.name.endswith(".md"):
            markdown_resources.append(child)
    return tuple(markdown_resources)

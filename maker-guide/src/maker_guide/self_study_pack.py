"""Export public learner PDFs and a local practice kit, never learner account data."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import cast
from zipfile import ZIP_DEFLATED, ZipFile

from maker_guide.repositories.helpers import dump_json, load_json

_PACKAGE = Path(__file__).resolve().parent
_COURSE = _PACKAGE / "curriculum/content/lf2607"
_MARKDOWN_LINK = re.compile(r"(?<=\]\()(?P<path>[^\s)]+\.md)(?P<anchor>#[^\s)]*)?")
_FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
_PDF_HEADER = r"""
\usepackage{fvextra}
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\},
  breaklines,breakanywhere,breaknonspaceingroup,fontsize=\small}
\RecustomVerbatimEnvironment{verbatim}{Verbatim}{breaklines,breakanywhere,fontsize=\small}
\usepackage{seqsplit}
\renewcommand{\seqinsert}{\penalty1000}
% Pandoc emits \^{} for a literal caret, not an accent.
\DeclareRobustCommand{\texttt}[1]{{\ttfamily\let\^\textasciicircum\seqsplit{#1}}}
"""


def write_practice_kit(output: Path) -> None:
    """Write only an explicit public starter allowlist and public course readings."""
    template = _PACKAGE / "astro_starter/template"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        root = "linux-foundations-practice"
        for name in (
            ".gitignore",
            "package-lock.json",
            "app/content.config.ts",
            "app/pages/index.astro",
            "app/pages/[...slug].astro",
            "scripts/publish.mjs",
            "scripts/publish.test.mjs",
        ):
            archive.write(template / name, f"{root}/site/{name}")
        build = (template / "scripts/build.mjs").read_text(encoding="utf-8")
        build = build.replace('import { buildCodex } from "./codex.mjs";\n', "")
        build = build.replace("  await buildCodex(stagingDirectory);\n", "")
        archive.writestr(f"{root}/site/scripts/build.mjs", build)
        manifest = load_json((template / "package.json").read_text(encoding="utf-8"))
        manifest["scripts"] = {"build": "node scripts/build.mjs"}
        archive.writestr(f"{root}/site/package.json", dump_json(manifest) + "\n")
        # Keep the lockfile's package identity/dependencies; change only local scripts/layout.
        configuration = (template / "astro.config.mjs").read_text(encoding="utf-8")
        configuration = configuration.replace('import { userInfo } from "node:os";\n', "")
        configuration = configuration.replace("  base: `/~${userInfo().username}/`,\n", "")
        archive.writestr(f"{root}/site/astro.config.mjs", configuration)
        archive.write(
            _COURSE / "guides/resources/home-layout.astro",
            f"{root}/site/app/layouts/SiteLayout.astro",
        )
        archive.write(_PACKAGE / "astro_shared/site.css", f"{root}/site/app/styles/site.css")
        archive.writestr(f"{root}/site/app/styles/student.css", "")
        archive.writestr(
            f"{root}/site/pages/index.md",
            "# My Linux site\n\nBuilt from Markdown on my own Ubuntu machine.\n",
        )
        for name in ("maker-report.sh", "today.sh"):
            archive.write(_COURSE / f"guides/resources/{name}", f"{root}/answers/{name}")
        checker = (_COURSE / "sessions/S06/self-study.md").read_text(encoding="utf-8")
        checker = checker.split("````bash\n", 1)[1].split("\n````", 1)[0]
        checker = checker.replace("then build-website.", "then cd ~/src && node scripts/build.mjs.")
        archive.writestr(f"{root}/answers/site-check.sh", checker + "\n")
        archive.write(_COURSE / "sessions/S09/resources/today.sh", f"{root}/starters/today.sh")
        for document in _documents():
            archive.write(document, f"{root}/reading/{document.relative_to(_COURSE)}")
        archive.write(
            _COURSE / "guides/resources/today.sh", f"{root}/reading/guides/resources/today.sh"
        )
        archive.writestr(
            f"{root}/README.txt",
            dedent("""\
                Start with the Continue at Home PDF, or reading/guides/continue-at-home.md.
                Use Ubuntu LTS. Keep existing ~/src and ~/public_html work safe.
                Try exercises before consulting answers/. No class account or token is needed.
                """),
        )


def _documents() -> list[Path]:
    """Select self-study and reference cards, not slides, mentors, or private exports."""
    return sorted(
        [
            *_COURSE.glob("sessions/*/self-study.md"),
            *_COURSE.glob("guides/*.md"),
            *_COURSE.glob("commands/*.md"),
            *_COURSE.glob("concepts/*.md"),
        ]
    )


def _pdf_markdown(document: Path, documents: set[Path]) -> str:
    """Keep shipped Markdown links relative to the corresponding PDFs."""
    # ponytail: inline links only; use a Pandoc AST filter if reference-style links appear.
    text = document.read_text(encoding="utf-8")

    def replace_link(match: re.Match[str]) -> str:
        path = match["path"]
        if ":" in path or path.startswith("/"):
            return match[0]
        target = (document.parent / path).resolve()
        if target not in documents:
            return match[0]
        return str(Path(path).with_suffix(".pdf")) + (match["anchor"] or "")

    fence = ""
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        marker = _FENCE.match(line)
        if marker is not None:
            delimiter = marker["fence"]
            if not fence:
                fence = delimiter
            elif (
                delimiter[0] == fence[0]
                and len(delimiter) >= len(fence)
                and not line[marker.end() :].strip()
            ):
                fence = ""
            lines.append(line)
        else:
            lines.append(line if fence else _MARKDOWN_LINK.sub(replace_link, line))
    return "".join(lines)


def main() -> None:
    """Export without contacting classroom services or reading learner homes."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--output", type=Path, default=Path("dist/self-study"))
    _ = parser.add_argument("--kit-only", action="store_true", help="Skip PDF rendering")
    arguments = parser.parse_args()
    output = cast("Path", arguments.output)
    kit_only = cast("bool", arguments.kit_only)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".self-study-", dir=output) as temporary_name:
        staging = Path(temporary_name)
        kit = staging / "linux-foundations-practice.zip"
        write_practice_kit(kit)
        if not kit_only:
            pandoc = shutil.which("pandoc")
            if pandoc is None:
                raise FileNotFoundError("PDF export requires pandoc and xelatex")
            header = staging / "header.tex"
            header.write_text(_PDF_HEADER, encoding="utf-8")
            documents = set(_documents())
            for document in sorted(documents):
                relative = document.relative_to(_COURSE).with_suffix(".pdf")
                destination = staging / "pdfs" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                contents = document.name in {
                    "self-study.md",
                    "continue-at-home.md",
                    "self-study-answers.md",
                }
                subprocess.run(  # noqa: S603 - fixed renderer, public source, no shell
                    [
                        pandoc,
                        "--from=markdown",
                        "--pdf-engine=xelatex",
                        "--standalone",
                        *(["--toc"] if contents else []),
                        "--toc-depth=2",
                        "--variable=mainfont:DejaVu Sans",
                        "--variable=monofont:DejaVu Sans Mono",
                        "--variable=geometry:margin=22mm",
                        "--variable=fontsize:11pt",
                        f"--include-in-header={header}",
                        f"--output={destination}",
                    ],
                    input=_pdf_markdown(document, documents),
                    text=True,
                    check=True,
                )
            resource = staging / "pdfs/guides/resources/today.sh"
            resource.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_COURSE / "guides/resources/today.sh", resource)
            (staging / "pdfs/START-HERE.txt").write_text(
                dedent("""\
                    Start with guides/continue-at-home.pdf.
                    Session guides: sessions/S01/self-study.pdf through sessions/S10/self-study.pdf.
                    Answers: guides/self-study-answers.pdf.
                    Reference indexes: commands/README.pdf and concepts/README.pdf.
                    Keep these directories together so cross-document PDF links remain usable.
                    """),
                encoding="utf-8",
            )
            with ZipFile(staging / "linux-foundations-pdfs.zip", "w", ZIP_DEFLATED) as archive:
                for path in sorted((staging / "pdfs").rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(staging / "pdfs"))
            shutil.copy2(staging / "linux-foundations-pdfs.zip", output)
        shutil.copy2(kit, output)
    _ = sys.stdout.write(f"Self-study files written to {output}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build a ttyd index that loads Salt-managed web fonts."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path


class BuildIndexError(RuntimeError):
    """Raised when the ttyd index cannot be built."""


def inject_stylesheet_link(document: str, stylesheet_path: str) -> str:
    """Insert a stylesheet link into a generated ttyd document."""
    link_element = f'<link rel="stylesheet" type="text/css" href="{stylesheet_path}">'
    if link_element in document:
        return document
    if "</head>" not in document:
        raise BuildIndexError("Generated ttyd index has no closing head tag")
    return document.replace("</head>", f"{link_element}</head>", 1)


def inject_favicon_link(document: str, favicon_path: str) -> str:
    """Replace ttyd's generated favicon with a Salt-managed favicon."""
    link_element = f'<link rel="icon" type="image/svg+xml" href="{favicon_path}">'
    if link_element in document:
        return document
    icon_start = document.find('<link rel="icon"')
    if icon_start == -1:
        if "</head>" not in document:
            raise BuildIndexError("Generated ttyd index has no closing head tag")
        return document.replace("</head>", f"{link_element}</head>", 1)
    icon_end = document.find(">", icon_start)
    if icon_end == -1:
        raise BuildIndexError("Generated ttyd index has malformed favicon tag")
    return document[:icon_start] + link_element + document[icon_end + 1 :]


def wrap_startup_script(document: str, font_family: str) -> str:
    """Patch ttyd startup behavior before its application code runs."""
    marker = "Could not load ttyd web font before startup"
    if marker in document:
        return document
    script_open = '<script type="text/javascript">'
    script_close = "</script>"
    before_script, script_separator, script_and_after = document.partition(script_open)
    if not script_separator:
        raise BuildIndexError("Generated ttyd index has no startup script")
    script, close_separator, after_script = script_and_after.rpartition(script_close)
    if not close_separator:
        raise BuildIndexError("Generated ttyd index has no closing script tag")
    return (
        before_script
        + script_open
        + title_normalizer_prelude()
        + font_loading_prelude(font_family)
        + script
        + "\n})();"
        + script_close
        + after_script
    )


def title_normalizer_prelude() -> str:
    """Return JavaScript that keeps OSC terminal titles undecorated."""
    return """(() => {
    const titleDescriptor =
        Object.getOwnPropertyDescriptor(Document.prototype, "title") ||
        Object.getOwnPropertyDescriptor(HTMLDocument.prototype, "title");
    if (!titleDescriptor || !titleDescriptor.get || !titleDescriptor.set) {
        return;
    }
    const terminalTitlePattern = /^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+ \\| /;
    const normalizeTitle = (title) => {
        const stringTitle = String(title);
        if (!terminalTitlePattern.test(stringTitle)) {
            return stringTitle;
        }
        return stringTitle.split(" | ", 1)[0];
    };
    Object.defineProperty(document, "title", {
        configurable: true,
        enumerable: true,
        get() {
            return titleDescriptor.get.call(document);
        },
        set(title) {
            titleDescriptor.set.call(document, normalizeTitle(title));
        },
    });
})();
"""


def font_loading_prelude(font_family: str) -> str:
    """Return JavaScript that waits for the terminal web font."""
    return f"""(async () => {{
    try {{
        if (document.fonts) {{
            const fontFamily = {json.dumps(font_family)};
            const cssFontFamily = fontFamily.includes(" ")
                ? `"${{fontFamily}}"`
                : fontFamily;
            await Promise.all([
                document.fonts.load(`400 14px ${{cssFontFamily}}`),
                document.fonts.load(`700 14px ${{cssFontFamily}}`),
            ]);
            await document.fonts.ready;
        }}
    }} catch (error) {{
        console.warn("Could not load ttyd web font before startup", error);
    }}
"""


def fetch_ttyd_index(port: int, timeout_seconds: float) -> str:
    """Fetch the default index from a temporary ttyd listener."""
    deadline = time.monotonic() + timeout_seconds
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/",
                timeout=1,
            ) as response:
                return response.read().decode("utf-8")
        except OSError as error:
            last_error = error
            time.sleep(0.1)
    raise BuildIndexError(f"Could not fetch ttyd index: {last_error}")


def build_custom_index(
    *,
    output_path: Path,
    stylesheet_path: str,
    favicon_path: str,
    font_family: str,
    port: int,
    timeout_seconds: float,
) -> None:
    """Start ttyd briefly, fetch its index, inject CSS, and write output."""
    process = subprocess.Popen(
        [
            "/usr/local/bin/ttyd",
            "--interface",
            "127.0.0.1",
            "--port",
            str(port),
            "/bin/true",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if (
            output_path.write_text(
                inject_stylesheet_link(
                    inject_favicon_link(
                        wrap_startup_script(
                            fetch_ttyd_index(port, timeout_seconds),
                            font_family,
                        ),
                        favicon_path,
                    ),
                    stylesheet_path,
                ),
                encoding="utf-8",
            )
            == 0
        ):
            raise BuildIndexError("Generated ttyd index is empty")
        output_path.chmod(0o644)
    finally:
        process.terminate()
        try:
            if process.wait(timeout=2) == 127:
                raise BuildIndexError("Temporary ttyd process exited with status 127")
        except subprocess.TimeoutExpired:
            process.kill()
            if process.wait() == 127:
                raise BuildIndexError("Temporary ttyd process exited with status 127")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    if parser.add_argument("--output", required=True, type=Path).dest != "output":
        raise BuildIndexError("Could not configure output argument")
    if parser.add_argument("--stylesheet", required=True).dest != "stylesheet":
        raise BuildIndexError("Could not configure stylesheet argument")
    if parser.add_argument("--favicon", required=True).dest != "favicon":
        raise BuildIndexError("Could not configure favicon argument")
    if parser.add_argument("--font-family", required=True).dest != "font_family":
        raise BuildIndexError("Could not configure font family argument")
    if parser.add_argument("--port", required=True, type=int).dest != "port":
        raise BuildIndexError("Could not configure port argument")
    if (
        parser.add_argument("--timeout-seconds", default=5.0, type=float).dest
        != "timeout_seconds"
    ):
        raise BuildIndexError("Could not configure timeout argument")
    return parser.parse_args()


def main() -> None:
    """Build the custom index."""
    arguments = parse_arguments()
    build_custom_index(
        output_path=arguments.output,
        stylesheet_path=arguments.stylesheet,
        favicon_path=arguments.favicon,
        font_family=arguments.font_family,
        port=arguments.port,
        timeout_seconds=arguments.timeout_seconds,
    )


if __name__ == "__main__":
    main()

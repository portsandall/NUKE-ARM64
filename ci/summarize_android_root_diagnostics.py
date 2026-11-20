#!/usr/bin/env python3
"""Render a compact summary of the non-blocking KisakBlack Android build log."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+Z\s*")
_ROOT_EXIT = re.compile(r"ROOT_(CONFIGURE|BUILD)_EXIT=(\d+)")
_DIAGNOSTIC = re.compile(
    r"^(?P<location>\S+:\d+:\d+):\s*"
    r"(?P<kind>fatal error|error|warning):\s*(?P<message>.*)$"
)
_FAILED = re.compile(r"^FAILED:\s*(?:\[code=\d+\]\s*)?(?P<target>.+)$")


def _exit_status(value: int | None) -> str:
    if value is None:
        return "not recorded"
    return "PASS (exit 0)" if value == 0 else f"FAIL (exit {value})"


def render_summary(log_text: str) -> str:
    """Return a stable Markdown summary for a captured CMake/Ninja build log."""
    configure_exit: int | None = None
    build_exit: int | None = None
    errors: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []
    failed_targets: list[str] = []

    for raw_line in log_text.splitlines():
        line = _TIMESTAMP.sub("", _ANSI.sub("", raw_line)).strip()
        root_match = _ROOT_EXIT.search(line)
        if root_match:
            value = int(root_match.group(2))
            if root_match.group(1) == "CONFIGURE":
                configure_exit = value
            else:
                build_exit = value
            continue

        failed_match = _FAILED.match(line)
        if failed_match:
            target = failed_match.group("target").strip()
            if target not in failed_targets:
                failed_targets.append(target)

        diagnostic = _DIAGNOSTIC.match(line)
        if not diagnostic:
            continue
        item = (
            diagnostic.group("location"),
            diagnostic.group("message").strip(),
        )
        target_list = warnings if diagnostic.group("kind") == "warning" else errors
        if item not in target_list:
            target_list.append(item)

    output = [
        "# KisakBlack Android root-build diagnostic",
        "",
        f"- CMake configure: **{_exit_status(configure_exit)}**",
        f"- Full KisakBlack target build: **{_exit_status(build_exit)}**",
        f"- Compiler errors: **{len(errors)}**",
        f"- Compiler warnings: **{len(warnings)}**",
    ]

    if failed_targets:
        output.extend(["", "## Failed build targets", ""])
        output.extend(f"- `{target}`" for target in failed_targets)

    if errors:
        output.extend(["", "## Compiler errors", ""])
        output.extend(
            f"- `{location}` — {message}" for location, message in errors
        )
    elif build_exit == 0:
        output.extend(["", "No compiler errors were reported."])
    else:
        output.extend(["", "No compiler error lines were parsed from the log."])

    output.extend(
        [
            "",
            "> This report summarizes the diagnostic log. A successful workflow",
            "> does not imply a successful full-engine build when that build step",
            "> is explicitly non-blocking.",
            "",
        ]
    )
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="captured root-build log")
    parser.add_argument("output", type=Path, help="Markdown summary destination")
    args = parser.parse_args()

    try:
        log_text = args.input.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"cannot read diagnostic log: {exc}", file=sys.stderr)
        return 2

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_summary(log_text), encoding="utf-8")
    except OSError as exc:
        print(f"cannot write diagnostic summary: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

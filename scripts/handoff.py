#!/usr/bin/env python3
"""Utilities for the session-handoff Codex skill."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_HANDOFF = "SESSION_HANDOFF.md"
DEFAULT_ARCHIVE_DIR = ".codex/handoffs"
REQUIRED_HEADINGS = [
    "# Session Handoff",
    "## Current Goal",
    "## Completed",
    "## Current State",
    "## Key Files",
    "## Decisions",
    "## Verification",
    "## Open Questions",
    "## Next Steps",
    "## Next Session Opening Message",
    "### Read Only",
    "### Continue",
    "## Notes For Next Session",
]
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|bearer)\b\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[opsru]_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[a-z]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bya29\.[A-Za-z0-9_\-.]{20,}"),
    re.compile(r"(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(cookie|set-cookie)\b\s*[:=]"),
]


def resolve_root(root: str) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"Root does not exist or is not a directory: {path}")
    return path


def handoff_path(root: Path, handoff: str) -> Path:
    path = Path(handoff)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def archive_path(root: Path, archive_dir: str) -> Path:
    path = Path(archive_dir)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def git_branch(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "unknown"
    branch = result.stdout.strip()
    return branch or "unknown"


def cmd_status(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    path = handoff_path(root, args.handoff)
    print(f"Root: {root}")
    print(f"Handoff: {path}")
    print(f"Branch: {git_branch(root)}")
    if path.exists():
        stat = path.stat()
        updated = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        print(f"Exists: yes")
        print(f"Size: {stat.st_size} bytes")
        print(f"Modified: {updated}")
    else:
        print("Exists: no")
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    source = handoff_path(root, args.handoff)
    if not source.exists():
        print(f"No handoff to archive: {source}")
        return 0

    dest_dir = archive_path(root, args.archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = dest_dir / f"{stamp}-{source.name}"
    shutil.copy2(source, dest)
    print(f"Archived {source} -> {dest}")
    return 0


def template_text(root: Path) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# Session Handoff

Updated: {now} local time
Project: {root.name}
Branch: {git_branch(root)}

## Current Goal
- None

## Completed
- None

## Current State
- None

## Key Files
- None

## Decisions
- None

## Verification
- None

## Open Questions
- None

## Next Steps
- None

## Next Session Opening Message

### Read Only
```text
Use session-handoff to read SESSION_HANDOFF.md in read-only mode. Do not modify files or run mutating commands. Restate the current goal, current state, risks/blockers, verification status, and recommended next action.
```

### Continue
```text
Use session-handoff to read SESSION_HANDOFF.md, verify local state, then continue from Next Steps. Before changing files, briefly restate the current goal and planned first action.
```

## Notes For Next Session
- None
"""


def cmd_template(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    text = template_text(root)
    if args.write:
        path = handoff_path(root, args.handoff)
        if path.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite existing handoff without --force: {path}")
        path.write_text(text, encoding="utf-8")
        print(f"Wrote template: {path}")
    else:
        print(text, end="")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    path = handoff_path(root, args.handoff)
    if not path.exists():
        print(f"Missing handoff: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            problems.append(f"Missing required heading: {heading}")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            problems.append(f"Possible secret matched pattern: {pattern.pattern}")

    line_count = text.count("\n") + 1
    if line_count > args.max_lines:
        problems.append(f"Handoff is long: {line_count} lines > {args.max_lines}")

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 2

    print(f"OK: {path}")
    return 0


def add_common_options(parser: argparse.ArgumentParser, *, defaults: bool) -> None:
    root_default = "." if defaults else argparse.SUPPRESS
    handoff_default = DEFAULT_HANDOFF if defaults else argparse.SUPPRESS
    parser.add_argument("--root", default=root_default, help="Project root. Defaults to current directory.")
    parser.add_argument("--handoff", default=handoff_default, help=f"Handoff file. Defaults to {DEFAULT_HANDOFF}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Session handoff helper")
    add_common_options(parser, defaults=True)
    common_after_command = argparse.ArgumentParser(add_help=False)
    add_common_options(common_after_command, defaults=False)

    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", parents=[common_after_command], help="Show handoff status")
    status.set_defaults(func=cmd_status)

    archive = subparsers.add_parser("archive", parents=[common_after_command], help="Archive the current handoff if it exists")
    archive.add_argument("--archive-dir", default=DEFAULT_ARCHIVE_DIR, help=f"Archive directory. Defaults to {DEFAULT_ARCHIVE_DIR}.")
    archive.set_defaults(func=cmd_archive)

    template = subparsers.add_parser("template", parents=[common_after_command], help="Print or write an empty handoff template")
    template.add_argument("--write", action="store_true", help="Write the template to the handoff file")
    template.add_argument("--force", action="store_true", help="Allow overwriting when used with --write")
    template.set_defaults(func=cmd_template)

    check = subparsers.add_parser("check", parents=[common_after_command], help="Validate required sections and scan for likely secrets")
    check.add_argument("--max-lines", type=int, default=150, help="Warn if the handoff exceeds this many lines")
    check.set_defaults(func=cmd_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

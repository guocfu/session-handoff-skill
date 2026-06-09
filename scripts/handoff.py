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
from typing import Optional


DEFAULT_HANDOFF = "SESSION_HANDOFF.md"
DEFAULT_ARCHIVE_DIR = ".codex/handoffs"
DEFAULT_ARCHIVE_KEEP = 20
REQUIRED_HEADINGS = [
    "# Session Handoff",
    "## Current Goal",
    "## Completed",
    "## Current State",
    "## Workspace Identity",
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
CONTENT_REQUIRED_HEADINGS = [
    "## Current Goal",
    "## Current State",
    "## Workspace Identity",
]
INCOMPLETE_VALUES = {"", "-", "none", "n/a", "na", "unknown", "tbd", "todo", "null"}
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
PLACEHOLDER_PATTERN = re.compile(r"<[^>\n]{1,80}>")


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


def non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected a non-negative integer: {value}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"Expected a non-negative integer: {value}")
    return parsed


def run_git(root: Path, args: list[str]) -> Optional[subprocess.CompletedProcess[str]]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None


def git_branch(root: Path) -> str:
    commands = [["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]]
    for command in commands:
        result = run_git(root, command)
        if result is None:
            continue

        branch = result.stdout.strip()
        if result.returncode == 0 and branch and branch != "HEAD":
            return branch

    return "unknown"


def git_head(root: Path) -> str:
    result = run_git(root, ["rev-parse", "HEAD"])
    if result is None or result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def git_root_name(root: Path) -> str:
    result = run_git(root, ["rev-parse", "--show-toplevel"])
    if result is None or result.returncode != 0:
        return "unknown"
    git_root = result.stdout.strip()
    return Path(git_root).name if git_root else "unknown"


def dirty_files_summary(root: Path) -> str:
    result = run_git(root, ["status", "--short"])
    if result is None or result.returncode != 0:
        return "unknown"
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return "None"
    shown = ", ".join(lines[:8])
    if len(lines) > 8:
        return f"{len(lines)} changed files; first entries: {shown}"
    return shown


def workspace_identity_text(root: Path) -> str:
    return f"""## Workspace Identity
- Project name: {root.name}
- Git root name: {git_root_name(root)}
- Relative path: .
- Branch: {git_branch(root)}
- HEAD: {git_head(root)}
- Local root observed at save time: {root}
- Dirty files: {dirty_files_summary(root)}"""


def unique_archive_dest(dest_dir: Path, stamp: str, source_name: str) -> Path:
    for sequence in range(10000):
        dest = dest_dir / f"{stamp}-{sequence:04d}-{source_name}"
        if not dest.exists():
            return dest
    raise SystemExit(f"Could not create a unique archive name in: {dest_dir}")


def current_archive_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def prune_archives(dest_dir: Path, source_name: str, keep: int) -> int:
    if keep == 0:
        return 0

    suffix = f"-{source_name}"
    archives = sorted(
        (path for path in dest_dir.iterdir() if path.is_file() and path.name.endswith(suffix)),
        key=lambda path: path.name,
    )
    stale = archives[:-keep]
    for path in stale:
        path.unlink()
    return len(stale)


def cmd_status(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    path = handoff_path(root, args.handoff)
    print(f"Root: {root}")
    print(f"Handoff: {path}")
    print(f"Branch: {git_branch(root)}")
    print(f"HEAD: {git_head(root)}")
    if path.exists():
        stat = path.stat()
        updated = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        print("Exists: yes")
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
    dest = unique_archive_dest(dest_dir, current_archive_stamp(), source.name)
    shutil.copy2(source, dest)
    print(f"Archived {source} -> {dest}")
    pruned = prune_archives(dest_dir, source.name, args.keep)
    if pruned:
        print(f"Pruned {pruned} archived handoff(s), keeping the latest {args.keep}")
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

{workspace_identity_text(root)}

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

    placeholders = sorted(set(match.group(0) for match in PLACEHOLDER_PATTERN.finditer(text)))
    for placeholder in placeholders:
        problems.append(f"Unresolved template placeholder: {placeholder}")

    for heading in CONTENT_REQUIRED_HEADINGS:
        section = section_text(text, heading)
        if section is not None and section_is_incomplete(section):
            problems.append(f"Section appears incomplete: {heading}")

    next_steps = section_text(text, "## Next Steps")
    if next_steps is not None and section_is_incomplete(next_steps):
        problems.append("Next Steps must describe a real next action, or explain that the task is complete.")

    verification = section_text(text, "## Verification")
    if verification is not None and section_is_incomplete(verification):
        problems.append("Verification must record checks run, or checks skipped with a reason.")

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


def section_text(text: str, heading: str) -> Optional[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return None

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def section_is_incomplete(section: str) -> bool:
    content_lines = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        if stripped.startswith("-"):
            stripped = stripped[1:].strip()
        content_lines.append(stripped)

    if not content_lines:
        return True

    normalized = " ".join(content_lines).strip().lower()
    return normalized in INCOMPLETE_VALUES


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
    archive.add_argument(
        "--keep",
        type=non_negative_int,
        default=DEFAULT_ARCHIVE_KEEP,
        help=f"Archived handoffs to keep for this handoff file. Use 0 to disable cleanup. Defaults to {DEFAULT_ARCHIVE_KEEP}.",
    )
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

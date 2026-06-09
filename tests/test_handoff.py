from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handoff.py"
SPEC = importlib.util.spec_from_file_location("handoff", SCRIPT)
assert SPEC is not None
handoff = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(handoff)


class HandoffCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def run_handoff(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_status_reports_missing_handoff(self) -> None:
        result = self.run_handoff("status", "--root", str(self.root))

        self.assertEqual(result.returncode, 0)
        self.assertIn("Exists: no", result.stdout)
        self.assertIn("Handoff:", result.stdout)

    def test_template_write_creates_valid_handoff(self) -> None:
        write = self.run_handoff("template", "--root", str(self.root), "--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        handoff = self.root / "SESSION_HANDOFF.md"
        self.assertTrue(handoff.exists())
        self.assertIn("## Next Session Opening Message", handoff.read_text(encoding="utf-8"))

        check = self.run_handoff("check", "--root", str(self.root))
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("OK:", check.stdout)

    def test_template_write_requires_force_to_overwrite(self) -> None:
        first = self.run_handoff("template", "--root", str(self.root), "--write")
        self.assertEqual(first.returncode, 0, first.stderr)

        second = self.run_handoff("template", "--root", str(self.root), "--write")
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("Refusing to overwrite existing handoff without --force", second.stderr)

        forced = self.run_handoff("template", "--root", str(self.root), "--write", "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)

    def test_check_reports_missing_file_and_invalid_content(self) -> None:
        missing = self.run_handoff("check", "--root", str(self.root))
        self.assertEqual(missing.returncode, 1)
        self.assertIn("Missing handoff:", missing.stderr)

        (self.root / "SESSION_HANDOFF.md").write_text(
            "# Session Handoff\n\napi_key = sk-test01234567890123456789\n",
            encoding="utf-8",
        )
        invalid = self.run_handoff("check", "--root", str(self.root))

        self.assertEqual(invalid.returncode, 2)
        self.assertIn("Missing required heading: ## Current Goal", invalid.stderr)
        self.assertIn("Possible secret matched pattern:", invalid.stderr)

    def test_check_reports_max_lines_problem(self) -> None:
        write = self.run_handoff("template", "--root", str(self.root), "--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        result = self.run_handoff("check", "--root", str(self.root), "--max-lines", "1")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Handoff is long:", result.stderr)

    def test_archive_keeps_latest_handoffs(self) -> None:
        handoff = self.root / "SESSION_HANDOFF.md"

        for index in range(3):
            handoff.write_text(f"# Session Handoff\n\nversion {index}\n", encoding="utf-8")
            result = self.run_handoff("archive", "--root", str(self.root), "--keep", "2")
            self.assertEqual(result.returncode, 0, result.stderr)

        archive_dir = self.root / ".codex" / "handoffs"
        archives = sorted(archive_dir.glob("*-SESSION_HANDOFF.md"))

        self.assertEqual(len(archives), 2)
        self.assertIn("version 1", archives[0].read_text(encoding="utf-8"))
        self.assertIn("version 2", archives[1].read_text(encoding="utf-8"))

    def test_archive_keep_zero_disables_cleanup(self) -> None:
        handoff = self.root / "SESSION_HANDOFF.md"

        for index in range(3):
            handoff.write_text(f"# Session Handoff\n\nversion {index}\n", encoding="utf-8")
            result = self.run_handoff("archive", "--root", str(self.root), "--keep", "0")
            self.assertEqual(result.returncode, 0, result.stderr)

        archives = sorted((self.root / ".codex" / "handoffs").glob("*-SESSION_HANDOFF.md"))
        self.assertEqual(len(archives), 3)

    def test_archive_supports_custom_handoff_and_archive_dir(self) -> None:
        custom = self.root / "CUSTOM_HANDOFF.md"
        custom.write_text("# Session Handoff\n\ncustom\n", encoding="utf-8")

        result = self.run_handoff(
            "archive",
            "--root",
            str(self.root),
            "--handoff",
            "CUSTOM_HANDOFF.md",
            "--archive-dir",
            "saved-handoffs",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        archives = sorted((self.root / "saved-handoffs").glob("*-CUSTOM_HANDOFF.md"))
        self.assertEqual(len(archives), 1)
        self.assertIn("custom", archives[0].read_text(encoding="utf-8"))

    def test_archive_rejects_negative_keep(self) -> None:
        result = self.run_handoff("archive", "--root", str(self.root), "--keep", "-1")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Expected a non-negative integer", result.stderr)

    def test_unique_archive_dest_increments_sequence_on_collision(self) -> None:
        archive_dir = self.root / ".codex" / "handoffs"
        archive_dir.mkdir(parents=True)
        stamp = "20260609-120000-000001"

        first = handoff.unique_archive_dest(archive_dir, stamp, "SESSION_HANDOFF.md")
        first.write_text("first", encoding="utf-8")
        second = handoff.unique_archive_dest(archive_dir, stamp, "SESSION_HANDOFF.md")

        self.assertEqual(first.name, f"{stamp}-0000-SESSION_HANDOFF.md")
        self.assertEqual(second.name, f"{stamp}-0001-SESSION_HANDOFF.md")

    def test_git_branch_falls_back_to_rev_parse(self) -> None:
        responses = [
            subprocess.CompletedProcess(["git", "branch", "--show-current"], 0, "", ""),
            subprocess.CompletedProcess(["git", "rev-parse", "--abbrev-ref", "HEAD"], 0, "feature/fallback\n", ""),
        ]

        with mock.patch.object(handoff.subprocess, "run", side_effect=responses):
            branch = handoff.git_branch(self.root)

        self.assertEqual(branch, "feature/fallback")

    def test_git_branch_returns_unknown_when_commands_fail(self) -> None:
        responses = [
            FileNotFoundError("git"),
            subprocess.CompletedProcess(["git", "rev-parse", "--abbrev-ref", "HEAD"], 0, "HEAD\n", ""),
        ]

        with mock.patch.object(handoff.subprocess, "run", side_effect=responses):
            branch = handoff.git_branch(self.root)

        self.assertEqual(branch, "unknown")


if __name__ == "__main__":
    unittest.main()

"""Tests for the state-file validator (Seam 1: text in, violations out).

The validator is exercised as a standalone script — stdin in, exit code and
violation list out — because that is exactly how CI and the orchestrator will
call it.
"""

import subprocess
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parent.parent / "bin" / "validate-state-file"

WELL_FORMED = """\
# Workflow: Disciplined Build — auth magic link

Started: 2026-06-10 by casper
Last updated: 2026-06-10

| # | Step | Status | Artifact |
|---|------|--------|----------|
| 1 | Grill the idea     | done        | docs/grill-auth-magic-link.md |
| 2 | Produce PRD        | done        | docs/prd-auth-magic-link.md |
| 3 | Break into issues  | done        | #41, #42, #43 |
| 4 | Implement slice    | in progress | branch `feat/auth-magic-link` |
| 5 | Review + verify    | todo        | - |

## Notes
Nothing skipped.
"""


def run_validator(text):
    return subprocess.run(
        [str(VALIDATOR), "-"],
        input=text,
        capture_output=True,
        text=True,
    )


class TestWellFormed(unittest.TestCase):
    def test_well_formed_file_passes(self):
        result = run_validator(WELL_FORMED)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)


class TestDoneWithoutArtifact(unittest.TestCase):
    def test_done_with_dash_artifact_is_violation(self):
        text = WELL_FORMED.replace(
            "| 5 | Review + verify    | todo        | - |",
            "| 5 | Review + verify    | done        | - |",
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 5", result.stdout)
        self.assertIn("done", result.stdout)
        self.assertIn("artifact", result.stdout)

    def test_done_with_empty_artifact_is_violation(self):
        text = WELL_FORMED.replace(
            "| 5 | Review + verify    | todo        | - |",
            "| 5 | Review + verify    | done        |  |",
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 5", result.stdout)


class TestInvalidStatus(unittest.TestCase):
    def test_unknown_status_is_violation(self):
        text = WELL_FORMED.replace(
            "| 4 | Implement slice    | in progress | branch `feat/auth-magic-link` |",
            "| 4 | Implement slice    | almost done | branch `feat/auth-magic-link` |",
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 4", result.stdout)
        self.assertIn("invalid status", result.stdout)
        self.assertIn("almost done", result.stdout)


class TestSkippedWithoutReason(unittest.TestCase):
    SKIPPED_ROW = "| 1 | Grill the idea     | skipped     | - |"
    DONE_ROW = "| 1 | Grill the idea     | done        | docs/grill-auth-magic-link.md |"

    def test_skipped_with_empty_notes_is_violation(self):
        text = WELL_FORMED.replace(self.DONE_ROW, self.SKIPPED_ROW).replace(
            "Nothing skipped.", ""
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 1", result.stdout)
        self.assertIn("skipped", result.stdout)
        self.assertIn("Notes", result.stdout)

    def test_skipped_with_template_placeholder_notes_is_violation(self):
        text = WELL_FORMED.replace(self.DONE_ROW, self.SKIPPED_ROW).replace(
            "Nothing skipped.", "<anything skipped, and why — recorded honestly>"
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 1", result.stdout)

    def test_skipped_with_reason_passes(self):
        text = WELL_FORMED.replace(self.DONE_ROW, self.SKIPPED_ROW).replace(
            "Nothing skipped.",
            "Skipped grilling: one-line config change, design space is trivial.",
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 0, result.stdout)


class TestMissingSections(unittest.TestCase):
    def test_missing_header_is_violation(self):
        text = WELL_FORMED.replace(
            "# Workflow: Disciplined Build — auth magic link\n", ""
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("# Workflow:", result.stdout)

    def test_missing_started_field_is_violation(self):
        text = WELL_FORMED.replace("Started: 2026-06-10 by casper\n", "")
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Started:", result.stdout)

    def test_missing_last_updated_field_is_violation(self):
        text = WELL_FORMED.replace("Last updated: 2026-06-10\n", "")
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Last updated:", result.stdout)

    def test_missing_step_table_is_violation(self):
        lines = [l for l in WELL_FORMED.splitlines() if not l.startswith("|")]
        result = run_validator("\n".join(lines) + "\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("step table", result.stdout)

    def test_missing_notes_section_is_violation(self):
        text = WELL_FORMED.replace("## Notes\nNothing skipped.\n", "")
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("## Notes", result.stdout)


class TestMultipleViolations(unittest.TestCase):
    def test_all_violations_are_reported_not_just_the_first(self):
        text = WELL_FORMED.replace(
            "| 5 | Review + verify    | todo        | - |",
            "| 5 | Review + verify    | done        | - |",
        ).replace(
            "| 4 | Implement slice    | in progress | branch `feat/auth-magic-link` |",
            "| 4 | Implement slice    | wip         | branch `feat/auth-magic-link` |",
        )
        result = run_validator(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("step 4", result.stdout)
        self.assertIn("step 5", result.stdout)


class TestFileInput(unittest.TestCase):
    def test_reads_from_file_path(self):
        import tempfile

        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False
        ) as f:
            f.write(WELL_FORMED)
            path = f.name
        result = subprocess.run(
            [str(VALIDATOR), path], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()

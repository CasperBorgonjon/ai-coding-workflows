"""Drift test: the manifest is the source of truth for the workflow's steps;
the prose table in SKILL.md is hand-written and must agree with it on step
numbers, names, checkpoint types, and skill names. This test fails on any
divergence, so the two can never silently drift apart.
"""

import json
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "disciplined-build"
MANIFEST = SKILL_DIR / "manifest.json"
SKILL_MD = SKILL_DIR / "SKILL.md"

VALID_CHECKPOINTS = {"hard", "soft"}


def manifest_steps():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        {
            "step": s["step"],
            "name": s["name"],
            "checkpoint": s["checkpoint"],
            "skills": [skill["name"] for skill in s["skills"]],
        }
        for s in data["steps"]
    ]


WORKFLOW_TABLE_HEADER = re.compile(
    r"^\|\s*#\s*\|\s*Step\s*\|\s*Skill\s*\|\s*Checkpoint\s*\|\s*$", re.I
)


def skill_md_steps():
    """Parse the workflow table (the one headed # | Step | Skill | Checkpoint)
    out of SKILL.md prose. The state-file schema example is a different table
    and must not be picked up."""
    steps = []
    in_table = False
    for line in SKILL_MD.read_text(encoding="utf-8").splitlines():
        if not in_table:
            in_table = bool(WORKFLOW_TABLE_HEADER.match(line))
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|\s*$", line)
        if not m:
            if not re.match(r"^\|[\s\-:|]+\|\s*$", line):
                break
            continue
        steps.append(
            {
                "step": int(m.group(1)),
                "name": m.group(2).strip(),
                "checkpoint": "hard" if "HARD" in m.group(4) else "soft",
                "skills": re.findall(r"`([^`]+)`", m.group(3)),
            }
        )
    return steps


class TestManifestSkillMdSync(unittest.TestCase):
    def test_same_steps_in_same_order(self):
        manifest = manifest_steps()
        prose = skill_md_steps()
        self.assertEqual(
            [(s["step"], s["name"]) for s in manifest],
            [(s["step"], s["name"]) for s in prose],
            "manifest.json and the SKILL.md table disagree on steps "
            "(manifest is the source of truth — update SKILL.md)",
        )

    def test_same_checkpoint_types(self):
        for m, p in zip(manifest_steps(), skill_md_steps()):
            self.assertEqual(
                m["checkpoint"],
                p["checkpoint"],
                f"step {m['step']} ({m['name']}): checkpoint differs "
                "between manifest.json and SKILL.md",
            )

    def test_same_skills_per_step(self):
        for m, p in zip(manifest_steps(), skill_md_steps()):
            self.assertEqual(
                m["skills"],
                p["skills"],
                f"step {m['step']} ({m['name']}): skills differ "
                "between manifest.json and SKILL.md",
            )


class TestManifestWellFormed(unittest.TestCase):
    def test_five_consecutively_numbered_steps(self):
        self.assertEqual([s["step"] for s in manifest_steps()], [1, 2, 3, 4, 5])

    def test_checkpoints_are_hard_or_soft(self):
        for s in manifest_steps():
            self.assertIn(s["checkpoint"], VALID_CHECKPOINTS)

    def test_every_skill_fully_pinned(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for step in data["steps"]:
            for skill in step["skills"]:
                for field in ("name", "source", "path", "ref"):
                    self.assertTrue(
                        skill.get(field),
                        f"step {step['step']}: skill missing '{field}'",
                    )
                self.assertRegex(
                    skill["ref"],
                    r"^[0-9a-f]{40}$",
                    f"skill '{skill['name']}': ref must be a full commit SHA "
                    "(upstream has no tags; 'main' is not a pin)",
                )

    def test_every_crosscutting_skill_fully_pinned(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for skill in data.get("crossCutting", []):
            for field in ("name", "source", "path", "ref"):
                self.assertTrue(
                    skill.get(field),
                    f"cross-cutting skill missing '{field}'",
                )
            self.assertRegex(
                skill["ref"],
                r"^[0-9a-f]{40}$",
                f"cross-cutting skill '{skill['name']}': ref must be a full "
                "commit SHA (upstream has no tags; 'main' is not a pin)",
            )


if __name__ == "__main__":
    unittest.main()

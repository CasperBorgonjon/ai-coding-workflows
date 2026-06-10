"""Integration tests for install.sh (Seam 4).

Runs the real installer into a temp dir with a fake HOME and asserts the
orchestrator and every manifest-declared skill land at the expected paths,
at the pinned refs. Needs network access to clone the manifest's sources
(public repos, no credentials); set DW_SKIP_NETWORK_TESTS=1 to skip those.

The unreachable-source test is fully offline.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "install.sh"
MANIFEST = ROOT / "skills" / "disciplined-build" / "manifest.json"

SKIP_NETWORK = os.environ.get("DW_SKIP_NETWORK_TESTS") == "1"


def manifest_skills():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    skills = {}
    for step in data["steps"]:
        for s in step["skills"]:
            skills[s["name"]] = s
    return skills


def run_install(args=(), home=None, cwd=None):
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = str(home)
    return subprocess.run(
        [str(INSTALL), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd or ROOT,
    )


def assert_full_install(testcase, skills_dir):
    testcase.assertTrue(
        (skills_dir / "disciplined-build" / "SKILL.md").is_file(),
        "orchestrator not installed",
    )
    testcase.assertTrue(
        (skills_dir / "disciplined-build" / "manifest.json").is_file(),
        "manifest not installed alongside orchestrator",
    )
    for name, skill in manifest_skills().items():
        skill_md = skills_dir / name / "SKILL.md"
        testcase.assertTrue(skill_md.is_file(), f"skill '{name}' not installed")
        pinned = skills_dir / name / ".pinned-ref"
        testcase.assertTrue(pinned.is_file(), f"skill '{name}' has no .pinned-ref")
        testcase.assertEqual(
            pinned.read_text().strip(),
            skill["ref"],
            f"skill '{name}' not at the manifest's pinned ref",
        )


@unittest.skipIf(SKIP_NETWORK, "DW_SKIP_NETWORK_TESTS=1")
class TestGlobalInstall(unittest.TestCase):
    """One real global install (fake HOME), asserted from several angles."""

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp(prefix="dw-home-"))
        cls.first = run_install(home=cls.home)
        cls.second = run_install(home=cls.home)  # idempotency

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def test_install_succeeds(self):
        self.assertEqual(self.first.returncode, 0, self.first.stderr)

    def test_all_manifest_skills_at_pinned_refs(self):
        assert_full_install(self, self.home / ".claude" / "skills")

    def test_rerun_is_idempotent(self):
        self.assertEqual(self.second.returncode, 0, self.second.stderr)
        assert_full_install(self, self.home / ".claude" / "skills")


@unittest.skipIf(SKIP_NETWORK, "DW_SKIP_NETWORK_TESTS=1")
class TestProjectInstall(unittest.TestCase):
    def test_project_mode_installs_into_cwd(self):
        with tempfile.TemporaryDirectory(prefix="dw-proj-") as proj, \
                tempfile.TemporaryDirectory(prefix="dw-home-") as home:
            result = run_install(["--project"], home=home, cwd=proj)
            self.assertEqual(result.returncode, 0, result.stderr)
            assert_full_install(self, Path(proj) / ".claude" / "skills")
            self.assertFalse(
                (Path(home) / ".claude" / "skills").exists(),
                "--project mode must not touch HOME",
            )


class TestUnreachableSource(unittest.TestCase):
    """Offline: a doctored manifest with a dead source must fail loudly."""

    def test_dead_source_exits_nonzero_with_clear_error(self):
        with tempfile.TemporaryDirectory(prefix="dw-copy-") as tmp, \
                tempfile.TemporaryDirectory(prefix="dw-home-") as home:
            tmp = Path(tmp)
            shutil.copy(INSTALL, tmp / "install.sh")
            shutil.copytree(ROOT / "skills", tmp / "skills")
            manifest_path = tmp / "skills" / "disciplined-build" / "manifest.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for step in data["steps"]:
                for s in step["skills"]:
                    s["source"] = "/nonexistent/dead-repo.git"
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            env = dict(os.environ, HOME=str(home))
            result = subprocess.run(
                [str(tmp / "install.sh")],
                capture_output=True,
                text=True,
                env=env,
                cwd=tmp,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot fetch", result.stderr)
            self.assertIn("/nonexistent/dead-repo.git", result.stderr)


if __name__ == "__main__":
    unittest.main()

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


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def make_repo(tmp, files):
    """Create a one-commit git repo at tmp containing `files` ({relpath: text});
    return (repo_path, commit_sha)."""
    repo = Path(tmp)
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "fixture"], repo)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    return repo, sha


def doctored_install(tmp, shared_context=None):
    """Copy install.sh + skills into tmp, empty every step's skill list (so the
    install is fully offline), and optionally inject a top-level sharedContext
    block. Return the path to the copied install.sh."""
    tmp = Path(tmp)
    shutil.copy(INSTALL, tmp / "install.sh")
    (tmp / "install.sh").chmod(0o755)
    shutil.copytree(ROOT / "skills", tmp / "skills")
    mpath = tmp / "skills" / "disciplined-build" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    for step in data["steps"]:
        step["skills"] = []
    if shared_context is not None:
        data["sharedContext"] = shared_context
    mpath.write_text(json.dumps(data), encoding="utf-8")
    return tmp / "install.sh"


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


@unittest.skipIf(SKIP_NETWORK, "DW_SKIP_NETWORK_TESTS=1")
class TestBootstrap(unittest.TestCase):
    """bootstrap.sh clones the repo itself, then defers to install.sh.

    DW_REPO points the clone at this local repo, so the test exercises the
    committed state without depending on what's pushed to GitHub.
    """

    def test_bootstrap_installs_without_a_local_clone(self):
        with tempfile.TemporaryDirectory(prefix="dw-home-") as home, \
                tempfile.TemporaryDirectory(prefix="dw-cwd-") as cwd:
            env = dict(os.environ, HOME=home, DW_REPO=str(ROOT))
            result = subprocess.run(
                ["bash", str(ROOT / "bootstrap.sh")],
                capture_output=True,
                text=True,
                env=env,
                cwd=cwd,  # an empty dir: proves no pre-existing clone needed
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            assert_full_install(self, Path(home) / ".claude" / "skills")


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


class TestSharedContextSource(unittest.TestCase):
    """Offline: a manifest's optional sharedContext block is fetched, pinned,
    and landed at .workflow/shared/CONTEXT.md on a --project install. Uses a
    local fixture git repo, so no network — skill lists are emptied too."""

    GLOSSARY = "# Team Glossary\n\n**Order**: a customer's request to buy.\n"

    def _tmp(self, prefix):
        d = tempfile.mkdtemp(prefix=prefix)
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return Path(d)

    def _run(self, install_sh, project, cwd):
        return subprocess.run(
            [str(install_sh), *(["--project"] if project else [])],
            capture_output=True, text=True,
            env=dict(os.environ, HOME=str(self._tmp("dw-home-"))), cwd=cwd,
        )

    def test_project_install_lands_pinned_glossary(self):
        glossary, sha = make_repo(self._tmp("dw-glossary-"), {"CONTEXT.md": self.GLOSSARY})
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": ".", "ref": sha},
        )
        proj = self._tmp("dw-proj-")
        result = self._run(install, project=True, cwd=proj)
        self.assertEqual(result.returncode, 0, result.stderr)
        ctx = proj / ".workflow" / "shared" / "CONTEXT.md"
        self.assertTrue(ctx.is_file(), "shared CONTEXT.md not landed")
        self.assertEqual(ctx.read_text(encoding="utf-8"), self.GLOSSARY)
        self.assertEqual(
            (proj / ".workflow" / "shared" / ".pinned-ref").read_text().strip(),
            sha, "shared context not pinned to the manifest's ref",
        )

    def test_glossary_in_a_subdirectory(self):
        glossary, sha = make_repo(
            self._tmp("dw-glossary-"), {"vocab/CONTEXT.md": self.GLOSSARY}
        )
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": "vocab", "ref": sha},
        )
        proj = self._tmp("dw-proj-")
        result = self._run(install, project=True, cwd=proj)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (proj / ".workflow" / "shared" / "CONTEXT.md").read_text(encoding="utf-8"),
            self.GLOSSARY,
        )

    def test_no_shared_context_key_installs_unchanged(self):
        install = doctored_install(self._tmp("dw-tree-"), shared_context=None)
        proj = self._tmp("dw-proj-")
        result = self._run(install, project=True, cwd=proj)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(
            (proj / ".workflow").exists(),
            "no sharedContext key must not create .workflow/shared",
        )

    def test_global_install_skips_shared_context_cleanly(self):
        glossary, sha = make_repo(self._tmp("dw-glossary-"), {"CONTEXT.md": self.GLOSSARY})
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": ".", "ref": sha},
        )
        cwd = self._tmp("dw-cwd-")
        result = self._run(install, project=False, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(
            (cwd / ".workflow").exists(),
            "global install must not write a project .workflow/",
        )
        self.assertIn("skipped", result.stdout)

    def test_rerun_replaces_glossary_wholesale(self):
        glossary, sha = make_repo(self._tmp("dw-glossary-"), {"CONTEXT.md": self.GLOSSARY})
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": ".", "ref": sha},
        )
        proj = self._tmp("dw-proj-")
        self.assertEqual(self._run(install, project=True, cwd=proj).returncode, 0)
        # Plant a stale file that the source does not contain, then re-run.
        stale = proj / ".workflow" / "shared" / "STALE.md"
        stale.write_text("left over from a previous pin", encoding="utf-8")
        result = self._run(install, project=True, cwd=proj)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(stale.exists(), "stale file survived a re-install (not wholesale)")
        self.assertTrue((proj / ".workflow" / "shared" / "CONTEXT.md").is_file())

    def test_missing_required_key_fails_cleanly(self):
        glossary, _ = make_repo(self._tmp("dw-glossary-"), {"CONTEXT.md": self.GLOSSARY})
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": "."},  # no "ref"
        )
        result = self._run(install, project=True, cwd=self._tmp("dw-proj-"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required key", result.stderr)
        self.assertNotIn("Traceback", result.stderr)  # clean message, not a stacktrace

    def test_missing_context_md_fails_loudly(self):
        repo, sha = make_repo(self._tmp("dw-glossary-"), {"README.md": "no glossary here"})
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(repo), "path": ".", "ref": sha},
        )
        result = self._run(install, project=True, cwd=self._tmp("dw-proj-"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no CONTEXT.md", result.stderr)

    def test_invalid_ref_fails_loudly(self):
        glossary, _ = make_repo(self._tmp("dw-glossary-"), {"CONTEXT.md": self.GLOSSARY})
        bad = "0" * 40
        install = doctored_install(
            self._tmp("dw-tree-"),
            shared_context={"source": str(glossary), "path": ".", "ref": bad},
        )
        result = self._run(install, project=True, cwd=self._tmp("dw-proj-"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shared context", result.stderr)
        self.assertIn(bad, result.stderr)


if __name__ == "__main__":
    unittest.main()

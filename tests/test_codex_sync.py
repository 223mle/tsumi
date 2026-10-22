import fcntl
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync-codex-skills"
INSTALL = ROOT / "scripts" / "install-codex-sync"
NAMES = ("clear-japanese", "agent-design-review", "tsumi-mode")


class CodexSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / "source"
        self.repo.mkdir()
        self.git("init", "-b", "fixture")
        for name in NAMES:
            skill = self.repo / "skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("version one\n")
        self.commit()
        self.state = self.home / ".codex" / "tsumi"

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def run_sync(self, source=None):
        return subprocess.run(["/usr/bin/python3", str(SYNC), "--state-dir", str(self.state), "--source", str(source or self.repo), "--ref", "refs/heads/fixture"], capture_output=True, text=True)

    def test_update_repeat_and_source_refs_unchanged(self):
        refs = self.git("show-ref")
        self.assertEqual(self.run_sync().returncode, 0)
        current = self.state / "current"
        first = current.resolve()
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(current.resolve(), first)
        self.assertEqual(self.git("show-ref"), refs)
        skill = self.repo / "skills" / "clear-japanese" / "SKILL.md"
        skill.write_text("version two\n")
        commit = self.commit()
        refs = self.git("show-ref")
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(current.resolve().name, commit)
        self.assertEqual((current / "skills/clear-japanese/SKILL.md").read_text(), "version two\n")
        self.assertEqual((first / "skills/clear-japanese/SKILL.md").read_text(), "version one\n")
        self.assertEqual(self.git("show-ref"), refs)
        cache_refs = subprocess.run(["git", "--git-dir", str(self.state / "cache.git"), "show-ref"], capture_output=True)
        self.assertEqual(cache_refs.stdout, b"")

    def test_failed_fetch_preserves_current(self):
        self.assertEqual(self.run_sync().returncode, 0)
        previous = (self.state / "current").resolve()
        self.assertNotEqual(self.run_sync(self.home / "missing").returncode, 0)
        self.assertEqual((self.state / "current").resolve(), previous)

    def test_git_failure_does_not_log_command_arguments(self):
        secret = "credential-do-not-log"
        result = self.run_sync(self.home / secret)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stderr)
        self.assertNotIn(secret, (self.state / "update.log").read_text())

    def test_incomplete_release_preserves_current(self):
        self.assertEqual(self.run_sync().returncode, 0)
        previous = (self.state / "current").resolve()
        (self.repo / "skills/clear-japanese/SKILL.md").unlink()
        self.commit()
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual((self.state / "current").resolve(), previous)

    def test_concurrent_update_skips_and_recovers(self):
        self.state.mkdir(parents=True)
        with (self.state / "update.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.assertEqual(self.run_sync().returncode, 0)
            self.assertFalse((self.state / "current").exists())
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertTrue((self.state / "current").exists())

    def test_archive_symlink_does_not_escape(self):
        self.assertEqual(self.run_sync().returncode, 0)
        previous = (self.state / "current").resolve()
        (self.repo / "external").symlink_to(self.home / "outside")
        self.commit()
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual((self.state / "current").resolve(), previous)
        self.assertFalse((self.home / "outside").exists())

    def test_installer_preserves_hooks_and_is_repeatable(self):
        hooks_path = self.home / ".codex/hooks.json"
        hooks_path.parent.mkdir()
        existing = {"description": "keep", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo existing"}]}]}}
        hooks_path.write_text(json.dumps(existing))
        for name in NAMES:
            path = self.home / ".agents/skills" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(self.home / "tsumi/skills" / name)
        loader = importlib.machinery.SourceFileLoader("installer", str(INSTALL))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        run = subprocess.run

        def local_source(command, **kwargs):
            return run([*command, "--state-dir", str(self.state), "--source", str(self.repo), "--ref", "refs/heads/fixture"], **kwargs)

        replace = module.os.replace

        def fail_hook_write(source, destination):
            if destination == hooks_path:
                raise PermissionError("interrupted hook write")
            return replace(source, destination)

        with patch.object(module.Path, "home", return_value=self.home), patch.object(module.subprocess, "run", side_effect=local_source):
            with patch.object(module.os, "replace", side_effect=fail_hook_write):
                with self.assertRaises(PermissionError):
                    module.main()
            self.assertEqual(json.loads(hooks_path.read_text()), existing)
            module.main()
            first = hooks_path.read_bytes()
            module.main()
        self.assertEqual(hooks_path.read_bytes(), first)
        config = json.loads(first)
        self.assertEqual(config["hooks"]["Stop"], existing["hooks"]["Stop"])
        self.assertEqual(config["description"], "keep")
        self.assertEqual(len(config["hooks"]["SessionStart"]), 1)
        self.assertEqual(config["hooks"]["SessionStart"][0]["matcher"], "^(startup|resume)$")
        for name in NAMES:
            self.assertEqual((self.home / ".agents/skills" / name / "SKILL.md").read_text(), "version one\n")
        backup = json.loads((self.state / "install-backup.json").read_text())
        self.assertEqual(json.loads(backup["hooks"]), existing)


if __name__ == "__main__":
    unittest.main()

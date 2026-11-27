import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.manifests import ManifestError, load_manifest
from automation.package_diff import prepare_bump
from automation.pr_validation import validate_git_pr, validate_pr_files
from automation.render import render_tree
from test_package_diff import CANDIDATE, DIGEST, MANIFEST, STABLE_CASK
from test_render import DARTOTSU


class PRValidationTests(unittest.TestCase):
    def test_accepts_recorded_candidate_and_rejects_wrong_branch_and_stale_ruby(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            base = root / "base"
            head = root / "head"
            manifest = base / MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text(DARTOTSU)
            render_tree(base, check=False)
            shutil.copytree(base, head)
            files = prepare_bump(load_manifest(manifest), "stable", CANDIDATE, {"universal": DIGEST})
            for path, contents in files.items():
                (head / path).write_text(contents)
            with (
                patch("automation.pr_validation.find_candidate", return_value=CANDIDATE),
                patch("automation.pr_validation.candidate_digests", return_value={"universal": DIGEST}),
            ):
                branch = "brewery-bump/cask/dartotsu/1.2.3"
                self.assertEqual(validate_pr_files(base, head, files, branch).version, "1.2.3")
                with self.assertRaisesRegex(ManifestError, "branch"):
                    validate_pr_files(base, head, files, branch + "-wrong")
                (head / STABLE_CASK).write_text("# modified after generation\n")
                with self.assertRaisesRegex(ManifestError, "expected bump"):
                    validate_pr_files(base, head, files, branch)

    def test_requires_the_recorded_base_and_head_in_the_test_merge(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args], text=True, capture_output=True, check=True,
                ).stdout.strip()

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Brewery fixture")
            git("config", "user.email", "brewery@example.invalid")
            git("config", "commit.gpgsign", "false")
            manifest = root / MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text(DARTOTSU)
            render_tree(root, check=False)
            git("add", ".")
            git("commit", "-qm", "Base")
            base = git("rev-parse", "HEAD")
            branch = "brewery-bump/cask/dartotsu/1.2.3"
            git("switch", "-qc", branch)
            for path, contents in prepare_bump(load_manifest(manifest), "stable", CANDIDATE, {"universal": DIGEST}).items():
                (root / path).write_text(contents)
            git("commit", "-qam", "Bump Dartotsu")
            head = git("rev-parse", "HEAD")
            git("switch", "-q", "main")
            git("merge", "--no-ff", "--no-edit", branch)

            with (
                patch("automation.pr_validation.find_candidate", return_value=CANDIDATE),
                patch("automation.pr_validation.candidate_digests", return_value={"universal": DIGEST}),
            ):
                self.assertEqual(validate_git_pr(root, base, head, branch).version, "1.2.3")
            with self.assertRaisesRegex(ManifestError, "stale"):
                validate_git_pr(root, head, base, branch)

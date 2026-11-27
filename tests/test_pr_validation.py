import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.manifests import ManifestError, load_manifest
from automation.package_diff import prepare_bump
from automation.pr_validation import validate_pr_files
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

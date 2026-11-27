import hashlib
from http.client import IncompleteRead
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.manifests import ManifestError, load_manifest
from automation.package_diff import checksum_download, prepare_bump, validate_diff
from automation.releases import Candidate, ReleaseError
from automation.render import render_tree
from test_render import DARTOTSU, PREVIEW


DIGEST = hashlib.sha256(b"new artifact").hexdigest()
MANIFEST = Path("packages/casks/dartotsu.yaml")
STABLE_CASK = Path("Casks/Manga Readers/dartotsu.rb")
PRERELEASE_CASK = Path("Casks/Manga Readers/dartotsu-pre.rb")
CANDIDATE = Candidate(
    "1.2.3", "v1.2.3",
    {"universal": "https://github.com/aayush2622/Dartotsu/releases/download/v1.2.3/Dartotsu-macos-v1.2.3.dmg"},
)


class PackageDiffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / MANIFEST.parent).mkdir(parents=True)
        (self.root / MANIFEST).write_text(DARTOTSU + PREVIEW, encoding="utf-8")
        render_tree(self.root, check=False)
        self.manifest = load_manifest(self.root / MANIFEST)

    def test_bump_changes_only_selected_channel_and_preserves_comment(self):
        prepared = prepare_bump(self.manifest, "stable", CANDIDATE, {"universal": DIGEST})
        self.assertEqual(set(prepared), {MANIFEST, STABLE_CASK})
        self.assertIn('version: "1.2.3" # published version', prepared[MANIFEST])
        self.assertTrue(prepared[MANIFEST].endswith(PREVIEW))
        self.assertIn('version "1.2.3"', prepared[STABLE_CASK])
        self.assertIn('conflicts_with cask: "dartotsu-pre"', prepared[STABLE_CASK])
        self.assertNotIn("1.2.3", (self.root / MANIFEST).read_text())
        validate_diff(self.manifest, "stable", CANDIDATE, {"universal": DIGEST}, prepared)

    def test_url_override_is_generated_from_the_resolved_asset(self):
        candidate = Candidate("1.2.3", "v1.2.3", {"universal": "https://example.org/approved.zip"})
        prepared = prepare_bump(self.manifest, "stable", candidate, {"universal": DIGEST})
        self.assertIn("url: https://example.org/approved.zip", prepared[MANIFEST])
        self.assertIn('url "https://example.org/approved.zip"', prepared[STABLE_CASK])

    def test_validator_rejects_unexpected_changes(self):
        prepared = prepare_bump(self.manifest, "stable", CANDIDATE, {"universal": DIGEST})
        for changes in [
            {**prepared, PRERELEASE_CASK: "# hand edited\n"},
            {**prepared, MANIFEST: prepared[MANIFEST].replace("macos: true", "macos: false")},
            {**prepared, STABLE_CASK: (self.root / STABLE_CASK).read_text()},
            {**prepared, STABLE_CASK: prepared[STABLE_CASK].replace(DIGEST, "0" * 64)},
            {MANIFEST: prepared[MANIFEST]},
        ]:
            with self.subTest(paths=changes.keys()), self.assertRaisesRegex(ManifestError, "expected bump"):
                validate_diff(self.manifest, "stable", CANDIDATE, {"universal": DIGEST}, changes)

    def test_downgrade_or_bad_digest_cannot_prepare_bump(self):
        for candidate, checksum in [(CANDIDATE, "bogus"), (Candidate("0.9.0", "v0.9.0", CANDIDATE.urls), DIGEST)]:
            with self.subTest(candidate=candidate), self.assertRaises(ManifestError):
                prepare_bump(self.manifest, "stable", candidate, {"universal": checksum})

    def test_per_architecture_artifacts_render_with_distinct_checksums(self):
        intel = "1" * 64
        candidate = Candidate("1.2.3", "v1.2.3", {
            "arm64": "https://example.org/Dartotsu-arm64.dmg",
            "x86_64": "https://example.org/Dartotsu-intel.dmg",
        })
        result = prepare_bump(self.manifest, "stable", candidate, {"arm64": DIGEST, "x86_64": intel})
        self.assertIn(f'on_arm do\n    sha256 "{DIGEST}"', result[STABLE_CASK])
        self.assertIn(f'on_intel do\n    sha256 "{intel}"', result[STABLE_CASK])
        self.assertIn("Dartotsu-arm64.dmg", result[STABLE_CASK])
        self.assertIn("Dartotsu-intel.dmg", result[STABLE_CASK])

    def test_truncated_http_response_is_a_package_failure(self):
        with patch("automation.package_diff.build_opener") as opener:
            opener.return_value.open.side_effect = IncompleteRead(b"partial")
            with self.assertRaisesRegex(ReleaseError, "package download failed"):
                checksum_download("https://example.org/asset.zip")

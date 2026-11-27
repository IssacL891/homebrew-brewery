import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.bumps import main, scan
from automation.manifests import load_manifest
from automation.releases import Candidate, ReleaseError, resolve_releases
from test_render import DARTOTSU as DARTOTSU_MANIFEST


DARTOTSU = {
    "repository": "aayush2622/Dartotsu",
    "tag_prefix": "v",
    "assets": {"universal": "Dartotsu-macos-{tag}.dmg"},
    "fallback": True,
}
YAAGL = {
    "repository": "yaagl/yet-another-anime-game-launcher",
    "assets": {"universal": "Yaagl.HSR.OS.app.tar.gz"},
}


def release(policy, tag, name=None, *, pre=False, draft=False):
    assets = [] if name is None else [{
        "name": name,
        "state": "uploaded",
        "browser_download_url": f"https://github.com/{policy['repository']}/releases/download/{tag}/{name}",
    }]
    return {"tag_name": tag, "prerelease": pre, "draft": draft, "assets": assets}


class ReleaseTests(unittest.TestCase):
    def test_uses_highest_published_dartotsu_release_with_exact_asset(self):
        result = resolve_releases([
            release(DARTOTSU, "v2026-10-14", "Other-app.apk"),
            release(DARTOTSU, "v1.2.3", "Dartotsu-macos-v1.2.3.dmg", draft=True),
            release(DARTOTSU, "v1.2.2", "Dartotsu-macos-v1.2.2.dmg"),
        ], {**DARTOTSU, "tag_pattern": r"v\d+\.\d+\.\d+"}, "1.0.0", "stable")
        self.assertEqual(result.version, "1.2.2")
        self.assertEqual(result.tag, "v1.2.2")
        self.assertTrue(result.urls["universal"].endswith("/v1.2.2/Dartotsu-macos-v1.2.2.dmg"))

    def test_yaagl_selects_stable_and_pre_independently(self):
        releases = [
            release(YAAGL, "0.4.1-alpha", "Yaagl.HSR.OS.app.tar.gz", pre=True),
            release(YAAGL, "0.4.0", "Yaagl.HSR.OS.app.tar.gz"),
        ]
        self.assertEqual(resolve_releases(releases, YAAGL, "0.3.21", "stable").version, "0.4.0")
        self.assertEqual(resolve_releases(releases, YAAGL, "0.4.0", "pre").version, "0.4.1-alpha")
        self.assertIsNone(resolve_releases(releases, YAAGL, "0.4.1", "pre"))
        self.assertIsNone(resolve_releases(releases, YAAGL, "0.4.1-alpha", "stable"))

    def test_incomplete_release_requires_configured_fallback_and_all_assets(self):
        latest = release(YAAGL, "0.4.2-alpha", "Yaagl.HSR.OS.app.tar.tar", pre=True)
        older = release(YAAGL, "0.4.1-alpha", "Yaagl.HSR.OS.app.tar.gz", pre=True)
        with self.assertRaisesRegex(ReleaseError, "missing"):
            resolve_releases([latest, older], YAAGL, "0.4.0", "pre")
        self.assertEqual(resolve_releases([latest, older], {**YAAGL, "fallback": True}, "0.4.0", "pre").version, "0.4.1-alpha")
        with self.assertRaisesRegex(ReleaseError, "x86_64"):
            resolve_releases([older], {**YAAGL, "assets": {
                "arm64": "Yaagl.HSR.OS.app.tar.gz", "x86_64": "Yaagl.HSR.OS.intel.tar.gz",
            }}, "0.4.0", "pre")

    def test_ambiguous_or_unorderable_release_is_reported(self):
        rc = release(YAAGL, "0.4.1-alpha", "Yaagl.HSR.OS.app.tar.gz", pre=True)
        rc["assets"] *= 2
        with self.assertRaisesRegex(ReleaseError, "ambiguous"):
            resolve_releases([rc], YAAGL, "0.4.0", "pre")
        with self.assertRaisesRegex(ReleaseError, "cannot compare"):
            resolve_releases([release(YAAGL, "not-a-version", pre=True)], YAAGL, "0.4.0", "pre")

    def test_mixed_scan_reports_package_failure_and_finishes(self):
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch) / "packages/casks"
            directory.mkdir(parents=True)
            for token in ("dartotsu", "healthy"):
                (directory / f"{token}.yaml").write_text(
                    DARTOTSU_MANIFEST.replace("token: dartotsu", f"token: {token}"),
                )
            manifests = [load_manifest(path) for path in sorted(directory.glob("*.yaml"))]
            with patch("automation.bumps.find_candidate", side_effect=[
                ReleaseError("missing macOS asset"),
                Candidate("1.2.3", "1.2.3", {"universal": "https://example.org/app.zip"}),
            ]), contextlib.redirect_stdout(io.StringIO()) as console:
                result = scan(manifests)
        self.assertEqual([row.status for row in result], ["warning", "candidate"])
        self.assertIn("dartotsu", console.getvalue())
        self.assertIn("healthy", console.getvalue())

    def test_shared_homebrew_failure_fails_before_scanning_packages(self):
        with (
            patch("sys.argv", ["bumps.py", "scan", "--dry-run"]),
            patch("automation.bumps.subprocess.run", side_effect=subprocess.CalledProcessError(1, "brew")),
            contextlib.redirect_stderr(io.StringIO()) as errors,
        ):
            self.assertEqual(main(), 1)
        self.assertIn("scan could not run", errors.getvalue())

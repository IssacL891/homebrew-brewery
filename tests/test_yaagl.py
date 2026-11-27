import unittest
from pathlib import Path

from automation.manifests import load_manifest
from automation.render import render_manifest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ASSETS = {
    "yaagl-gi": "Yaagl.app.tar.gz",
    "yaagl-gi-os": "Yaagl.OS.app.tar.gz",
    "yaagl-hsr": "Yaagl.HSR.app.tar.gz",
    "yaagl-hsr-os": "Yaagl.HSR.OS.app.tar.gz",
    "yaagl-zzz": "Yaagl.ZZZ.app.tar.gz",
    "yaagl-zzz-os": "Yaagl.ZZZ.OS.app.tar.gz",
}


class YaaglChannelTests(unittest.TestCase):
    def test_all_editions_have_conflicting_stable_and_prerelease_definitions(self):
        for token, asset in EXPECTED_ASSETS.items():
            with self.subTest(token=token):
                manifest = load_manifest(ROOT / "packages" / "casks" / "Yaagl" / f"{token}.yaml")
                self.assertEqual(manifest.data["upstream"]["assets"], {"universal": asset})
                self.assertEqual(set(manifest.data["channels"]), {"stable", "pre"})
                definitions = render_manifest(manifest)
                stable = definitions[Path("Casks/Yaagl") / f"{token}.rb"]
                preview = definitions[Path("Casks/Yaagl") / f"{token}-pre.rb"]
                self.assertIn(f'conflicts_with cask: "{token}-pre"', stable)
                self.assertIn(f'conflicts_with cask: "{token}"', preview)

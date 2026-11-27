import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.manifests import ManifestError, dump_manifest, load_manifest
from automation.render import render_manifest, render_tree


DIGEST = "6da82a5767db52da522d18260b87e887b3516ce9d8a9266c7b7b89f484fb22fa"
DARTOTSU = f"""schema: 1
kind: cask
token: dartotsu
directory: Manga Readers
name: Dartotsu
desc: Complete rewrite of Dantotsu in Flutter
homepage: https://github.com/aayush2622/Dartotsu
url: https://github.com/aayush2622/Dartotsu/releases/download/v{{version}}/Dartotsu-macos-v{{version}}.dmg
livecheck:
  url: url
  strategy: git
macos: true
app: Dartotsu.app
channels:
  stable:
    version: "1.0.0" # published version
    sha256: "{DIGEST}"
"""
PREVIEW = f"""  pre:
    version: "1.1.0-alpha"
    sha256: "{DIGEST}"
"""


class RenderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def manifest(self, text=DARTOTSU, path="packages/casks/dartotsu.yaml"):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_nested_cask_keeps_published_metadata(self):
        result = render_manifest(load_manifest(self.manifest()))
        ruby = result[Path("Casks/Manga Readers/dartotsu.rb")]
        self.assertIn('version "1.0.0"', ruby)
        self.assertIn(f'sha256 "{DIGEST}"', ruby)
        self.assertIn('download/v#{version}/Dartotsu-macos-v#{version}.dmg', ruby)
        self.assertIn("livecheck do\n    url :url\n    strategy :git", ruby)
        self.assertIn("depends_on :macos", ruby)
        self.assertIn('app "Dartotsu.app"', ruby)
        self.assertEqual(subprocess.run(["ruby", "-c"], input=ruby, text=True, capture_output=True).returncode, 0)

    def test_channels_preserve_cleanup_and_conflict_with_each_other(self):
        manifest = DARTOTSU.replace("channels:", 'zap:\n  - "~/Library/Application Support/Dartotsu"\nchannels:')
        outputs = render_manifest(load_manifest(self.manifest(manifest + PREVIEW)))
        stable = outputs[Path("Casks/Manga Readers/dartotsu.rb")]
        preview = outputs[Path("Casks/Manga Readers/dartotsu-pre.rb")]
        self.assertIn('version "1.0.0"', stable)
        self.assertIn('version "1.1.0-alpha"', preview)
        self.assertIn('conflicts_with cask: "dartotsu-pre"', stable)
        self.assertIn('conflicts_with cask: "dartotsu"', preview)
        for ruby in (stable, preview):
            self.assertIn('zap trash: "~/Library/Application Support/Dartotsu"', ruby)

    def test_formula_contains_reviewed_recipe_and_inline_patch(self):
        recipe = self.root / "recipes"
        recipe.mkdir()
        (recipe / "dartotsu.rb").write_text('def install\n  bin.install "dartotsu"\nend\n')
        (recipe / "dartotsu.patch").write_text('diff --git a/Makefile b/Makefile\n')
        manifest = DARTOTSU.replace("kind: cask", "kind: formula")
        for start in ("directory:", "name:", "macos:", "app:"):
            manifest = "\n".join(line for line in manifest.split("\n") if not line.startswith(start))
        manifest = manifest.replace(
            "channels:", "recipe: recipes/dartotsu.rb\npatch: recipes/dartotsu.patch\nchannels:"
        )
        outputs = render_manifest(load_manifest(self.manifest(manifest + PREVIEW, "packages/formulae/dartotsu.yaml")))
        preview = outputs[Path("Formula/dartotsu-pre.rb")]
        self.assertIn("class DartotsuPre < Formula", preview)
        self.assertIn('conflicts_with "dartotsu"', preview)
        self.assertIn('bin.install "dartotsu"', preview)
        self.assertIn("patch :DATA", preview)
        self.assertIn("__END__\ndiff --git a/Makefile b/Makefile", preview)
        self.assertIn("download/v1.1.0-alpha/Dartotsu-macos-v1.1.0-alpha.dmg", preview)
        self.assertEqual(subprocess.run(["ruby", "-c"], input=preview, text=True, capture_output=True).returncode, 0)

    def test_rejects_bad_manifests(self):
        for manifest in (
            DARTOTSU + "name: Duplicate\n",
            DARTOTSU + "unexpected: true\n",
            DARTOTSU.replace(DIGEST, "bad"),
            DARTOTSU.replace("Manga Readers", "../../elsewhere"),
            DARTOTSU.replace("{version}", "{outside}"),
            DARTOTSU.replace("Dartotsu.app", "!!python/object:builtins.object {}"),
        ):
            with self.subTest(manifest=manifest), self.assertRaises(ManifestError):
                load_manifest(self.manifest(manifest))

    def test_interpolation_in_labels_is_literal(self):
        manifest = DARTOTSU.replace("name: Dartotsu", """name: 'Dartotsu #{raise "executed"}'""")
        ruby = next(iter(render_manifest(load_manifest(self.manifest(manifest))).values()))
        result = subprocess.run(
            ["ruby", "-e", "def cask(*)\n yield\nend\n"
             "def name(value)\n puts value\nend\n"
             "def method_missing(*)\nend\n" + ruby],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(result.stdout, 'Dartotsu #{raise "executed"}\n')

    def test_manifests_round_trip_and_check_drift_without_writing(self):
        manifest_path = self.manifest()
        self.assertEqual(dump_manifest(load_manifest(manifest_path)), manifest_path.read_text())
        self.assertEqual(render_tree(self.root, check=False), [])
        target = self.root / "Casks/Manga Readers/dartotsu.rb"
        target.write_text("# unrelated edit\n")
        self.assertEqual(render_tree(self.root, check=True), [target.relative_to(self.root)])
        self.assertEqual(target.read_text(), "# unrelated edit\n")

    def test_detects_colliding_output_paths(self):
        self.manifest(DARTOTSU + PREVIEW)
        self.manifest(
            DARTOTSU.replace("token: dartotsu", "token: dartotsu-pre"),
            "packages/casks/dartotsu-pre.yaml",
        )
        with self.assertRaisesRegex(ManifestError, "duplicate output"):
            render_tree(self.root, check=True)


if __name__ == "__main__":
    unittest.main()

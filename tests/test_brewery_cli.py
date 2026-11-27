import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.manifests import yaml_parser
from automation.render import render_tree


CLI = Path(__file__).resolve().parents[1] / "automation" / "brewery.py"


class BreweryCLITests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CLI), "--root", str(self.root), *args],
            text=True, capture_output=True, check=False,
        )

    def test_prints_a_cask_template_without_creating_files(self):
        result = self.run_cli("new", "cask", "my-app", "--category", "Apps/Utilities")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = yaml_parser().load(result.stdout)
        self.assertEqual((data["schema"], data["kind"], data["token"]), (1, "cask", "my-app"))
        self.assertIsNone(data["app"])
        self.assertIn("Exact bundle name", result.stdout)
        self.assertIn("sha256", data["channels"]["stable"])
        self.assertNotIn("directory", data)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_writes_a_preview_pair_that_renders_after_filling_it_in(self):
        result = self.run_cli("new", "cask", "my-app", "--category", "Daily Tools/Apps", "--pre", "--write")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.root / "packages/casks/Daily Tools/Apps/my-app.yaml"
        self.assertTrue(path.is_file())
        self.assertFalse((self.root / "Casks").exists())
        data = yaml_parser().load(path.read_text())
        self.assertEqual(set(data["channels"]), {"stable", "pre"})
        self.assertIsNone(data["upstream"]["repository"])
        data.update(
            name="My App", desc="Test app", homepage="https://example.org",
            url="https://example.org/{version}/MyApp.zip", app="My App.app",
            upstream={"repository": "example/my-app", "assets": {"universal": "MyApp.zip"}},
        )
        for channel, version in (("stable", "1.2.3"), ("pre", "1.2.4-beta")):
            data["channels"][channel] = {"version": version, "sha256": "1" * 64}
        with path.open("w", encoding="utf-8") as stream:
            yaml_parser().dump(data, stream)
        self.assertEqual(render_tree(self.root, check=False), [])
        directory = self.root / "Casks/Daily Tools/Apps"
        self.assertTrue((directory / "my-app.rb").is_file())
        self.assertTrue((directory / "my-app-pre.rb").is_file())

    def test_prints_a_formula_template_with_a_recipe_field(self):
        result = self.run_cli("new", "formula", "my-tool")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = yaml_parser().load(result.stdout)
        self.assertEqual(data["kind"], "formula")
        self.assertIn("recipe", data)
        self.assertNotIn("app", data)

    def test_rejects_collisions_across_categories_and_reviewed_ruby_files(self):
        first = self.run_cli("new", "cask", "my-app", "--pre", "--category", "Tools", "--write")
        self.assertEqual(first.returncode, 0, first.stderr)
        existing = self.root / "packages/casks/Tools/my-app.yaml"
        original = existing.read_bytes()

        for token, category in (("my-app", "Tools"), ("my-app", "Other"), ("my-app-pre", "Other")):
            with self.subTest(token=token, category=category):
                result = self.run_cli("new", "cask", token, "--category", category, "--write")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(token, result.stderr)
        self.assertEqual(existing.read_bytes(), original)
        self.assertFalse((self.root / "packages/casks/Other").exists())

        ruby = self.root / "Formula/my-tool.rb"
        ruby.parent.mkdir()
        ruby.write_text("# manually maintained\n")
        result = self.run_cli("new", "formula", "my-tool", "--write")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("my-tool", result.stderr)

    def test_rejects_unsafe_paths_and_can_create_another_draft(self):
        for args in (("Bad Token",), ("my-app", "--category", "../outside"), ("my-app", "--category", "/private/tmp")):
            with self.subTest(args=args):
                self.assertNotEqual(self.run_cli("new", "cask", *args, "--write").returncode, 0)
        self.assertEqual(list(self.root.iterdir()), [])
        for token in ("first-app", "second-app"):
            result = self.run_cli("new", "cask", token, "--write")
            self.assertEqual(result.returncode, 0, result.stderr)

import hashlib
import json
from pathlib import Path
import platform
import shutil
import tempfile
import unittest
from unittest.mock import patch

from automation.bumps import scan
from automation.manifests import load_manifest
from automation.package_diff import prepare_bump
from automation.releases import ReleaseError, resolve_releases
from test_render import DARTOTSU

from automation.build_artifacts import BuildError, bottle_from_json, build_artifact, build_bottle, publish_release, release_identity, select_artifact
from automation.releases import Candidate


class ArtifactTests(unittest.TestCase):
    def test_upstream_is_preferred_and_only_declared_missing_targets_build(self):
        candidate = Candidate("2.0", "v2.0", {"arm64": "https://example.org/app.zip"}, ["x86_64"])
        self.assertEqual(select_artifact(candidate, "arm64", {"targets": ["arm64", "x86_64"]}), "upstream")
        self.assertEqual(select_artifact(candidate, "x86_64", {"targets": ["x86_64"]}), "build")
        self.assertEqual(select_artifact(candidate, "x86_64", {}), "missing")
        self.assertEqual(select_artifact(candidate, "universal", {"targets": ["universal"]}), "missing")

    def test_release_identity_separates_channels_and_recipe_versions(self):
        args = ("cask", "sample", "stable", "2.0", "a" * 40, "b" * 64)
        self.assertNotEqual(release_identity(*args), release_identity(*args[:2], "pre", *args[3:]))
        self.assertNotEqual(release_identity(*args), release_identity(*args[:-1], "c" * 64))

    def test_bottle_names_and_metadata_come_from_homebrew(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            archive = directory / "sample--2.0.arm64_tahoe.bottle.tar.gz"
            archive.write_bytes(b"bottle fixture")
            sha = hashlib.sha256(archive.read_bytes()).hexdigest()
            metadata = {"tap/repo/sample": {
                "formula": {"name": "sample", "pkg_version": "2.0"},
                "bottle": {
                    "root_url": "https://example.org/asset", "cellar": "any_skip_relocation", "rebuild": 0,
                    "tags": {"arm64_tahoe": {"filename": "sample-2.0.arm64_tahoe.bottle.tar.gz",
                                              "local_filename": archive.name, "sha256": sha}},
                },
            }}
            root = "https://example.org/asset"
            path, published, bottle = bottle_from_json(directory, metadata, "sample", "2.0", "arm64_tahoe", root)
            self.assertEqual((path, published), (archive, "sample-2.0.arm64_tahoe.bottle.tar.gz"))
            self.assertEqual(bottle["tags"]["arm64_tahoe"], {"cellar": "any_skip_relocation", "sha256": sha})
            with self.assertRaises(BuildError):
                bottle_from_json(directory, metadata, "sample", "2.0", "x86_64", root)
            archive.write_bytes(b"changed")
            with self.assertRaises(BuildError):
                bottle_from_json(directory, metadata, "sample", "2.0", "arm64_tahoe", root)

    def test_publisher_reuses_draft_assets_and_verifies_public_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            path.write_bytes(b"artifact")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            calls = []

            class Fixture:
                def release(self, tag):
                    return {"draft": True, "id": 5, "body": json.dumps(receipt), "assets": [{"name": path.name, "digest": f"sha256:{digest}"}]}

                def upload(self, tag, path):
                    raise AssertionError("matching assets must be reused")

                def finalize(self, release_id):
                    calls.append(release_id)

            receipt = {"tag": "brewery-build-test", "channel": "stable", "files": {path.name: digest}}
            publish_release(Fixture(), receipt, {path.name: path}, lambda name: digest)
            self.assertEqual(calls, [5])
            with self.assertRaises(BuildError):
                publish_release(Fixture(), receipt, {path.name: path}, lambda name: "0" * 64)

    @unittest.skipUnless(platform.system() == "Darwin", "macOS fixture")
    def test_recipe_builds_an_executable_archive_and_rejects_wrong_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "packages/casks/dartotsu.yaml"
            path.parent.mkdir(parents=True)
            recipe = root / "recipes/dartotsu.sh"
            recipe.parent.mkdir()
            shutil.copyfile(Path(__file__).parent / "fixtures/build/cask.sh", recipe)
            path.write_text(DARTOTSU.replace("schema: 1", "schema: 2") + """
upstream:
  repository: example/app
  assets:
    arm64: mac-arm64.zip
    x86_64: mac-intel.zip
build:
  script: recipes/dartotsu.sh
  targets: [arm64, x86_64]
""")
            manifest = load_manifest(path)
            source = root / "source.tar.gz"
            source.write_bytes(b"fixture input")
            arch = platform.machine()
            result = build_artifact(manifest, source, arch, root / "stage")
            self.assertGreater(result.stat().st_size, 0)
            wrong = "arm64" if arch == "x86_64" else "x86_64"
            with self.assertRaisesRegex(BuildError, "declared architecture"):
                build_artifact(manifest, source, wrong, root / "stage")

    def test_only_missing_assets_create_build_work(self):
        releases = [{"draft": False, "prerelease": False, "tag_name": "v2.0", "assets": []}]
        policy = {"repository": "example/app", "assets": {"arm64": "sample.zip"}, "tag_prefix": "v"}
        self.assertEqual(resolve_releases(releases, policy, "1.0", "stable",
                                          build_targets=("arm64",)).missing, ["arm64"])
        with self.assertRaisesRegex(ReleaseError, "missing"):
            resolve_releases(releases, policy, "1.0", "stable")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "packages/casks/dartotsu.yaml"
            path.parent.mkdir(parents=True)
            path.write_text(DARTOTSU + "\nupstream:\n  repository: example/app\n  assets:\n    universal: sample.zip\n")
            manifest = load_manifest(path)
            with (
                patch("automation.bumps.github_releases", side_effect=ReleaseError("GitHub release lookup failed")),
                patch("automation.bumps.stage_build") as build,
            ):
                self.assertEqual(scan([manifest], prepare=True, build_dir=Path(tmp))[0].status, "warning")
                build.assert_not_called()

    def test_bottle_build_stages_generated_formula_and_restores_build_tap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            path = root / "packages/formulae/sample.yaml"
            path.parent.mkdir(parents=True)
            recipe = root / "recipes/sample.rb"
            recipe.parent.mkdir()
            recipe.write_text('def install\n  bin.install "sample"\nend\n')
            path.write_text("""schema: 2
kind: formula
token: sample
desc: Build fixture
homepage: https://example.org
recipe: recipes/sample.rb
url: https://example.org/{version}.tar.gz
build:
  bottle_tag: arm64_tahoe
channels:
  stable:
    version: "1.0"
    sha256: \"""" + "1" * 64 + '"\n')
            manifest = load_manifest(path)
            tap = root / "tap"
            installed = tap / "Formula/sample.rb"
            installed.parent.mkdir(parents=True)
            installed.write_text("# original formula\n")
            stage = root / "stage"
            url = "https://example.org/bottles"

            def brew(args, cwd, timeout=900):
                if args[1] == "--repository":
                    return str(tap)
                self.assertIn('version "2.0"', installed.read_text())
                if args[1] == "bottle":
                    file = stage / "sample--2.0.arm64_tahoe.bottle.tar.gz"
                    file.write_bytes(b"fixture bottle")
                    (stage / "sample.bottle.json").write_text(json.dumps({"tap/repo/sample": {
                        "formula": {"name": "sample", "pkg_version": "2.0"},
                        "bottle": {
                            "root_url": url, "cellar": "any", "rebuild": 0,
                            "tags": {"arm64_tahoe": {"filename": "sample-2.0.arm64_tahoe.bottle.tar.gz",
                                                     "local_filename": file.name,
                                                     "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}},
                        },
                    }}))
                return ""

            candidate = Candidate("2.0", "2.0", {"universal": "https://example.org/2.0.tar.gz"})
            with (
                patch.dict("os.environ", {"RUNNER_ENVIRONMENT": "github-hosted", "ACT": ""}),
                patch("automation.build_artifacts.platform.system", return_value="Darwin"),
                patch("automation.build_artifacts.command", side_effect=brew),
            ):
                file, bottle = build_bottle(manifest, "stable", candidate, {"universal": "2" * 64},
                                            "fixture/repo", "sample", url, stage)
            self.assertTrue(file.is_file())
            self.assertEqual(installed.read_text(), "# original formula\n")
            prepared = prepare_bump(manifest, "stable",
                                    Candidate(candidate.version, candidate.tag, candidate.urls, bottle=bottle),
                                    {"universal": "2" * 64})
            self.assertIn("bottle do", prepared[Path("Formula/sample.rb")])
            self.assertIn("sha256 cellar: :any, arm64_tahoe:", prepared[Path("Formula/sample.rb")])

    def test_publication_builds_pr_diff_only_after_public_checksum_passes(self):
        from automation.build_artifacts import recipe_hash
        from automation.bumps import PackageResult
        from automation.publish import GitHub

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            path = root / "packages/casks/dartotsu.yaml"
            path.parent.mkdir(parents=True)
            recipe = root / "recipes/dartotsu.sh"
            recipe.parent.mkdir()
            recipe.write_text("exit 1\n")
            path.write_text(DARTOTSU.replace("schema: 1", "schema: 2") + """
upstream:
  repository: example/app
  assets:
    universal: sample.zip
build:
  script: recipes/dartotsu.sh
  targets: [universal]
""")
            manifest = load_manifest(path)
            source = "1" * 40
            fingerprint = recipe_hash(manifest)
            tag = release_identity("cask", "dartotsu", "stable", "2.0", source, fingerprint)
            filename = "dartotsu-universal.zip"
            stage = root / "staged" / tag
            stage.mkdir(parents=True)
            (stage / filename).write_bytes(b"fixture")
            digest = hashlib.sha256(b"fixture").hexdigest()
            receipt = {"tag": tag, "kind": "cask", "token": "dartotsu", "channel": "stable", "version": "2.0",
                       "revision": source, "recipe": fingerprint, "targets": {"universal": filename},
                       "files": {filename: digest}}
            candidate = Candidate("2.0", "v2.0", {}, ["universal"])
            package = PackageResult("cask", "dartotsu", "stable", "built", "staged",
                                    candidate, build={"receipt": receipt, "digests": {}})
            api = GitHub(root, "tester/brewery", "fixture[bot]", root / "staged")
            release = {"id": 10, "draft": True, "body": json.dumps(receipt), "assets": []}
            with (
                patch.object(api, "release", return_value=release),
                patch.object(api, "upload") as upload,
                patch.object(api, "finalize") as finalize,
                patch("automation.publish.checksum_download", return_value=digest),
                patch("automation.publish.candidate_digests", return_value={"universal": digest}),
            ):
                published = api.publish_build(package)
            upload.assert_called_once_with(tag, stage / filename)
            finalize.assert_called_once_with(10)
            self.assertIn(f"/{tag}/{filename}", published.files[Path("Casks/Manga Readers/dartotsu.rb")])
            with (
                patch.object(api, "release", return_value={**release, "draft": False,
                             "assets": [{"name": filename, "digest": f"sha256:{digest}"}]}),
                patch("automation.publish.checksum_download", return_value="0" * 64),
                patch("automation.publish.prepare_bump") as prepare,
            ):
                with self.assertRaisesRegex(BuildError, "public download"):
                    api.publish_build(package)
                prepare.assert_not_called()

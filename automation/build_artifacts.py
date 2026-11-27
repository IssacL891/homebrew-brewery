"""Build opted-in fallback artifacts and verify their release receipts."""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import quote, unquote
import zipfile

from automation.manifests import SHA256
from automation.package_diff import candidate_digests, checksum_download, prepare_bump
from automation.releases import ReleaseError, github_releases, read_json


class BuildError(ValueError):
    """A declared binary could not be built or verified."""


def select_artifact(candidate, target: str, policy: dict) -> str:
    if target in candidate.urls:
        return "upstream"
    if target in candidate.missing and target in policy.get("targets", ()):
        return "build"
    return "missing"


def digest_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise BuildError("required artifact is missing or invalid")
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def release_identity(kind: str, token: str, channel: str, version: str, revision: str, recipe: str) -> str:
    key = json.dumps([kind, token, channel, version, revision, recipe], separators=(",", ":"))
    return f"brewery-build-{kind}-{token}-{channel}-{hashlib.sha256(key.encode()).hexdigest()[:24]}"


def public_url(repository: str, tag: str, filename: str = "") -> str:
    base = f"https://github.com/{repository}/releases/download/{tag}"
    return f"{base}/{quote(filename, safe='')}" if filename else base


def safe_filename(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.+-]+", value) or value in {".", ".."}:
        raise BuildError("invalid artifact filename")
    return value


def command(args: list[str], cwd: Path, timeout: int = 900) -> str:
    # Recipe processes inherit ordinary tools and paths, but no workflow credentials.
    keep = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env.update(HOMEBREW_NO_AUTO_UPDATE="1", HOMEBREW_NO_ANALYTICS="1")
    try:
        return subprocess.run(args, cwd=cwd, env=env, timeout=timeout, text=True,
                              capture_output=True, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        raise BuildError(f"{Path(args[0]).name} failed during package build or validation") from None


def inspect_app_zip(path: Path, bundle: str, target: str, signing: str) -> None:
    expected = {"arm64", "x86_64"} if target == "universal" else {target}
    with tempfile.TemporaryDirectory(prefix="brewery-app-check-") as temporary:
        root = Path(temporary)
        try:
            with zipfile.ZipFile(path) as archive:
                seen = set()
                for item in archive.infolist():
                    parts = PurePosixPath(item.filename)
                    mode = item.external_attr >> 16
                    key = str(parts).casefold()
                    if (parts.is_absolute() or ".." in parts.parts or "\\" in item.filename
                        or not parts.parts or parts.parts[0] != bundle or stat.S_ISLNK(mode) or key in seen):
                        raise BuildError("built ZIP has unexpected or unsafe contents")
                    seen.add(key)
                    extracted = Path(archive.extract(item, root))
                    if not item.is_dir():
                        extracted.chmod(0o755 if mode & 0o111 else 0o644)
            app = root / bundle
            metadata = plistlib.loads((app / "Contents/Info.plist").read_bytes())
            executable = app / "Contents/MacOS" / safe_filename(metadata["CFBundleExecutable"])
            architectures = set(command(["lipo", "-archs", str(executable)], root, 20).split())
            if architectures != expected:
                raise BuildError("built app does not match its declared architecture")
            if signing in {"signed", "notarized"}:
                command(["codesign", "--verify", "--deep", "--strict", str(app)], root, 60)
            if signing == "notarized":
                command(["spctl", "--assess", "--type", "execute", str(app)], root, 60)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile, plistlib.InvalidFileException) as exc:
            if isinstance(exc, BuildError):
                raise
            raise BuildError("built ZIP does not contain the declared macOS app") from None


def build_artifact(manifest, source: Path, target: str, stage: Path) -> Path:
    policy = manifest.data["build"]
    if target not in policy["targets"]:
        raise BuildError("the build target is not configured")
    stage.mkdir(parents=True, exist_ok=True)
    name = safe_filename(f"{manifest.data['token']}-{target}.zip")
    with tempfile.TemporaryDirectory(prefix="brewery-build-") as temporary:
        root = Path(temporary)
        output = root / name
        command(["/bin/bash", str(manifest.resolve_recipe(policy["script"])), str(source), str(output), target], root)
        digest_file(output)
        inspect_app_zip(output, manifest.data["app"], target, policy.get("signing", "none"))
        destination = stage / name
        shutil.copyfile(output, destination)
    return destination


def bottle_from_json(directory: Path, metadata: dict, token: str, version: str, tag: str, root: str):
    try:
        if len(metadata) != 1:
            raise BuildError("expected one Homebrew bottle")
        definition = next(iter(metadata.values()))
        formula = definition["formula"]
        bottle = definition["bottle"]
        if (formula["name"], formula["pkg_version"], bottle["root_url"], bottle["rebuild"]) != (token, version, root, 0):
            raise BuildError("bottle metadata does not match the requested formula and version")
        if set(bottle["tags"]) != {tag}:
            raise BuildError("the runner cannot build the configured bottle target")
        entry = bottle["tags"][tag]
        path = directory / safe_filename(entry["local_filename"])
        name = safe_filename(unquote(entry["filename"]))
        if name != f"{token}-{version}.{tag}.bottle.tar.gz" or digest_file(path) != entry["sha256"]:
            raise BuildError("bottle filename or checksum is incorrect")
        cellar = bottle["cellar"]
        if cellar not in {"any", "any_skip_relocation", "/opt/homebrew/Cellar", "/usr/local/Cellar"}:
            raise BuildError("unexpected bottle cellar")
        return path, name, {"root_url": root, "tags": {tag: {"cellar": cellar, "sha256": entry["sha256"]}}}
    except (KeyError, TypeError):
        raise BuildError("invalid Homebrew bottle metadata") from None


def build_bottle(manifest, channel, candidate, digests, tap: str, token: str, root_url: str, stage: Path):
    if os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted" or os.environ.get("ACT"):
        raise BuildError("formula bottles must be built on disposable GitHub-hosted macOS")
    if platform.system() != "Darwin":
        raise BuildError("formula bottles require macOS")
    files = prepare_bump(manifest, channel, candidate, digests)
    ruby, = (path for path in files if path.suffix == ".rb")
    tap_root = Path(command(["brew", "--repository", tap], manifest.root, 20).strip()).resolve()
    target = tap_root / ruby
    if tap_root == manifest.root or target.resolve() != target:
        raise BuildError("expected a separate trusted build tap")
    original = target.read_bytes()
    stage.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(files[ruby], encoding="utf-8")
        formula = f"{tap}/{token}"
        command(["brew", "install", "--formula", "--build-bottle", formula], stage)
        command(["brew", "bottle", "--json", "--no-rebuild", "--root-url", root_url, formula], stage)
    finally:
        target.write_bytes(original)
    paths = list(stage.glob("*.bottle.json"))
    if len(paths) != 1:
        raise BuildError("Homebrew did not emit a single bottle receipt")
    path, name, bottle = bottle_from_json(stage, json.loads(paths[0].read_text()), token, candidate.version,
                                         manifest.data["build"]["bottle_tag"], root_url)
    destination = stage / name
    path.rename(destination)
    paths[0].unlink()
    return destination, bottle


def recipe_hash(manifest) -> str:
    data = manifest.data
    keys = [data[key] for key in ("recipe", "patch") if key in data]
    if "script" in data["build"]:
        keys.append(data["build"]["script"])
    digest = hashlib.sha256(json.dumps({key: value for key, value in data.items() if key != "channels"},
                                      sort_keys=True).encode())
    for key in keys:
        digest.update(manifest.resolve_recipe(key).read_bytes())
    return digest.hexdigest()


def build_identity(manifest, channel, candidate, digests=None) -> dict:
    data = manifest.data
    if data["kind"] == "formula":
        revision = (digests or candidate_digests(candidate))["universal"]
    else:
        origin = data["upstream"]["repository"]
        commit = read_json(
            ["gh", "api", f"repos/{origin}/commits/{quote(candidate.tag, safe='')}"],
            label="pinned source commit lookup",
        )
        revision = commit.get("sha", "") if isinstance(commit, dict) else ""
        if not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise BuildError("could not pin the upstream source revision")
    recipe = recipe_hash(manifest)
    token = data["token"] + ("-pre" if channel == "pre" else "")
    tag = release_identity(data["kind"], token, channel, candidate.version, revision, recipe)
    return {"tag": tag, "kind": data["kind"], "token": token, "channel": channel, "version": candidate.version,
            "revision": revision, "recipe": recipe}


def finish_candidate(candidate, receipt: dict, repository: str):
    root = public_url(repository, receipt["tag"])
    if receipt["kind"] == "formula":
        bottle = receipt["bottle"]
        if bottle["root_url"] != root or len(bottle["tags"]) != 1:
            raise BuildError("published bottle metadata does not match the build release")
        tag, info = next(iter(bottle["tags"].items()))
        filename = f"{receipt['token']}-{receipt['version']}.{tag}.bottle.tar.gz"
        if receipt["files"] != {filename: info["sha256"]}:
            raise BuildError("published bottle metadata does not match the build receipt")
        return replace(candidate, bottle=bottle)
    names = receipt["targets"]
    if set(names) != set(candidate.missing) or set(names.values()) != set(receipt["files"]):
        raise BuildError("published binaries do not match the missing targets")
    return replace(candidate, urls={**candidate.urls, **{key: public_url(repository, receipt["tag"], name)
                                                          for key, name in names.items()}}, missing=[])


def check_receipt(receipt: dict, identity: dict, manifest, candidate) -> None:
    if not isinstance(receipt, dict) or any(receipt.get(key) != value for key, value in identity.items()):
        raise BuildError("build receipt does not match the pinned source and recipe")
    files = receipt.get("files")
    if not isinstance(files, dict) or not files or any(not isinstance(digest, str) or not SHA256.fullmatch(digest)
                                                     for digest in files.values()):
        raise BuildError("invalid build receipt checksums")
    revision = identity["revision"]
    size = 64 if identity["kind"] == "formula" else 40
    if not isinstance(revision, str) or not re.fullmatch(f"[a-f0-9]{{{size}}}", revision):
        raise BuildError("invalid pinned build source")
    for name in files:
        safe_filename(name)
    if identity["kind"] == "formula":
        if set(receipt.get("bottle", {}).get("tags", {})) != {manifest.data["build"]["bottle_tag"]}:
            raise BuildError("published bottle target does not match the manifest")
    else:
        expected = {target: f"{manifest.data['token']}-{target}.zip" for target in candidate.missing}
        if receipt.get("targets") != expected:
            raise BuildError("published cask targets do not match the manifest")


def read_published(manifest, channel, candidate, repository: str, app: str, digests=None):
    identity = build_identity(manifest, channel, candidate, digests)
    for release in github_releases(repository):
        if release["tag_name"] != identity["tag"] or release["draft"]:
            continue
        if (not app or (release.get("author") or {}).get("login") != app
                or release.get("prerelease") != (channel == "pre")):
            raise BuildError("published build has an unexpected author")
        try:
            receipt = json.loads(release["body"])
            check_receipt(receipt, identity, manifest, candidate)
            finished = finish_candidate(candidate, receipt, repository)
            for name, digest in receipt["files"].items():
                if checksum_download(public_url(repository, identity["tag"], name)) != digest:
                    raise BuildError("published binary checksum does not match its receipt")
            return identity, finished
        except (TypeError, ValueError, KeyError) as exc:
            if isinstance(exc, (BuildError, ReleaseError)):
                raise
            raise BuildError("invalid published build receipt") from None
    return identity, None


def stage_build(manifest, channel, candidate, identity: dict, repository: str, tap: str, directory: Path,
                digests: dict) -> dict:
    stage = directory / identity["tag"]
    stage.mkdir(parents=True, exist_ok=False)
    receipt = {**identity, "files": {}}
    try:
        if identity["kind"] == "formula":
            file, bottle = build_bottle(manifest, channel, candidate, digests, tap, identity["token"],
                                        public_url(repository, identity["tag"]), stage)
            receipt.update(bottle=bottle, files={file.name: digest_file(file)})
        else:
            with tempfile.TemporaryDirectory(prefix="brewery-source-") as temporary:
                source = Path(temporary) / "source.tar.gz"
                origin = manifest.data["upstream"]["repository"]
                checksum_download(f"https://codeload.github.com/{origin}/tar.gz/{identity['revision']}", output=source)
                receipt["targets"] = {}
                for target in candidate.missing:
                    if select_artifact(candidate, target, manifest.data["build"]) != "build":
                        raise BuildError("the missing target has no approved build script")
                    file = build_artifact(manifest, source, target, stage)
                    receipt["targets"][target] = file.name
                    receipt["files"][file.name] = digest_file(file)
        check_receipt(receipt, identity, manifest, candidate)
    except (OSError, ValueError):
        shutil.rmtree(stage)
        raise
    return receipt


def publish_release(api, receipt: dict, files: dict[str, Path], verify) -> None:
    for name, digest in receipt["files"].items():
        if digest_file(files[name]) != digest:
            raise BuildError("staged artifact changed before publishing")
    tag = receipt["tag"]
    release = api.release(tag)
    if release is None:
        release = api.create_release(receipt)
    else:
        try:
            previous = json.loads(release["body"])
        except (KeyError, TypeError, ValueError):
            raise BuildError("existing build release has no valid receipt") from None
        if previous != receipt:
            raise BuildError("existing release has a different build receipt")
    uploaded = {asset["name"]: asset.get("digest") for asset in release["assets"]}
    if set(uploaded) - receipt["files"].keys():
        raise BuildError("existing build release has unexpected assets")
    for name, digest in receipt["files"].items():
        if name in uploaded:
            if uploaded[name] != f"sha256:{digest}":
                raise BuildError("existing release asset has a different checksum")
        elif release["draft"]:
            api.upload(tag, files[name])
        else:
            raise BuildError("published release is missing an expected asset")
    if release["draft"]:
        api.finalize(release["id"])
    for name, digest in receipt["files"].items():
        if verify(name) != digest:
            raise BuildError("public download did not match the build receipt")

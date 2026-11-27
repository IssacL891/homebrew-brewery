"""Report eligible Brewery bumps without writing to the tap."""

import argparse
from dataclasses import asdict, dataclass
from difflib import unified_diff
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.build_artifacts import BuildError, read_published, stage_build
from automation.manifests import Manifest, ManifestError, load_manifest
from automation.package_diff import candidate_digests, prepare_bump
from automation.releases import Candidate, ReleaseError, github_releases, livecheck_version, resolve_releases, version_key


DEFAULT_TAP = "issacl891/brewery"
DEFAULT_REPOSITORY = "IssacL891/homebrew-brewery"


@dataclass(frozen=True)
class PackageResult:
    kind: str
    token: str
    channel: str
    status: str
    message: str
    candidate: Candidate | None = None
    files: dict[Path, str] | None = None
    build: dict | None = None


def result_to_json(result: PackageResult) -> dict:
    data = asdict(result)
    if result.files:
        data["files"] = {path.as_posix(): contents for path, contents in result.files.items()}
    return data


def result_from_json(data: dict) -> PackageResult:
    candidate = Candidate(**data["candidate"]) if data["candidate"] else None
    files = {Path(path): contents for path, contents in data["files"].items()} if data["files"] else None
    return PackageResult(data["kind"], data["token"], data["channel"], data["status"],
                         data["message"], candidate, files, data.get("build"))


def find_candidate(manifest: Manifest, channel: str, tap: str) -> Candidate | None:
    data = manifest.data
    current = data["channels"][channel]["version"]
    if "upstream" in data:
        policy = data["upstream"]
        return resolve_releases(
            github_releases(policy["repository"]), policy, current, channel,
            build_targets=tuple(data.get("build", {}).get("targets", ())),
        )
    if channel == "pre":
        raise ReleaseError("prerelease requires an explicit upstream policy")

    version = livecheck_version(tap, data["kind"], data["token"])
    parsed = version_key(version)
    if parsed <= version_key(current):
        return None
    if parsed.is_prerelease:
        raise ReleaseError("livecheck returned a prerelease for the stable channel")
    template = data.get("url")
    if not template or "{version}" not in template or "{tag}" in template:
        raise ReleaseError("livecheck bump needs a versioned URL template or explicit upstream policy")
    return Candidate(version, version, {"universal": template.replace("{version}", version)})


def needs_binary(manifest: Manifest, candidate: Candidate) -> bool:
    return bool(candidate.missing or (manifest.data["kind"] == "formula" and "build" in manifest.data))


def prepare_package(
    manifest: Manifest, channel: str, token: str, candidate: Candidate, tap: str, build_dir: Path | None,
) -> PackageResult:
    kind = manifest.data["kind"]
    digests = candidate_digests(candidate)
    if needs_binary(manifest, candidate):
        repository = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY)
        identity, published = read_published(manifest, channel, candidate, repository,
                                             os.environ.get("BREWERY_APP_BOT", ""), digests)
        if published:
            candidate = published
            digests = candidate_digests(candidate)
        elif build_dir is None:
            return PackageResult(kind, token, channel, "build-required", f"{candidate.version} needs a build", candidate)
        else:
            receipt = stage_build(manifest, channel, candidate, identity, repository, tap, build_dir, digests)
            return PackageResult(kind, token, channel, "built", f"{candidate.version} staged for publication",
                                 candidate, build={"receipt": receipt, "digests": digests})
    files = prepare_bump(manifest, channel, candidate, digests)
    return PackageResult(kind, token, channel, "candidate", f"{candidate.version} (tag {candidate.tag})", candidate, files)


def scan(
    manifests: list[Manifest], selector: str | None = None, tap: str = DEFAULT_TAP, *, prepare: bool = False, build_dir: Path | None = None,
) -> list[PackageResult]:
    selected = []
    for manifest in manifests:
        data = manifest.data
        for channel in data["channels"]:
            token = f"{data['token']}-pre" if channel == "pre" else data["token"]
            if selector is None or selector in (token, f"{data['kind']}:{token}"):
                selected.append((manifest, channel, token))
    if selector and len(selected) != 1:
        raise ManifestError(f"expected one package for {selector}; qualify ambiguous tokens as cask: or formula:")

    results = []
    for manifest, channel, token in selected:
        kind = manifest.data["kind"]
        try:
            candidate = find_candidate(manifest, channel, tap)
            status = "candidate" if candidate else "current"
            if prepare and candidate:
                results.append(prepare_package(manifest, channel, token, candidate, tap, build_dir))
                continue
            message = f"{candidate.version} (tag {candidate.tag})" if candidate else "no newer eligible release"
        except BuildError as exc:
            results.append(PackageResult(kind, token, channel, "warning", f"binary build: {exc}"))
        except (ReleaseError, ManifestError, OSError) as exc:
            message = "could not read or write package preparation files" if isinstance(exc, OSError) else str(exc)
            results.append(PackageResult(kind, token, channel, "warning", message))
        else:
            results.append(PackageResult(kind, token, channel, status, message, candidate))

    for result in results:
        print(f"{result.kind}:{result.token} {result.status} — {result.message}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["scan"])
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--package")
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--build-dir", type=Path, help="Stage configured binaries on a disposable runner.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tap", default=DEFAULT_TAP)
    args = parser.parse_args()
    try:
        if args.build_dir and (os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted" or os.environ.get("ACT")):
            raise ManifestError("package build staging requires a disposable GitHub-hosted runner")
        subprocess.run(["brew", "--version"], check=True, capture_output=True, timeout=10)
        paths = sorted((args.root / "packages").glob("*/*.yaml"))
        if not paths:
            raise ManifestError("no package manifests found")
        manifests = []
        failed_manifests = 0
        for path in paths:
            try:
                manifests.append(load_manifest(path))
            except ManifestError:
                print(f"{path.name} warning — invalid package manifest", file=sys.stderr)
                failed_manifests += 1
        if not manifests:
            raise ManifestError("no valid package manifests found")
        results = scan(manifests, args.package, args.tap, prepare=True, build_dir=args.build_dir)
        for result in results:
            for path, proposed in (result.files or {}).items():
                original = (args.root / path).read_text(encoding="utf-8")
                sys.stdout.writelines(unified_diff(
                    original.splitlines(keepends=True), proposed.splitlines(keepends=True),
                    fromfile=f"a/{path}", tofile=f"b/{path}",
                ))
        if args.result_file:
            base = subprocess.run(
                ["git", "-C", str(args.root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
            ).stdout.strip()
            args.result_file.write_text(json.dumps({
                "base_sha": base, "packages": [result_to_json(result) for result in results],
            }), encoding="utf-8")
        warnings = sum(row.status == "warning" for row in results) + failed_manifests
        print(f"{len(results)} channels scanned, {warnings} warnings")
        if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(summary).open("a", encoding="utf-8") as output:
                output.write(f"### Brewery package scan\n\n{len(results)} channels scanned, {warnings} warnings.\n\n")
                for row in results:
                    output.write(f"- {row.kind}:{row.token} **{row.status}** — {row.message}\n")
        return int(bool(args.package and warnings))
    except (ManifestError, OSError, subprocess.SubprocessError) as exc:
        print(f"scan could not run: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

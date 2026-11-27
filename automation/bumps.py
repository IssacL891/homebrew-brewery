"""Report eligible Brewery bumps without writing to the tap."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.manifests import Manifest, ManifestError, load_manifest
from automation.releases import Candidate, ReleaseError, github_releases, livecheck_version, resolve_releases, version_key


DEFAULT_TAP = "issacl891/brewery"


@dataclass(frozen=True)
class PackageResult:
    kind: str
    token: str
    channel: str
    status: str
    message: str
    candidate: Candidate | None = None


def find_candidate(manifest: Manifest, channel: str, tap: str) -> Candidate | None:
    data = manifest.data
    current = data["channels"][channel]["version"]
    if "upstream" in data:
        policy = data["upstream"]
        return resolve_releases(github_releases(policy["repository"]), policy, current, channel)
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


def scan(manifests: list[Manifest], selector: str | None = None, tap: str = DEFAULT_TAP) -> list[PackageResult]:
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
            message = f"{candidate.version} (tag {candidate.tag})" if candidate else "no newer eligible release"
        except ReleaseError as exc:
            results.append(PackageResult(kind, token, channel, "warning", str(exc)))
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
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tap", default=DEFAULT_TAP)
    args = parser.parse_args()
    try:
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
        results = scan(manifests, args.package, args.tap)
        warnings = sum(row.status == "warning" for row in results) + failed_manifests
        print(f"{len(results)} channels scanned, {warnings} warnings")
        return int(bool(args.package and warnings))
    except (ManifestError, OSError, subprocess.SubprocessError) as exc:
        print(f"scan could not run: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

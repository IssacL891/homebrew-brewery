"""Verify a recorded app bump against the trusted Git base and regenerated files."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.build_artifacts import BuildError, read_published
from automation.bumps import DEFAULT_REPOSITORY, find_candidate, needs_binary
from automation.manifests import ManifestError, load_manifest
from automation.package_diff import candidate_digests, validate_diff
from automation.releases import Candidate, ReleaseError
from automation.render import render_tree


FULL_SHA = re.compile(r"[a-f0-9]{40}\Z")
PACKAGE_PATH = re.compile(r"packages/(casks|formulae)/[^/]+\.yaml\Z")


def bump_branch(kind: str, token: str, version: str) -> str:
    slug = quote(version, safe="-._")
    # Encode the edge cases that Git rejects even though URL quoting permits them.
    slug = slug.replace("..", "%2E%2E")
    if slug.endswith((".", ".lock")):
        slug = slug[:slug.rfind(".")] + "%2E" + slug[slug.rfind(".") + 1:]
    return f"brewery-bump/{kind}/{token}/{slug}"


def regular_file(root: Path, relative: Path) -> Path:
    path = root.resolve() / relative
    if not path.is_file() or path.resolve() != path:
        raise ManifestError(f"expected regular file: {relative}")
    return path


def validate_pr_files(
    base: Path, head: Path, changed_paths, branch: str,
) -> Candidate:
    paths = set(changed_paths)
    package_files = [path for path in paths if PACKAGE_PATH.fullmatch(path.as_posix())]
    if len(package_files) != 1:
        raise ManifestError("a bump must change exactly one existing manifest")

    package_path = package_files[0]
    original = load_manifest(regular_file(base, package_path))
    proposed = load_manifest(regular_file(head, package_path))
    old_data = original.data
    new_data = proposed.data
    original_channels = old_data["channels"]
    proposed_channels = new_data["channels"]
    if set(original_channels) != set(proposed_channels):
        raise ManifestError("a bump must preserve its channel definitions")
    changes = [channel for channel, details in original_channels.items() if details != proposed_channels[channel]]
    if len(changes) != 1:
        raise ManifestError("a bump must change exactly one channel")
    channel = changes[0]
    kind = old_data["kind"]
    token = old_data["token"] + ("-pre" if channel == "pre" else "")
    if branch != bump_branch(kind, token, proposed_channels[channel]["version"]):
        raise ManifestError("the branch does not match the proposed package version")

    candidate = find_candidate(original, channel, "issacl891/brewery")
    if candidate is None or candidate.version != proposed_channels[channel]["version"]:
        raise ManifestError("the current upstream candidate does not match the proposed bump")
    artifacts = candidate_digests(candidate)
    if needs_binary(original, candidate):
        _, candidate = read_published(
            original, channel, candidate, os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY),
            os.environ.get("BREWERY_APP_BOT", ""), artifacts,
        )
        if candidate is None:
            raise ManifestError("an opted-in binary has not been published and verified")
        artifacts = candidate_digests(candidate)
    files = {path: regular_file(head, path).read_bytes().decode("utf-8") for path in paths}
    validate_diff(original, channel, candidate, artifacts, files)
    return candidate


def git(root: Path, *args: str) -> str:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}
    return subprocess.run(
        ["git", "-C", str(root), *args], env=env, check=True, text=True, capture_output=True,
    ).stdout


def validate_git_pr(root: Path, base: str, head: str, branch: str) -> Candidate:
    if not FULL_SHA.fullmatch(base) or not FULL_SHA.fullmatch(head):
        raise ManifestError("expected full base and head SHAs")
    merge_base = git(root, "merge-base", base, head).strip()
    parents = git(root, "show", "-s", "--format=%P", "HEAD").split()
    if merge_base != base or parents != [base, head]:
        raise ManifestError("the recorded PR merge ref is stale or does not match the event")

    paths = {
        Path(name) for name in git(root, "diff", "--name-only", "--no-renames", "-z", merge_base, head).split("\0")
        if name
    }
    combined_diff = {
        Path(name) for name in git(root, "diff", "--name-only", "--no-renames", "-z", base, "HEAD").split("\0")
        if name
    }
    if combined_diff != paths:
        raise ManifestError("the test merge changes unexpected files")

    with tempfile.TemporaryDirectory(prefix="brewery-base-") as temporary:
        trusted = Path(temporary) / "tree"
        git(root, "worktree", "add", "--detach", str(trusted), base)
        try:
            candidate = validate_pr_files(trusted, root, paths, branch)
        finally:
            git(root, "worktree", "remove", str(trusted))

    drift = render_tree(root, check=True)
    if drift:
        raise ManifestError(f"generated files do not match YAML: {', '.join(map(str, drift))}")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()
    try:
        candidate = validate_git_pr(args.root, args.base, args.head, args.branch)
    except (ManifestError, ReleaseError, BuildError, subprocess.SubprocessError, OSError, UnicodeError) as exc:
        print(f"PR validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Verified the generated bump for {candidate.version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

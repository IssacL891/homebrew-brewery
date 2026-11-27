"""Select newer releases and verify that the expected published assets exist."""

from dataclasses import dataclass, field
from functools import cache
from itertools import groupby
import json
import os
import re
import subprocess
from urllib.parse import unquote, urlsplit

from packaging.version import InvalidVersion, Version


class ReleaseError(ValueError):
    """A package release could not be selected safely."""


@dataclass(frozen=True)
class Candidate:
    version: str
    tag: str
    urls: dict[str, str]
    missing: list[str] = field(default_factory=list)
    bottle: dict | None = None


def version_key(value: str) -> Version:
    try:
        return Version(value)
    except (InvalidVersion, TypeError):
        raise ReleaseError("cannot compare a release version") from None


def release_asset_url(asset: dict, repository: str, tag: str, name: str) -> str:
    url = asset.get("browser_download_url")
    if not isinstance(url, str):
        raise ReleaseError("release asset has no download URL")
    parsed = urlsplit(url)
    prefix = f"/{repository}/releases/download/"
    path = unquote(parsed.path)
    if (
        parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment
        or path[:len(prefix)].casefold() != prefix.casefold()
        or path[len(prefix):] != f"{tag}/{name}"
    ):
        raise ReleaseError("release asset URL does not match the configured upstream")
    return url


def pick_assets(release: dict, policy: dict, version: str) -> tuple[dict[str, str], list[str]]:
    tag = release["tag_name"]
    urls = {}
    missing = []
    for target, template in policy["assets"].items():
        name = template.replace("{tag}", tag).replace("{version}", version)
        matches = [asset for asset in release.get("assets", []) if asset.get("name") == name
                   and asset.get("state") == "uploaded"]
        if len(matches) > 1:
            raise ReleaseError(f"ambiguous {target} asset")
        if matches:
            urls[target] = release_asset_url(matches[0], policy["repository"], tag, name)
        else:
            missing.append(target)
    return urls, missing


def resolve_releases(releases: list[dict], policy: dict, current_version: str, channel: str,
                     *, build_targets: tuple[str, ...] = ()) -> Candidate | None:
    current = version_key(current_version)
    prefix = policy.get("tag_prefix", "")
    tag_pattern = policy.get("tag_pattern")
    available = []
    for release in releases:
        if release.get("draft") or release.get("prerelease") != (channel == "pre"):
            continue
        tag = release.get("tag_name")
        if not isinstance(tag, str) or not tag.startswith(prefix) or (tag_pattern and not re.fullmatch(tag_pattern, tag)):
            continue
        version = tag.removeprefix(prefix)
        parsed = version_key(version)
        if parsed > current:
            available.append((parsed, version, release))

    missing_for = None
    groups = groupby(sorted(available, key=lambda item: item[0], reverse=True), key=lambda item: item[0])
    for _, group in groups:
        _, version, release = next(group)
        if next(group, None) is not None:
            raise ReleaseError("ambiguous tags for the same package version")
        urls, missing = pick_assets(release, policy, version)
        if not missing or set(missing) <= set(build_targets):
            return Candidate(version, release["tag_name"], urls, missing)
        missing_for = ", ".join(missing)
        if not policy.get("fallback"):
            break
    if missing_for:
        raise ReleaseError(f"missing release asset for {missing_for}")
    return None


def read_json(command: list[str], *, label: str):
    env = {**os.environ, "GH_PROMPT_DISABLED": "1", "HOMEBREW_NO_AUTO_UPDATE": "1",
           "HOMEBREW_NO_ANALYTICS": "1", "HOMEBREW_NO_ENV_HINTS": "1"}
    try:
        process = subprocess.run(command, env=env, text=True, capture_output=True, timeout=120, check=True)
        return json.loads(process.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        raise ReleaseError(f"{label} failed") from None


@cache
def github_releases(repository: str) -> list[dict]:
    pages = read_json(
        ["gh", "api", "--paginate", "--slurp", f"repos/{repository}/releases?per_page=100"],
        label="GitHub release lookup",
    )
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ReleaseError("GitHub returned an invalid release list")
    return [release for page in pages for release in page]


def livecheck_version(tap: str, kind: str, token: str) -> str:
    result = read_json(
        ["brew", "livecheck", f"--{kind}", "--json", "--full-name", f"{tap}/{token}"],
        label="Homebrew livecheck",
    )
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        raise ReleaseError("Homebrew livecheck did not return one package")
    version = result[0].get("version")
    if not isinstance(version, dict) or not isinstance(version.get("latest"), str):
        raise ReleaseError("Homebrew livecheck could not determine the latest version")
    return version["latest"]

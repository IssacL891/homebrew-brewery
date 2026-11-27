"""Prepare and check manifest-only release changes and their generated Ruby."""

from copy import deepcopy
import hashlib
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from automation.manifests import Manifest, ManifestError, SHA256, dump_manifest, validate_manifest
from automation.releases import Candidate, ReleaseError, version_key
from automation.render import render_manifest


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise URLError("package download redirected away from HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def checksum_download(url: str) -> str:
    if urlsplit(url).scheme != "https":
        raise ReleaseError("package download requires HTTPS")
    opener = build_opener(HTTPSRedirects())
    request = Request(url, headers={"User-Agent": "homebrew-brewery/1"})
    digest = hashlib.sha256()
    try:
        with opener.open(request, timeout=45) as response:
            if response.status != 200 or response.headers.get_content_type() == "text/html":
                raise ReleaseError("download did not return the expected artifact")
            size = 0
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            if size == 0:
                raise ReleaseError("download returned an empty artifact")
            length = response.headers.get("Content-Length")
            if length and (not length.isdecimal() or size != int(length)):
                raise ReleaseError("package download ended before its advertised length")
    except (URLError, OSError, HTTPException) as exc:
        status = getattr(exc, "code", None)
        message = f"package download failed (HTTP {status})" if status else "package download failed"
        raise ReleaseError(message) from None
    return digest.hexdigest()


def candidate_digests(candidate: Candidate) -> dict[str, str]:
    return {target: checksum_download(url) for target, url in candidate.urls.items()}


def prepare_bump(manifest: Manifest, channel: str, candidate: Candidate, digests: dict[str, str]) -> dict[Path, str]:
    data = deepcopy(manifest.data)
    release = data["channels"].get(channel)
    if release is None or version_key(candidate.version) <= version_key(release["version"]):
        raise ManifestError("bump must advance an existing channel")
    if set(candidate.urls) != set(digests) or not digests or any(not SHA256.fullmatch(d) for d in digests.values()):
        raise ManifestError("candidate artifacts need verified SHA-256 checksums")

    release["version"] = candidate.version
    release["tag"] = candidate.tag
    if set(digests) == {"universal"}:
        release.pop("artifacts", None)
        release["sha256"] = digests["universal"]
        url = candidate.urls["universal"]
        template = data.get("url", "").replace("{tag}", candidate.tag).replace("{version}", candidate.version)
        if url == template:
            release.pop("url", None)
        else:
            release["url"] = url
    else:
        release.pop("sha256", None)
        release.pop("url", None)
        release["artifacts"] = {key: {"url": candidate.urls[key], "sha256": digests[key]} for key in sorted(digests)}

    updated = Manifest(manifest.path, manifest.root, data)
    validate_manifest(updated)
    original_ruby = render_manifest(manifest)
    generated = render_manifest(updated)
    files = {manifest.path.relative_to(manifest.root): dump_manifest(updated)}
    files.update({path: text for path, text in generated.items() if text != original_ruby[path]})
    if len(files) != 2:
        raise ManifestError("expected one Ruby output to change")
    return files


def validate_diff(
    base: Manifest, channel: str, candidate: Candidate, digests: dict[str, str], changes: dict[Path, str],
) -> None:
    if changes != prepare_bump(base, channel, candidate, digests):
        raise ManifestError("changes do not match the expected bump and regenerated Ruby")

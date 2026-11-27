"""Read and round-trip the package data authored by Brewery maintainers."""

from dataclasses import dataclass
from io import StringIO
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.tokens import AliasToken, AnchorToken, TagToken


class ManifestError(ValueError):
    """A package manifest or its output is invalid."""


@dataclass
class Manifest:
    path: Path
    root: Path
    data: dict

    def resolve_recipe(self, path: str) -> Path:
        recipe = (self.root / path).resolve()
        if not recipe.is_relative_to(self.root / "recipes") or not recipe.is_file():
            raise ManifestError(f"{self.path}: missing or out-of-tree recipe: {path}")
        return recipe


TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9.+,_-]*\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
BOTTLE_TAG = re.compile(r"(?:arm64_)?[a-z][a-z0-9_]*\Z")
PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
COMMON_KEYS = {"schema", "kind", "token", "directory", "desc", "homepage", "url", "channels", "livecheck", "upstream", "build"}
CASK_KEYS = {"name", "macos", "arch", "app", "zap"}
FORMULA_KEYS = {"recipe", "patch", "license", "depends_on"}
MANIFEST_DIRS = {"cask": "casks", "formula": "formulae"}


def yaml_parser() -> YAML:
    parser = YAML(typ="rt")
    parser.allow_duplicate_keys = False
    parser.preserve_quotes = True
    parser.indent(mapping=2, sequence=4, offset=2)
    parser.width = 1000
    parser.max_depth = 16
    return parser


def validate_mapping(data, keys, field: str) -> None:
    if not isinstance(data, dict):
        raise ManifestError(f"{field} must be a mapping")
    unexpected = data.keys() - keys
    if unexpected:
        raise ManifestError(f"unknown {field} field(s): {', '.join(sorted(map(str, unexpected)))}")


def validate_string(value, field: str) -> None:
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise ManifestError(f"{field} must be a nonempty string without control characters")


def validate_string_list(value, field: str) -> None:
    if not isinstance(value, list):
        raise ManifestError(f"{field} must be a list")
    for item in value:
        validate_string(item, field)


def validate_relative_path(value, field: str) -> None:
    validate_string(value, field)
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or value == "." or ".." in path.parts or "\\" in value:
        raise ManifestError(f"{field} must be an ordinary relative path")


def validate_url(value, field: str, templated: bool = False) -> None:
    validate_string(value, field)
    stripped = PLACEHOLDER.sub("", value)
    if "{" in stripped or "}" in stripped:
        raise ManifestError(f"{field} has an invalid URL template")
    placeholders = PLACEHOLDER.findall(value)
    if any(not templated or key not in {"version", "tag"} for key in placeholders):
        raise ManifestError(f"{field} uses an unsupported URL placeholder")
    url = urlsplit(PLACEHOLDER.sub("example", value))
    if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
        raise ManifestError(f"{field} must be an HTTP(S) URL without credentials")


def validate_sha256(value, field: str) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ManifestError(f"{field} is invalid")


def validate_release(release, channel: str, fallback_url: str | None, kind: str, arch: str | None, schema: int) -> None:
    validate_mapping(release, {"version", "sha256", "tag", "url", "artifacts", "bottle"}, channel)
    version = release.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ManifestError(f"{channel}.version is invalid")
    if "tag" in release and (not isinstance(release["tag"], str) or not VERSION.fullmatch(release["tag"])):
        raise ManifestError(f"{channel}.tag is invalid")
    if "bottle" in release:
        if schema != 2 or kind != "formula":
            raise ManifestError("bottles require schema 2 formulae")
        validate_bottle(release["bottle"])
    if "artifacts" in release:
        if kind != "cask" or "url" in release or "sha256" in release:
            raise ManifestError(f"{channel}.artifacts is only for architecture-specific cask downloads")
        artifacts = release["artifacts"]
        validate_mapping(artifacts, {"arm64", "x86_64"}, f"{channel}.artifacts")
        if set(artifacts) != ({arch} if arch in ("arm64", "x86_64") else {"arm64", "x86_64"}):
            raise ManifestError(f"{channel}.artifacts must cover the cask architectures")
        for target, artifact in artifacts.items():
            field = f"{channel}.artifacts.{target}"
            validate_mapping(artifact, {"url", "sha256"}, field)
            validate_url(artifact.get("url"), f"{field}.url")
            validate_sha256(artifact.get("sha256"), f"{field}.sha256")
        return

    validate_sha256(release.get("sha256"), f"{channel}.sha256")
    if "url" in release:
        validate_url(release["url"], f"{channel}.url")
    elif not fallback_url:
        raise ManifestError(f"{channel} needs a URL or a shared URL template")
    elif "{tag}" in fallback_url and "tag" not in release:
        raise ManifestError(f"{channel}.tag is required by the URL template")


def validate_upstream(policy) -> None:
    validate_mapping(policy, {"repository", "tag_prefix", "tag_pattern", "assets", "fallback"}, "upstream")
    repository = policy.get("repository")
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ManifestError("upstream.repository must be a GitHub owner/repo")
    assets = policy.get("assets")
    validate_mapping(assets, {"universal", "arm64", "x86_64"}, "upstream.assets")
    if not assets or ("universal" in assets and len(assets) != 1):
        raise ManifestError("upstream.assets needs a universal asset or explicit architecture assets")
    for name in assets.values():
        validate_string(name, "upstream asset")
        if "/" in name or "\\" in name or any(key not in {"tag", "version"} for key in PLACEHOLDER.findall(name)):
            raise ManifestError("upstream asset name must use only tag or version placeholders")
        if any(brace in PLACEHOLDER.sub("", name) for brace in "{}"):
            raise ManifestError("upstream asset name has unexpected braces")
    if "fallback" in policy and type(policy["fallback"]) is not bool:
        raise ManifestError("upstream.fallback must be a boolean")
    if "tag_prefix" in policy:
        validate_string(policy["tag_prefix"], "upstream.tag_prefix")
    if "tag_pattern" in policy:
        validate_string(policy["tag_pattern"], "upstream.tag_pattern")
        try:
            re.compile(policy["tag_pattern"])
        except re.error as exc:
            raise ManifestError(f"invalid upstream.tag_pattern: {exc}") from exc


def validate_bottle(bottle) -> None:
    validate_mapping(bottle, {"root_url", "tags"}, "bottle")
    validate_url(bottle.get("root_url"), "bottle.root_url")
    tags = bottle.get("tags")
    if not isinstance(tags, dict) or not tags:
        raise ManifestError("bottle.tags must contain at least one Homebrew target")
    for target, entry in tags.items():
        if not isinstance(target, str) or not BOTTLE_TAG.fullmatch(target):
            raise ManifestError("invalid Homebrew bottle target")
        validate_mapping(entry, {"cellar", "sha256"}, "bottle tag")
        if entry.get("cellar") not in ("any", "any_skip_relocation", "/opt/homebrew/Cellar", "/usr/local/Cellar"):
            raise ManifestError("invalid Homebrew bottle cellar")
        validate_sha256(entry.get("sha256"), "bottle.sha256")


def validate_build(manifest: Manifest) -> None:
    data = manifest.data
    build = data["build"]
    if data["schema"] != 2:
        raise ManifestError("build recipes require manifest schema 2")
    if data["kind"] == "formula":
        validate_mapping(build, {"bottle_tag"}, "build")
        if not isinstance(build.get("bottle_tag"), str) or not BOTTLE_TAG.fullmatch(build["bottle_tag"]):
            raise ManifestError("build.bottle_tag must be a Homebrew target")
        return

    validate_mapping(build, {"script", "targets", "signing"}, "build")
    script = build.get("script")
    validate_relative_path(script, "build.script")
    if not script.endswith(".sh"):
        raise ManifestError("build.script must name a reviewed shell recipe")
    manifest.resolve_recipe(script)
    targets = build.get("targets")
    validate_string_list(targets, "build.targets")
    if not targets or len(targets) != len(set(targets)) or not set(targets) <= set(data.get("upstream", {}).get("assets", {})):
        raise ManifestError("build.targets must name distinct configured upstream targets")
    assets = set(data["upstream"]["assets"])
    arch = data.get("arch")
    expected = {arch} if arch else {"arm64", "x86_64"}
    if assets != expected and not (assets == {"universal"} and not arch):
        raise ManifestError("binary fallback assets must cover the declared cask architectures")
    if build.get("signing", "none") not in ("none", "signed", "notarized"):
        raise ManifestError("build.signing must be none, signed or notarized")


def validate_manifest(manifest: Manifest) -> None:
    data = manifest.data
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] not in (1, 2):
        raise ManifestError("expected package manifest schema 1 or 2")
    kind = data.get("kind")
    if kind not in ("cask", "formula"):
        raise ManifestError("kind must be cask or formula")
    validate_mapping(data, COMMON_KEYS | (CASK_KEYS if kind == "cask" else FORMULA_KEYS), "manifest")
    token = data.get("token")
    if not isinstance(token, str) or not TOKEN.fullmatch(token) or manifest.path.stem != token:
        raise ManifestError("token must match the manifest filename")
    if manifest.path.parent != manifest.root / "packages" / MANIFEST_DIRS[kind]:
        raise ManifestError("manifest directory must match its kind")
    if "directory" in data:
        validate_relative_path(data["directory"], "directory")
    validate_string(data.get("desc"), "desc")
    validate_url(data.get("homepage"), "homepage")
    if "url" in data:
        validate_url(data["url"], "url", templated=True)

    channels = data.get("channels")
    validate_mapping(channels, {"stable", "pre"}, "channels")
    if "stable" not in channels:
        raise ManifestError("channels.stable is required")
    for channel, release in channels.items():
        validate_release(release, channel, data.get("url"), kind, data.get("arch"), data["schema"])

    if "upstream" in data:
        validate_upstream(data["upstream"])
    if "build" in data:
        validate_build(manifest)

    if "livecheck" in data:
        livecheck = data["livecheck"]
        validate_mapping(livecheck, {"url", "strategy"}, "livecheck")
        if livecheck.get("url") not in ("url", "homepage"):
            raise ManifestError("livecheck.url must be url or homepage")
        if livecheck.get("strategy") not in ("git", "github_latest"):
            raise ManifestError("unsupported livecheck strategy")

    if kind == "cask":
        validate_string(data.get("name"), "name")
        validate_string(data.get("app"), "app")
        if "macos" in data and type(data["macos"]) is not bool:
            raise ManifestError("macos must be a boolean")
        if "arch" in data and data["arch"] not in ("arm64", "x86_64"):
            raise ManifestError("arch must be arm64 or x86_64")
        if "zap" in data:
            validate_string_list(data["zap"], "zap")
    else:
        for key in ("recipe", "patch"):
            if key == "recipe" or key in data:
                validate_relative_path(data.get(key), key)
                manifest.resolve_recipe(data[key])
        if "license" in data:
            validate_string(data["license"], "license")
        if "depends_on" in data:
            validate_string_list(data["depends_on"], "depends_on")


def load_manifest(path: Path) -> Manifest:
    if path.is_symlink():
        raise ManifestError(f"{path}: a manifest must be a regular file")
    path = path.resolve()
    try:
        source = path.read_text(encoding="utf-8")
        for token in yaml_parser().scan(source):
            if isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise ManifestError("YAML anchors, aliases and tags are unsupported")
        data = yaml_parser().load(source)
        manifest = Manifest(path, path.parent.parent.parent.resolve(), data)
        validate_manifest(manifest)
        return manifest
    except (YAMLError, OSError, ValueError) as exc:
        raise ManifestError(f"{path}: {exc}") from exc


def dump_manifest(manifest: Manifest) -> str:
    output = StringIO()
    yaml_parser().dump(manifest.data, output)
    return output.getvalue()

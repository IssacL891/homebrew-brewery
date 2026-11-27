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
PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
COMMON_KEYS = {"schema", "kind", "token", "directory", "desc", "homepage", "url", "channels", "livecheck"}
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


def validate_release(release, channel: str, fallback_url: str | None) -> None:
    validate_mapping(release, {"version", "sha256", "tag", "url"}, channel)
    for key, pattern in (("version", VERSION), ("sha256", SHA256)):
        value = release.get(key)
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ManifestError(f"{channel}.{key} is invalid")
    if "tag" in release and (not isinstance(release["tag"], str) or not VERSION.fullmatch(release["tag"])):
        raise ManifestError(f"{channel}.tag is invalid")
    if "url" in release:
        validate_url(release["url"], f"{channel}.url")
    elif not fallback_url:
        raise ManifestError(f"{channel} needs a URL or a shared URL template")
    elif "{tag}" in fallback_url and "tag" not in release:
        raise ManifestError(f"{channel}.tag is required by the URL template")


def validate_manifest(manifest: Manifest) -> None:
    data = manifest.data
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != 1:
        raise ManifestError("expected package manifest schema 1")
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
        validate_release(release, channel, data.get("url"))

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

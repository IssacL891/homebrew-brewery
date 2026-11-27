"""Local maintainer commands for Brewery packages."""

import argparse
from pathlib import Path
import sys

from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.manifests import (
    MANIFEST_DIRS,
    TOKEN,
    Manifest,
    ManifestError,
    dump_manifest,
    validate_relative_path,
    yaml_parser,
)
from automation.render import OUTPUT_DIRS


def add_placeholders(data: CommentedMap, fields: dict[str, str]) -> None:
    for key, prompt in fields.items():
        data[key] = None
        data.yaml_add_eol_comment(prompt, key)


def package_template(kind: str, token: str, pre: bool) -> CommentedMap:
    data = CommentedMap(schema=1, kind=kind, token=token)
    if kind == "cask":
        add_placeholders(data, {"name": "App display name"})
    add_placeholders(data, {
        "desc": "Short package description",
        "homepage": "Project homepage URL",
        "url": "Download URL or a template using {version} or {tag}",
    })
    if kind == "cask":
        data["macos"] = True
        add_placeholders(data, {"app": "Exact bundle name, such as My App.app"})
    else:
        add_placeholders(data, {"recipe": "Path to the build recipe under recipes/"})

    if pre:
        upstream = CommentedMap()
        add_placeholders(upstream, {"repository": "GitHub owner/repo"})
        upstream["assets"] = CommentedMap()
        add_placeholders(upstream["assets"], {
            "universal": "Release asset filename or pattern using {tag} or {version}",
        })
        data["upstream"] = upstream

    data["channels"] = CommentedMap()
    for channel in ("stable", "pre") if pre else ("stable",):
        data["channels"][channel] = CommentedMap()
        add_placeholders(data["channels"][channel], {
            "version": 'Quoted release version, such as "1.2.3"',
            "sha256": "SHA-256 of the download for this channel",
        })
    data.yaml_set_start_comment("Fill in the blank values before rendering or committing this manifest.")
    return data


def check_tokens(root: Path, kind: str, tokens: set[str]) -> None:
    manifests = root / "packages" / MANIFEST_DIRS[kind]
    for path in sorted(manifests.rglob("*.yaml")):
        token = path.stem.casefold()
        if token in tokens:
            raise ManifestError(f"{token} already has a manifest at {path.relative_to(root)}")
        if f"{token}-pre" in tokens:
            data = yaml_parser().load(path.read_text(encoding="utf-8"))
            channels = data.get("channels", {}) if isinstance(data, dict) else {}
            if not isinstance(channels, dict) or "pre" in channels:
                raise ManifestError(f"check {path.relative_to(root)} before using {token}-pre")

    for path in sorted((root / OUTPUT_DIRS[kind]).rglob("*.rb")):
        if path.stem.casefold() in tokens:
            raise ManifestError(f"{path.stem} already has Ruby at {path.relative_to(root)}")


def new_package(root: Path, kind: str, token: str, category: str | None, pre: bool, write: bool) -> None:
    if not TOKEN.fullmatch(token) or (kind == "formula" and not token[0].isalpha()):
        raise ManifestError("use a lowercase package token with letters, digits, and hyphens")
    if category is not None:
        validate_relative_path(category, "category")

    root = root.resolve()
    destination = root / "packages" / MANIFEST_DIRS[kind] / (category or "") / f"{token}.yaml"
    template = dump_manifest(Manifest(destination, root, package_template(kind, token, pre)))
    if not write:
        sys.stdout.write(template)
        return

    if destination.resolve() != destination:
        raise ManifestError("package destination crosses a symlink")
    tokens = {token, f"{token}-pre"} if pre else {token}
    check_tokens(root, kind, tokens)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(template)
    print(f"Created {destination.relative_to(root)}. Fill it in, then run automation/render.py.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    subcommands = parser.add_subparsers(dest="command", required=True)
    new = subcommands.add_parser("new", help="Create a fill-in-the-blanks package manifest.")
    new.add_argument("kind", choices=MANIFEST_DIRS)
    new.add_argument("token", help="The unique Homebrew package token.")
    new.add_argument("--category", help="Optional path below the package directory.")
    new.add_argument("--pre", action="store_true", help="Include a prerelease channel.")
    new.add_argument("--write", action="store_true", help="Create the manifest instead of printing it.")
    args = parser.parse_args()
    try:
        new_package(args.root, args.kind, args.token, args.category, args.pre, args.write)
    except (ManifestError, OSError, YAMLError, UnicodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

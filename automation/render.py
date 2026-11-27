"""Generate standalone Homebrew package definitions from YAML."""

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.manifests import Manifest, ManifestError, load_manifest


MARKER = "# Generated from "
OUTPUT_DIRS = {"cask": "Casks", "formula": "Formula"}


def ruby_string(value: str) -> str:
    escaped = json.dumps(value, ensure_ascii=False)
    # JSON uses the same simple escapes; unlike JSON, Ruby also interpolates '#'.
    return escaped.replace("#{", r"\#{").replace("#@", r"\#@").replace("#$", r"\#$")


def ruby_url(data: dict, release: dict) -> str:
    if "url" in release:
        return ruby_string(release["url"])
    template = data["url"]
    if "tag" in release:
        template = template.replace("{tag}", release["tag"])
    if data["kind"] == "cask":
        return ruby_string(template).replace("{version}", "#{version}")
    return ruby_string(template.replace("{version}", release["version"]))


def livecheck_stanzas(data: dict) -> list[str]:
    if "livecheck" not in data:
        return []
    livecheck = data["livecheck"]
    return ["", "  livecheck do", f"    url :{livecheck['url']}", f"    strategy :{livecheck['strategy']}", "  end"]


def render_cask(data: dict, token: str, release: dict, sibling: str | None) -> list[str]:
    lines = [
        f"cask {ruby_string(token)} do",
        f"  version {ruby_string(release['version'])}",
        f"  sha256 {ruby_string(release['sha256'])}",
        "",
        f"  url {ruby_url(data, release)}",
        f"  name {ruby_string(data['name'])}",
        f"  desc {ruby_string(data['desc'])}",
        f"  homepage {ruby_string(data['homepage'])}",
        *livecheck_stanzas(data),
    ]
    if sibling:
        lines.extend(["", f"  conflicts_with cask: {ruby_string(sibling)}"])
    if "arch" in data or data.get("macos"):
        lines.append("")
        if "arch" in data:
            lines.append(f"  depends_on arch: :{data['arch']}")
        if data.get("macos"):
            lines.append("  depends_on :macos")
    lines.extend(["", f"  app {ruby_string(data['app'])}"])
    zap = data.get("zap", [])
    if zap:
        trash = ruby_string(zap[0]) if len(zap) == 1 else f"[{', '.join(map(ruby_string, zap))}]"
        lines.extend(["", f"  zap trash: {trash}"])
    return [*lines, "end"]


def render_formula(manifest: Manifest, token: str, release: dict, sibling: str | None) -> list[str]:
    data = manifest.data
    class_name = "".join(word.capitalize() for word in token.split("-"))
    if not class_name[0].isalpha():
        raise ManifestError(f"{manifest.path}: formula token must start with a letter")
    lines = [
        f"class {class_name} < Formula",
        f"  desc {ruby_string(data['desc'])}",
        f"  homepage {ruby_string(data['homepage'])}",
        f"  url {ruby_url(data, release)}",
        f"  version {ruby_string(release['version'])}",
        f"  sha256 {ruby_string(release['sha256'])}",
    ]
    if "license" in data:
        lines.append(f"  license {ruby_string(data['license'])}")
    lines.extend(livecheck_stanzas(data))
    if sibling:
        lines.extend(["", f"  conflicts_with {ruby_string(sibling)}, because: \"both install the same package\""])
    dependencies = data.get("depends_on", [])
    if dependencies:
        lines.extend(["", *(f"  depends_on {ruby_string(dep)}" for dep in dependencies)])
    if "patch" in data:
        lines.extend(["", "  patch :DATA"])
    recipe = manifest.resolve_recipe(data["recipe"]).read_text(encoding="utf-8")
    lines.extend(["", *(f"  {line}" if line else "" for line in recipe.splitlines()), "end"])
    if "patch" in data:
        patch = manifest.resolve_recipe(data["patch"]).read_text(encoding="utf-8")
        lines.extend(["", "__END__", *patch.splitlines()])
    return lines


def render_manifest(manifest: Manifest) -> dict[Path, str]:
    data = manifest.data
    base = data["token"]
    paired = "pre" in data["channels"]
    outputs = {}
    for channel, release in data["channels"].items():
        token = f"{base}-pre" if channel == "pre" else base
        sibling = (base if channel == "pre" else f"{base}-pre") if paired else None
        output = Path(OUTPUT_DIRS[data["kind"]]) / data.get("directory", "") / f"{token}.rb"
        if data["kind"] == "cask":
            body = render_cask(data, token, release, sibling)
        else:
            body = render_formula(manifest, token, release, sibling)
        marker = f"{MARKER}{manifest.path.relative_to(manifest.root)}. Edit the YAML and regenerate."
        outputs[output] = "\n".join([marker, "", *body, ""])
    return outputs


def render_tree(root: Path, check: bool) -> list[Path]:
    root = root.resolve()
    outputs = {}
    claimed = set()
    errors = []
    for path in sorted((root / "packages").glob("*/*.yaml")):
        for output, content in render_manifest(load_manifest(path)).items():
            if str(output).casefold() in claimed:
                raise ManifestError(f"duplicate output: {output}")
            claimed.add(str(output).casefold())
            outputs[output] = content

    for output, content in outputs.items():
        path = root / output
        if path.resolve() != path:
            raise ManifestError(f"output traverses a symlink: {output}")
        if path.is_file() and path.read_bytes() == content.encode("utf-8"):
            continue
        if check:
            errors.append(output)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")

    for directory in OUTPUT_DIRS.values():
        for path in (root / directory).rglob("*.rb"):
            relative = path.relative_to(root)
            if relative not in outputs:
                with path.open(encoding="utf-8") as stream:
                    if stream.readline().startswith(MARKER):
                        errors.append(relative)
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check for drift without writing files.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors = render_tree(args.root, args.check)
    except (ManifestError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for path in errors:
        print(f"Missing, changed, or orphaned generated file: {path}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())

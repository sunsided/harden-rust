#!/usr/bin/env python3
"""Pin GitHub Actions `uses:` references to full commit SHAs, in place.

    python3 pin-actions.py .github/workflows/*.yml

Resolves every `owner/repo[/path]@ref` that is not already a 40-character SHA through `gh api`,
rewrites it to `@<sha> # <most specific tag>` and leaves local (`./`) and `docker://` uses alone.
For dtolnay/rust-toolchain, whose ref names the toolchain, it adds an explicit `toolchain:` input.
Requires an authenticated `gh` CLI.
"""

import json
import re
import subprocess
import sys
from functools import cache

USES = re.compile(
    r"^(?P<indent>\s*)(?P<dash>-\s+)?uses:\s*"
    r"(?P<repo>[\w.-]+/[\w.-]+)(?P<path>/[^@\s]*)?@(?P<ref>[^\s#]+)(?P<comment>\s*#.*)?$"
)
SHA = re.compile(r"^[0-9a-f]{40}$")


def gh_json(endpoint):
    """Call `gh api` with pagination and return the parsed JSON (pages merged for lists)."""
    out = subprocess.check_output(
        ["gh", "api", "--paginate", "--slurp", endpoint], text=True, stderr=subprocess.DEVNULL
    )
    pages = json.loads(out)

    if isinstance(pages[0], list):
        return [item for page in pages for item in page]

    return pages[0]


def version_key(tag):
    """Sort key that orders `v1.10.0` after `v1.9.0`."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", tag)]


@cache
def tags_of(repo):
    """Return {tag name: commit SHA} for a repository."""
    return {t["name"]: t["commit"]["sha"] for t in gh_json(f"repos/{repo}/tags?per_page=100")}


@cache
def resolve(repo, ref):
    """Return (commit SHA, comment label) for a ref of a repository.

    A floating ref such as `v0.5` that is not itself a tag or branch resolves to the newest
    `v0.5.*` tag.
    """
    tags = tags_of(repo)

    try:
        sha = gh_json(f"repos/{repo}/commits/{ref}")["sha"]
    except subprocess.CalledProcessError:
        newer = sorted((t for t in tags if t.startswith(ref + ".")), key=version_key)

        if not newer:
            raise

        return tags[newer[-1]], newer[-1]

    # Prefer the most specific tag on the same commit that extends the requested ref (v6 -> v6.0.1).
    same = [t for t, s in tags.items() if s == sha]
    matching = sorted((t for t in same if t.startswith(ref)), key=version_key)
    label = matching[-1] if matching else ref

    return sha, label


def newer_major(repo, label):
    """Return the newest release tag of a higher major version than `label`, if any."""
    match = re.match(r"v?(\d+)", label)

    if not match:
        return None

    current = int(match.group(1))
    releases = [t for t in tags_of(repo) if re.fullmatch(r"v?\d+\.\d+\.\d+", t)]
    higher = [t for t in releases if int(re.match(r"v?(\d+)", t).group(1)) > current]

    return max(higher, key=version_key) if higher else None


def step_lines(lines, start, key_indent):
    """Yield indices of the lines that belong to the step whose first line is `start`."""
    for index in range(start + 1, len(lines)):
        text = lines[index]
        indent = len(text) - len(text.lstrip())

        if text.strip() and indent < key_indent:
            return

        yield index


def toolchain_input(lines, start, key_indent, toolchain):
    """Ensure the step at `start` passes `toolchain:` in its `with:` block."""
    pad = " " * key_indent

    for index in step_lines(lines, start, key_indent):
        if lines[index].startswith(pad + "with:") and lines[index].strip() != "with:":
            if "toolchain" not in lines[index]:
                print(f"warning: line {index + 1}: inline `with:` mapping; add `toolchain: {toolchain}` by hand")

            return

        if lines[index].startswith(pad + "with:"):
            block = list(step_lines(lines, index, key_indent + 1))

            if not any(lines[i].strip().startswith("toolchain:") for i in block):
                lines.insert(index + 1, f"{pad}  toolchain: {toolchain}\n")

            return

    lines.insert(start + 1, f"{pad}with:\n{pad}  toolchain: {toolchain}\n")


def pin_file(path):
    """Pin every unpinned action in one workflow file; return the number of changes."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.readlines()

    changes = 0
    index = 0

    while index < len(lines):
        match = USES.match(lines[index].rstrip("\n"))
        index += 1

        if not match or SHA.match(match["ref"]):
            continue

        repo, ref = match["repo"], match["ref"]
        sha, label = resolve(repo, ref)
        newer = newer_major(repo, label)

        if newer:
            print(f"note: {repo} {label} pinned; newer major available: {newer} (check its changelog)")

        dash = match["dash"] or ""
        lines[index - 1] = f"{match['indent']}{dash}uses: {repo}{match['path'] or ''}@{sha} # {label}\n"
        changes += 1

        if repo == "dtolnay/rust-toolchain":
            toolchain_input(lines, index - 1, len(match["indent"]) + len(dash), ref)

    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)

    return changes


def main():
    """Entry point."""
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    for path in sys.argv[1:]:
        print(f"{path}: pinned {pin_file(path)} action(s)")


if __name__ == "__main__":
    main()

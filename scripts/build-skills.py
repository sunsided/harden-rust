#!/usr/bin/env python3
"""Package each skill under skills/ into a reproducible dist/<name>-<version>.skill bundle.

A .skill bundle is a zip with the skill folder at its root, as Claude expects. Only files
tracked by git are packed, read from the working tree. The version comes from the
`version:` key in the skill's SKILL.md frontmatter. Entries are sorted and stamped with the
last commit time (or SOURCE_DATE_EPOCH), so the same tree yields the same bytes.

The build fails when a name exceeds 64 characters or a description exceeds 1024, the
limits Claude enforces on upload.
"""

import hashlib
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DIST = Path(os.environ.get("DIST_DIR", ROOT / "dist"))


def git(*args: str) -> str:
    """Run git in the repository root and return its stdout."""
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def frontmatter(skill_md: Path) -> dict[str, str]:
    """Return the top-level frontmatter keys of a SKILL.md, with folded values joined."""
    match = re.match(r"---\n(.*?)\n---\n", skill_md.read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        sys.exit(f"error: {skill_md.relative_to(ROOT)} has no frontmatter")

    fields: dict[str, list[str]] = {}
    key = None
    for line in match.group(1).splitlines():
        top = re.match(r"([A-Za-z][\w-]*):\s*(.*)", line)
        if top:
            key = top.group(1)
            value = top.group(2)
            fields[key] = [] if value in {">", ">-", "|", "|-"} else [value]
        elif key is not None:
            fields[key].append(line.strip())

    return {k: " ".join(v).strip().strip("\"'") for k, v in fields.items()}


def check_upload_limits(skill: str, fields: dict[str, str]) -> None:
    """Exit with an error when the name or description exceeds Claude's upload limits."""
    name_len = len(fields.get("name", ""))
    desc_len = len(fields.get("description", ""))
    if not 0 < name_len <= 64:
        sys.exit(f"error: {skill}: name is {name_len} chars (1-64 allowed)")
    if not 0 < desc_len <= 1024:
        sys.exit(f"error: {skill}: description is {desc_len} chars (1-1024 allowed)")


def build(skill_dir: Path, epoch: int) -> Path:
    """Write the bundle for one skill folder and its .sha256 file, returning the bundle path."""
    skill = skill_dir.name
    fields = frontmatter(skill_dir / "SKILL.md")
    if fields.get("name") != skill:
        sys.exit(f"error: {skill}: frontmatter name {fields.get('name')!r} does not match its folder")
    version = fields.get("version")
    if not version:
        sys.exit(f"error: {skill}: SKILL.md has no version key")
    check_upload_limits(skill, fields)

    files = sorted(git("ls-files", "-z", "--", f"skills/{skill}").split("\0")[:-1])
    stamp = time.gmtime(epoch)[:6]
    out = DIST / f"{skill}-{version}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as bundle:
        for rel in files:
            path = ROOT / rel
            info = zipfile.ZipInfo(str(path.relative_to(SKILLS)), date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Keep exec bits so bundled scripts stay runnable; drop everything else.
            info.external_attr = (0o100755 if os.access(path, os.X_OK) else 0o100644) << 16
            bundle.writestr(info, path.read_bytes())

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_name(out.name + ".sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    return out


def main() -> None:
    """Build a bundle for every skill folder."""
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH") or git("log", "-1", "--format=%ct"))
    DIST.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(p.parent for p in SKILLS.glob("*/SKILL.md")):
        print(build(skill_dir, epoch))


if __name__ == "__main__":
    main()

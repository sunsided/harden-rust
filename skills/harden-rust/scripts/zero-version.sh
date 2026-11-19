#!/bin/sh
# Reset the committed version to 0.0.0 so CI can stamp the GitVersion one with `cargo set-version`.
#
#   sh scripts/zero-version.sh [Cargo.toml]
#
# `cargo set-version` refuses to move a version backwards, and it compares pre-release
# identifiers as SemVer strings: a CI version such as 1.4.0-PullRequest12.3 sorts *below*
# the committed 1.4.0-alpha (uppercase precedes lowercase), so stamping it would fail.
# Zeroing first makes every stamped version an upgrade.
#
# Edits `version` in [workspace.package] when present (members inherit it via
# version.workspace = true), otherwise in [package]. Touches nothing else; safe to run twice.
set -eu

manifest="${1:-Cargo.toml}"

if [ ! -f "$manifest" ]; then
  echo "error: $manifest not found; run from the repository root" >&2
  exit 1
fi

if grep -q '^\[workspace\.package\]' "$manifest"; then
  section='[workspace.package]'
else
  section='[package]'
fi

awk -v section="$section" '
  /^\[/ { inside = ($0 == section) }
  inside && /^version[[:space:]]*=/ { print "version = \"0.0.0\""; patched = 1; next }
  { print }
  END { if (!patched) exit 3 }
' "$manifest" > "$manifest.tmp" || {
  rm -f "$manifest.tmp"
  echo "error: no version key in $section of $manifest" >&2
  exit 1
}

mv "$manifest.tmp" "$manifest"
echo "reset $section version in $manifest to 0.0.0"

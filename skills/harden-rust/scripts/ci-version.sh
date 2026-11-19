#!/bin/sh
# Print the version a CI build should carry, from GitVersion's output.
#
#   version="$(sh scripts/ci-version.sh)"                  # crate version, for cargo set-version
#   info="$(sh scripts/ci-version.sh --informational)"    # adds +PullRequestN on PR builds
#
# Outside pull requests this is GitVersion's SemVer: X.Y.Z-alpha.N, X.Y.Z-beta.N or X.Y.Z.
# For pull requests GitVersion would produce X.Y.Z-PullRequest12.3, which buries the PR in the
# pre-release label. This keeps the label of the branch the PR targets instead: X.Y.Z-alpha.3.
# --informational appends the PR as build metadata (X.Y.Z-alpha.3+PullRequest12) for places a
# human reads (binary --version, image labels); crate versions never carry metadata.
#   base develop, or main in GitHub Flow         -> alpha
#   base release/*, hotfix/*, or main in Git Flow -> beta
# PR builds stay CI artifacts and are never published.
#
# Inputs: GitVersion_SemVer, GitVersion_MajorMinorPatch, GitVersion_PreReleaseNumber (from the
# execute action), GITHUB_BASE_REF and GITHUB_REF (set by Actions), BRANCH_FLOW (github|gitflow).
set -eu

informational=false
[ "${1:-}" = --informational ] && informational=true

if [ -z "${GITHUB_BASE_REF:-}" ]; then
  printf '%s\n' "$GitVersion_SemVer"
  exit 0
fi

pr="$(printf '%s' "${GITHUB_REF:-}" | sed -n 's#^refs/pull/\([0-9][0-9]*\)/.*#\1#p')"

case "${BRANCH_FLOW:-github}:$GITHUB_BASE_REF" in
  *:release/* | *:hotfix/* | gitflow:main) label=beta ;;
  *) label=alpha ;;
esac

# A PR into release/X.Y.Z or hotfix/X.Y.Z belongs to that version; GitVersion cannot see the
# PR's target and would report the develop line instead.
core="$(printf '%s' "$GITHUB_BASE_REF" | sed -nE 's#^(release|hotfix)/v?([0-9]+\.[0-9]+\.[0-9]+)$#\2#p')"

version="${core:-$GitVersion_MajorMinorPatch}-$label.${GitVersion_PreReleaseNumber:-0}"

if [ "$informational" = true ]; then
  version="$version+PullRequest${pr:-0}"
fi

printf '%s\n' "$version"

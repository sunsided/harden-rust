#!/usr/bin/env python3
"""Report and optionally configure crates.io trusted publishing for every publishable crate.

Read-only by default. Lists the publishable workspace crates, checks which exist on crates.io,
whether an existing crate of that name belongs to this repository (its `repository` field) or to
someone else, and (when CARGO_REGISTRY_TOKEN is set) which already have a GitHub
trusted-publishing config.

    python3 trusted-publishing.py [--workflow publish-crates-io.yml] [--environment crates-io] [--apply]

--apply creates the missing configs through the crates.io API after a confirmation prompt.
The token needs the `trusted-publishing` endpoint scope for the affected crates.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://crates.io/api/v1"
USER_AGENT = "harden-rust-skill trusted-publishing helper"


def publishable_crates():
    """Return the names of workspace crates that may be published to crates.io."""
    meta = json.loads(
        subprocess.check_output(["cargo", "metadata", "--no-deps", "--format-version", "1"])
    )

    # `publish` is null (any registry) or a list of allowed registries; [] means publish = false.
    return [
        pkg["name"]
        for pkg in meta["packages"]
        if pkg["publish"] is None or "crates-io" in pkg["publish"]
    ]


def github_repo():
    """Return (owner, repo) parsed from the `origin` remote URL."""
    url = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    match = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?$", url)

    if not match:
        sys.exit(f"origin is not a GitHub remote: {url}")

    return match.group(1), match.group(2)


def request(method, path, token=None, body=None):
    """Call the crates.io API and return (status, parsed JSON or None)."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    if token:
        headers["Authorization"] = token

    data = None

    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        return err.code, None


def existing_configs(crate, token):
    """Return the GitHub trusted-publishing configs of a crate, or None if they are not readable."""
    status, data = request("GET", f"/trusted_publishing/github_configs?crate={crate}", token)
    return data["github_configs"] if status == 200 else None


def config_matches(cfg, owner, repo, workflow, environment):
    """Tell whether an existing config already targets this repository and workflow."""
    return (
        cfg["repository_owner"].lower() == owner.lower()
        and cfg["repository_name"].lower() == repo.lower()
        and cfg["workflow_filename"] == workflow
        and (cfg["environment"] or None) == environment
    )


def same_repository(url, owner, repo):
    """Tell whether a crates.io `repository` URL points at owner/repo on GitHub."""
    match = re.search(r"github\.com[:/]([^/]+)/([^/#?]+?)(?:\.git)?/?$", url or "")
    return bool(match) and (match.group(1).lower(), match.group(2).lower()) == (owner.lower(), repo.lower())


def classify(crate, owner, repo, args, token):
    """Return the status string for one crate."""
    status, data = request("GET", f"/crates/{crate}")

    if status == 404:
        return "unpublished"

    if status != 200:
        return f"error (HTTP {status})"

    remote = data["crate"].get("repository")

    if not same_repository(remote, owner, repo):
        return f"name taken (crates.io repository: {remote or 'none'}); rename or confirm ownership"

    if not token:
        return "published (set CARGO_REGISTRY_TOKEN to check config)"

    configs = existing_configs(crate, token)

    if configs is None:
        return "published (config not readable with this token)"

    if any(config_matches(c, owner, repo, args.workflow, args.environment) for c in configs):
        return "configured"

    return "missing"


def create_config(crate, owner, repo, args, token):
    """Create the trusted-publishing config for one crate and report the result."""
    body = {
        "github_config": {
            "crate": crate,
            "repository_owner": owner,
            "repository_name": repo,
            "workflow_filename": args.workflow,
            "environment": args.environment,
        }
    }
    status, _ = request("POST", "/trusted_publishing/github_configs", token, body)
    print(f"  {crate}: {'created' if status in (200, 201) else f'FAILED (HTTP {status})'}")


def print_manual_steps(missing, unpublished, owner, repo, args):
    """Print the steps that still need a human."""
    if unpublished:
        print("\nFirst publish (manual, with a short-lived token scoped to publish-new):")
        print("  cargo publish " + " ".join(f"-p {c}" for c in unpublished))
        print("  (cargo orders multi-package publishes by dependency)")
        print("\nAfter the first publish, rerun this script to configure trusted publishing for them.")

    if missing:
        print("\nTrusted publishing config, per crate (web UI, or rerun with --apply):")

        for crate in missing:
            print(f"  https://crates.io/crates/{crate}/settings")

        env = args.environment or "(leave empty)"
        print(f"  owner={owner} repo={repo} workflow={args.workflow} environment={env}")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workflow", default="publish-crates-io.yml")
    parser.add_argument("--environment", default="crates-io")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("CARGO_REGISTRY_TOKEN")
    owner, repo = github_repo()
    crates = publishable_crates()
    statuses = {crate: classify(crate, owner, repo, args, token) for crate in crates}

    print(f"Repository {owner}/{repo}, workflow {args.workflow}\n")

    for crate, status in statuses.items():
        print(f"  {crate:<32} {status}")

    missing = [c for c, s in statuses.items() if s == "missing"]
    unpublished = [c for c, s in statuses.items() if s == "unpublished"]

    if args.apply and missing:
        answer = input(f"\nCreate {len(missing)} trusted-publishing config(s) on crates.io? [y/N] ")

        if answer.strip().lower() == "y":
            for crate in missing:
                create_config(crate, owner, repo, args, token)

            missing = []

    print_manual_steps(missing, unpublished, owner, repo, args)


if __name__ == "__main__":
    main()

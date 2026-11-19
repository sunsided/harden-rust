# crates.io trusted publishing

Trusted publishing lets the publish workflow exchange its GitHub OIDC token for a
short-lived crates.io token. There is no long-lived `CARGO_REGISTRY_TOKEN` secret.
`publish-crates-io.yml` does the exchange with `rust-lang/crates-io-auth-action`, in the `crates-io`
environment (`docs/release.md`, `docs/github.md`).

## Constraints

- **The first publish is manual.** A crate must exist on crates.io before it can get a
  trusted-publishing config. Publish it once from a machine, with a short-lived API token
  scoped to `publish-new`. Revoke the token afterwards.
- **One config per crate.** Each config names the GitHub owner, the repo, the workflow
  **filename** (`publish-crates-io.yml`) and the environment (`crates-io`). If any of these changes, for
  example after a workflow rename or a repo transfer, publishing breaks until the config is
  updated.
- Only crate owners can add configs.

## Aid for large workspaces

`scripts/trusted-publishing.py` (run it from the repo root):

```sh
python3 <skill>/scripts/trusted-publishing.py                    # read-only status report
CARGO_REGISTRY_TOKEN=... python3 <skill>/scripts/trusted-publishing.py          # also checks existing configs
CARGO_REGISTRY_TOKEN=... python3 <skill>/scripts/trusted-publishing.py --apply  # creates the missing configs (asks first)
```

- It lists the publishable crates from `cargo metadata`, and reads owner and repo from `origin`.
- For each crate it reports one of these states:
  - `unpublished`;
  - `name taken`: the crates.io crate of that name points at another repository. Rename it,
    or have the user confirm ownership;
  - `missing`: published, no matching config;
  - `configured`.
- Unpublished crates: it prints a single `cargo publish -p a -p b ...` command. Current cargo
  publishes several packages in dependency order; on an old toolchain, publish dependencies
  first. Run it only after the user confirms.
- `--apply` calls `POST /api/v1/trusted_publishing/github_configs`. Ask the user before you run
  it. Have the user create the token at https://crates.io/settings/tokens with the
  **`trusted-publishing`** endpoint scope, limited to these crates, and a short expiry.
  The user sets the token in their own shell. Never ask them to paste it into the chat.

## Manual way (web UI)

For each crate, open `https://crates.io/crates/<crate>/settings`, go to Trusted Publishing,
then Add, and enter: owner, repo, workflow `publish-crates-io.yml`, environment `crates-io`.

## After setup

- Remove any old `CARGO_REGISTRY_TOKEN` repo secret.
- Optional: in each crate's settings, require trusted publishing only (`trustpub_only`), so
  that token uploads are rejected.

Sources: crates.io OpenAPI (https://crates.io/api/openapi.json, paths
`/api/v1/trusted_publishing/*`, endpoint scope `trusted-publishing`),
https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07/,
https://release-plz.dev/docs/github/quickstart

# Supply chain

## cargo-deny

- Template: `templates/deny.toml`. If the repo already has a `deny.toml`, merge the license
  allowlist into it and keep everything else.
- The license allowlist must contain the project's own licenses, plus `CC0-1.0` when examples
  are CC0 (`docs/licensing.md`).
- `wildcards = "deny"` together with `allow-wildcard-paths = true`. Publishable crates need
  `version = "..."` on path dependencies anyway.
- Run it with `task deny`. CI uses `EmbarkStudios/cargo-deny-action`.
- An advisory `ignore` entry needs `{ id = "RUSTSEC-...", reason = "..." }` and the user's OK.

## Dependabot

- Template: `templates/.github/dependabot.yml`. It covers the cargo ecosystem (root, plus
  `/fuzz` when present) and github-actions.
- **Group by ecosystem, then by size.** Each ecosystem has one group for `major` updates and
  one for `minor` + `patch`. A breaking upgrade gets its own PR, and routine bumps arrive
  together.
- **Commit prefix = ecosystem name** (`Cargo`, `Actions`, `npm`, `Docker`), giving subjects
  like "Cargo: Bump serde from 1.0.1 to 1.0.2". Never `deps:` or `chore:`. release-plz files
  `Cargo:` / `npm:` bumps under Dependencies and skips `Actions:` (CI-only) in changelogs.
- **Cadence follows zizmor.** `cooldown.default-days: 7` is zizmor's `dependabot-cooldown`
  recommendation, and it limits exposure to freshly compromised releases. If the repo
  configures a stricter zizmor threshold, use that. The schedule is weekly.
- Dependabot updates SHA-pinned actions and their `# vX.Y.Z` comments.
- Remove `/fuzz` from `directories` when the repo has no fuzz crate.
- Add ecosystems for what the repo contains: `docker` (Dockerfiles), `npm` (the web
  frontend's directory, which also covers yarn), each with the same cooldown and grouping.
- Dependabot's default commit subjects ("Bump x from 1 to 2") are imperative already.
  Its branches (`dependabot/...`) are the allowed bot exception to the branching model.

## cargo-semver-checks

- release-plz runs it on release PRs by default (`semver_check = true`).
- CI also runs it on PRs (`semver` job), so breaking changes show up before the release PR.
- It needs a published baseline, so new crates fail until their first publish.
- Locally: `task semver`.

## MSRV

- Every publishable crate declares `rust-version`. In a workspace, put it in
  `[workspace.package]` and set `rust-version.workspace = true` per member, unless crates
  differ.
- When it is missing, ask the user. Recommend the **lowest version that works**, so the
  crate stays usable on older toolchains. That is at least the edition's minimum (2024
  needs 1.85, 2021 needs 1.56), raised by what the dependencies declare. `cargo msrv find`
  confirms it when installed; otherwise check with `cargo +<version> check --all-targets`.
  The second option is the newest stable, for apps that do not care.
- Single crate: put `rust-version` in `[package]`.
- Check it with `cargo hack check --rust-version --workspace --all-targets --ignore-private`.
  cargo-hack reads each crate's `rust-version` and installs that toolchain through rustup, so
  there is a single source of truth.
- **MSRV is a signal, not a contract.** Start as low as it costs nothing, because that is
  friendly to the ecosystem. Raising it is fine whenever a dependency update needs it or a
  newer language or std feature makes the code meaningfully better. Development happens on
  current stable anyway.
  - Do not hold dependencies back, or contort code, just to keep an old MSRV.
  - Raise it in a minor release, and say so in the changelog.
  - The `msrv` CI job keeps the declared value honest. It never blocks a deliberate raise.

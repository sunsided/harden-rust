---
name: harden-rust
description: >
  Use when the user wants to harden, bootstrap, audit or "productionize" a Rust repository:
  Taskfile tasks, GitHub Actions CI (actionlint, zizmor, SHA pinning), codecov, pedantic clippy
  and doc-comment lints, forbid(unsafe_code), cargo-deny, Dependabot, MSRV and semver checks,
  typos, git hooks (prek), fuzz/proptest/benchmark scaffolding, licensing (EUPL/MPL or
  MIT/Apache, REUSE), README badges and doctests, mermaid diagrams on docs.rs, crate and GitHub
  metadata, branching model and commit style, repo settings, rulesets and deployment
  environments, Copilot review rules and a REVIEW.md registry, CONTRIBUTING.md, WASM targets
  (wasm-bindgen, wasm-pack, trunk, WASI) with SvelteKit/Vite/yarn frontends, release binaries
  with cargo auditable, SBOMs and attestations, and releases with release-plz and crates.io
  trusted publishing, including multi-crate workspaces. Trigger on "harden this repo",
  "set up CI for my crate", "prepare this crate for crates.io", "add release automation",
  "set up trusted publishing", "make this repo production ready", "audit my Rust project
  setup", even without the word "harden". Skip for writing or reviewing Rust code itself
  (use rust-style) and for non-Rust projects.
version: 0.2.0
tags: [rust, ci, github-actions, release, crates-io, hardening]
execution:
  plan:
    allow: [inspect repository, run read-only cargo/git/gh commands, draft changes]
    deny: [create or mutate files, publish, push]
  code:
    allow: [create and update repository files, refactor code per rust-style, commit on a feature branch]
    deny: [publish crates, push, change GitHub or crates.io settings without explicit confirmation]
---

# Harden Rust

Bring a Rust repository to a strict, consistent baseline. The work happens in fixed phases.
Templates live in `templates/`, scripts in `scripts/`, and deep dives in `docs/`. `<skill>`
below means this skill's directory.

## Prime directives

1. **Inventory before editing.** Never overwrite an existing file wholesale. Merge into
   existing workflows, Taskfiles and configs, and keep their file names. Keep tasks, jobs and
   settings that the template does not know about. Show the intended diff before you write.
2. **Ask instead of guessing.** Use the AskUserQuestion tool at every decision point below.
   Put the recommended option first. Do not ask about what the repo already answers.
3. **Fix, do not suppress.** Lint findings get fixed in code. Never write `#[allow]` or a
   crate-level suppression. A scoped `#[expect(lint, reason = "...")]` is allowed only where
   the lint is wrong for that spot.
4. **Never write versions or SHAs from memory.** That covers action SHAs, hook revs, the
   mermaid version and license texts. Resolve them at apply time with the commands named in
   the docs.
5. **Nothing leaves the machine without confirmation.** Confirm that exact action first for:
   `cargo publish`, a push, `gh repo create` or `gh repo edit`, GitHub settings, rulesets,
   environments, and crates.io config.
6. **Follow the repo's own conventions; otherwise the baseline** (`docs/github.md`).
   - Read CONTRIBUTING.md first. Where it differs from the baseline, CONTRIBUTING.md wins.
   - Do this skill's work on a `feature/harden-<area>` branch. The branching model is GitHub
     Flow or Git Flow. Never use `chore/`, `fix/` or `deps/` branches.
   - Commit messages are imperative ("Add CI workflow"), never `chore: ...`.
7. **Code style is a separate skill.** Load `rust-style` before you write or refactor Rust.

## Decision points (always AskUserQuestion)

| Phase | Question | Doc |
|---|---|---|
| 2 | Branching model (GitHub Flow / Git Flow), if not evident | `github.md` |
| 2 | Commit style when history uses another convention (e.g. Conventional Commits) and CONTRIBUTING.md is silent | `github.md` |
| 2 | Non-conforming branches: rename locally (remote renames are outward-facing) or leave | `github.md` |
| 2 | License scheme; CC0 examples (only if `examples/` exists) | `licensing.md` |
| 2 | Versioning mode: release-plz (libraries, per-crate) or GitVersion (apps, Git Flow, shared version, alpha/beta/stable) | `versioning.md` |
| 2 | Which crates publish; renaming names taken on crates.io | `release.md` |
| 2 | Per-crate versions when `version.workspace = true` | `release.md` |
| 2 | MSRV when `rust-version` is missing (recommend the lowest that works; a signal, raisable) | `supply-chain.md` |
| 2 | Fuzz targets, proptest properties, benches | `testing.md` |
| 2 | Crates allowed to use unsafe (only if any is found) | `lints.md` |
| 2 | Binary targets to ship (musl always included) | `binaries.md` |
| 2 | WASM targets; npm publishing | `wasm.md` |
| 2 | Review setup: light or `docs/review/` registry | `review.md` |
| 2 | Hooks: prek (default) or pre-commit, if the repo already uses one | `automation.md` |
| 2 | Metadata that deviates strongly; dead relative README links | `metadata.md`, `readme.md` |
| 2 | Lint backlog over ~200 findings: fix all now, or stage it | below |
| 3 | Each conflict with an existing user file or task | `taskfile.md`, `ci.md` |
| 3 | `gh repo edit`, repo settings, rulesets, environments | `github.md`, `metadata.md` |
| 6 | Trusted-publishing configs through the crates.io API | `trusted-publishing.md` |

## Phase 1: Inventory (read-only)

Collect facts and print them as a gap table (area, current state, target, action).

- `cargo metadata --no-deps --format-version 1`:
  - single crate or workspace, and members;
  - target kinds (lib, bin, cdylib);
  - `publish`, `version`, `rust-version`, `edition`;
  - metadata fields (`docs/metadata.md`).
  - Flag `version.workspace = true`.
- `python3 <skill>/scripts/trusted-publishing.py`: which crate names are free, published, or
  **taken by another repository**.
- Config: `[lints]` / `[workspace.lints]`, `clippy.toml`, `rustfmt.toml`, `deny.toml`,
  `_typos.toml`, `REUSE.toml`, `LICENSES/`, `.gitignore`. Check that `Cargo.lock` is tracked.
- Automation:
  - `.github/workflows/*`, `.github/dependabot.yml`, `.github/instructions/`;
  - `release-plz.toml` / `release.toml`;
  - `Taskfile*` and its includes;
  - `.pre-commit-config.yaml`, `fuzz/`, `benches/`, proptest, `Dockerfile`.
- Versioning: `GitVersion.yml` (`workflow:` at the top level means the v6 format, kept pinned
  to 6.x; `calculation:` means v7), `release-plz.toml`, `release.toml`, and how CI stamps
  versions (`cargo set-version`).
- Conventions: CONTRIBUTING.md, REVIEW.md, `docs/review/`, CLAUDE.md / AGENTS.md. For the
  branches, run `git branch -a`: a `develop` branch means Git Flow, and non-conforming
  branches get flagged. For the commit style, run `git log --format=%s -20`.
- Tracked build output: `git ls-files target | head`. If anything is tracked, untrack it with
  `git rm -r --cached target`.
- GitHub: `git remote get-url origin`, then
  `gh repo view --json visibility,description,repositoryTopics,homepageUrl`. If that fails,
  the repo does not exist yet, and every GitHub step goes to the Phase 6 checklist.
- WASM signals: `cdylib`, `wasm-bindgen`, `Trunk.toml`, `package.json` (`packageManager`),
  `wasm32-*`.
- Code smells:
  - `find . -name mod.rs -not -path '*/target/*'`;
  - the separator grep and the unsafe grep from `docs/lints.md`.
- Lint backlog, counted without editing any file:

  ```sh
  cargo clippy --workspace --all-targets --all-features --message-format short -- \
    -W clippy::pedantic -W missing_docs -W clippy::missing_docs_in_private_items 2>&1 \
    | grep -cE '^[^ ]+: (warning|error)'
  ```

  Count `mod.rs` files separately: `mod_module_files` would abort compilation. rustdoc lints
  show up later, in `task doc`.
- READMEs: badges, relative links, and whether each link target exists. Repo size and areas,
  for the review-setup decision.

## Phase 2: Plan and confirm

Write a numbered change list from the gap table. Resolve every decision point with
AskUserQuestion. Get one confirmation for the whole plan. Then create the working branch
(`git switch -c feature/harden-baseline`, or one branch per area if the user prefers).

## Phase 3: Apply infrastructure

In this order. Commit after each step with an imperative message. Do not push.

1. **Taskfile and CI together**, in one commit, because they mirror each other.
   - `docs/taskfile.md`: `Taskfile.dist.yaml` and `fuzz/Taskfile.dist.yaml`. Load
     taskfile-authoring if available.
   - `docs/ci.md`: `ci.yml` and `actions-lint.yml`.
   - Copy the scripts the tasks call (`check-branch.sh`, `check-commit-msg.py`,
     `lint-mermaid.py`, `review-index.py`) to `scripts/`.
   - Wire in only what exists so far. Areas created by later steps add their own pieces when
     they land: step 5 adds the `fuzz/` include, its tasks and the CI `fuzz` job (after
     `cargo fuzz init`, which refuses an existing `fuzz/`). Step 6 adds `--html-in-header`
     to `doc` and to the CI `doc` job.
2. **Coverage**: `docs/coverage.md`, `codecov.yml`.
3. **Supply chain**: `docs/supply-chain.md`. `deny.toml`, `dependabot.yml`, `_typos.toml`.
4. **Licensing**: `docs/licensing.md`, `REUSE.toml`.
5. **Testing scaffolds**: `docs/testing.md`.
6. **Documentation**: `docs/documentation.md` (mermaid on docs.rs, README doctests), `docs/mermaid.html`.
7. **WASM and web** (if present): `docs/wasm.md`, `wasm.yml`.
8. **Metadata and README**: `docs/metadata.md`, `docs/readme.md`.
9. **Hooks, review rules, Copilot**: `docs/automation.md`, `docs/review.md`.
   `.pre-commit-config.yaml`, `copilot-instructions.md`, `review/*.md`, `REVIEW.md`.
10. **CONTRIBUTING.md** (template): merge it into an existing file, and keep only the
    branching model that applies.
11. **Release**: `docs/versioning.md` picks the mode.
    - **release-plz mode** (`docs/release.md`): `release-plz.toml`, `release-plz.yml`,
      `publish-crates-io.yml`.
    - **GitVersion mode** (human-driven releases): `GitVersion.yml`
      (`templates/gitversion/`), `scripts/zero-version.sh` and `scripts/ci-version.sh`, the
      `version` / `release:tag` / `release:cargo` tasks, the optional `release.toml`, and
      `publish-crates-io.gitversion.yml` applied as `publish-crates-io.yml`.
    - Both modes: `release-binaries.yml` for binaries (`docs/binaries.md`).
12. **GitHub settings** (after confirmation): `docs/github.md`. Repo settings, the ruleset
    (`templates/github/ruleset-default-branch.json`), and the environments.

Placeholders:

- Replace every `__PLACEHOLDER__` you use: `__OWNER__`, `__REPO__`, `__CRATE__`,
  `__BRANCH__`, `__LICENSE__`, `__YEAR__`, `__AUTHOR__` (source: `docs/licensing.md`),
  `__MERMAID_VERSION__`, `__MERMAID_CLI_VERSION__`, the `__*_REV__` hook revs, and the bin and
  wasm ones.
- Check with `git grep -nE '__[A-Z][A-Z_]*__'`.
- Pin the actions: `python3 <skill>/scripts/pin-actions.py .github/workflows/*.yml`. It needs
  an authenticated `gh`. Act on its "newer major" notes.
- Freeze the hook revs: `prek auto-update --freeze`.

## Phase 4: Lints and remediation

1. Add the lint table (`docs/lints.md`, `Cargo.lints.toml`), `clippy.toml` and
   `rustfmt.toml`. Set `unsafe_code = "forbid"` and add `#![forbid(unsafe_code)]` where the
   inventory found no unsafe. Clippy now fails, and that is expected. The steps below make
   the branch green again. Do not push before then.
2. Load `rust-style`, then fix the code in themed commits:
   1. Turn each `foo/mod.rs` into `foo.rs` plus `foo/` (`git mv`). Move integration tests to
      `tests/it/`.
   2. Split files that contain separator comments into modules.
   3. Write the missing doc comments, private items included.
   4. Clear the pedantic findings. `task lint:fix` does the mechanical ones, but review its
      diff: some fixes change semantics, for example casts.
   5. Apply the blank-line and helper-extraction rules to the files you touched.
3. A staged backlog, if the user chose one: set the affected lints to `warn`, leave
   `-D warnings` out of CI for now, and record the remaining count in an issue or `TODO.md`.

## Phase 5: Verify

Run each check. If `task ci` stops at a missing tool, run the remaining subtasks one by one.
Name every check you skipped.

```sh
task ci                                           # or its subtasks
actionlint                                        # snap install: actionlint -stdin-filename f - < f
zizmor .github/
cargo deny check
prek validate-config .pre-commit-config.yaml
uvx reuse lint
cargo package --list -p <crate>                   # LICENSES/, README, docs/mermaid.html included
release-plz release --dry-run                     # and `release-plz update` on a throwaway branch
python3 <skill>/scripts/trusted-publishing.py     # read-only
task version                                      # GitVersion mode: shows the computed version
git grep -nE '__[A-Z][A-Z_]*__'                   # no placeholders left
```

Grep the diff for newly added `#[allow(`, and remove or justify each one.

## Phase 6: Manual steps checklist

Print this list filled in for the repo, and skip what is already done. Offer to run the `gh`
steps after confirmation.

1. **Repo**: `gh repo create`, if it does not exist yet. Then set the description and topics
   (`docs/metadata.md`).
2. **Settings** (`docs/github.md`):
   - merge commits and squash merges (PR title and description);
   - delete head branches after merge;
   - auto-merge only once checks are required;
   - Actions allowed to create PRs.
3. **Ruleset**: the required status checks, on the default branch (and `develop` in Git Flow).
4. **Environments**: `crates-io` (tags `v*.*.*` / `*-v*.*.*`), plus one per extra deploy
   target (`npm`, pages, ...).
5. **Release App**: the variable `RELEASE_APP_CLIENT_ID` and the secret
   `RELEASE_APP_PRIVATE_KEY` (`docs/release.md`).
6. **Codecov**: install https://github.com/apps/codecov.
7. **First publish**: manually, for crates that are not on crates.io yet. Rename taken names
   first.
8. **Trusted publishing**: per crate, workflow `publish-crates-io.yml`, environment
   `crates-io`. Use `trusted-publishing.py --apply`, or the web UI.
9. **semver job**: enable it once every library crate has a first release.
10. **Local**: `prek install`. Install the missing tools named in Phase 5. In GitVersion
    mode, also install `dotnet tool install -g GitVersion.Tool` (and set `DO_NOT_TRACK=1`
    to opt out of its telemetry).
11. **Push** the branch, and open a PR with an imperative title. Its CI run is the final check.

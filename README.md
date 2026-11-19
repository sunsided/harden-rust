# harden-rust

Claude Code skills that bring Rust repositories to a strict, consistent baseline and keep
the code written in them at the same standard.

## Skills

### `harden-rust`

A one-time setup and audit for a repository. It runs in fixed phases:

1. Inventory
2. Plan and confirm
3. Apply
4. Remediate
5. Verify
6. Manual-steps checklist

It covers these areas:

- **Taskfile** (`Taskfile.dist.yaml`, delegating to `taskfile-authoring`). nextest is
  preferred, `task ci` mirrors CI, and `task clean` also cleans fuzz builds while keeping
  corpora and crash artifacts.
- **GitHub Actions**:
  - one job per check, SHA-pinned (`scripts/pin-actions.py`, which also flags newer majors);
  - `permissions: {}` and `persist-credentials: false`;
  - actionlint plus zizmor (blocking).
- **Lints**:
  - `clippy::pedantic`;
  - no `mod.rs`;
  - docs required on private items too;
  - `forbid(unsafe_code)`, with the safety-dance badge;
  - a separator-comment ban;
  - stricter complexity thresholds.
- **Supply chain**: cargo-deny; Dependabot grouped by ecosystem and by major vs minor/patch,
  with ecosystem prefixes and a zizmor cooldown; cargo-semver-checks; MSRV via
  `cargo hack --rust-version`; typos.
- **Coverage**: cargo-llvm-cov plus Codecov via OIDC.
- **Conventions**:
  - GitHub Flow or Git Flow, never `fix/`, `chore/` or `deps/` (`scripts/check-branch.sh`);
  - `copilot/*` branches migrated to `feature/*`;
  - imperative commit subjects (`scripts/check-commit-msg.py`);
  - CONTRIBUTING.md wins.
- **GitHub settings**:
  - merge commits and squash merges (PR title and description);
  - auto-delete head branches;
  - auto-merge only with required checks;
  - a ruleset with required status checks;
  - one tag-restricted environment per deployment target.
- **Hooks and review**:
  - a prek/pre-commit config that calls Taskfile tasks;
  - Copilot path-scoped review rules;
  - an optional `REVIEW.md` plus `docs/review/` registry, generated and drift-checked by
    `scripts/review-index.py`.
- **Docs**:
  - README badges, absolute URLs only;
  - READMEs as crate docs or doctest modules;
  - mermaid diagrams rendered on docs.rs and linted (`scripts/lint-mermaid.py`);
  - doctoc for long docs;
  - a CONTRIBUTING.md template.
- **Licensing**: `EUPL-1.2 OR MPL-2.0` (pushed) or `MIT OR Apache-2.0`, with CC0 examples via
  REUSE.
- **Testing**: fuzz plus proptest where feasible, plus criterion or divan benches.
- **WASM**:
  - `wasm32-unknown-unknown` and WASI without threads (vscode.dev);
  - wasm-bindgen, wasm-pack and trunk;
  - SvelteKit/Vite/yarn/corepack frontends;
  - cargo-sbom and npm trusted publishing.
- **Versioning**: SemVer 2.0, in one of two modes.
  - release-plz: bot-driven, per-crate, from commits.
  - GitVersion 7: human-driven, shared version.
    - `-alpha` on develop/main, `-beta` on release/hotfix, stable tags.
    - PR builds keep the target's label: `scripts/ci-version.sh`.
    - `scripts/zero-version.sh` works around the `cargo set-version` / cargo-release
      "cannot downgrade" bug.
    - `task release:tag`, plus optional cargo-release.
- **Releases**:
  - release-plz (git-only mode) tags and creates GitHub Releases;
  - `publish-crates-io.yml` publishes from the tag in a tag-restricted `crates-io`
    environment via trusted publishing;
  - `release-binaries.yml` builds `cargo auditable` binaries (always including linux-musl),
    extracts SBOMs, attests binary, SBOM and archive, and attaches them to the Release;
  - `scripts/trusted-publishing.py` checks crate-name ownership and configures trusted
    publishing in bulk.

### `rust-style`

House style for every line of Rust that is written or reviewed:

- doc comments on every item, private ones included;
- no `mod.rs`;
- no `// ----` separators (split into modules instead);
- strategic blank lines;
- aggressive helper extraction;
- clean pedantic clippy, using `#[expect(..., reason)]` instead of `#[allow]`.

## Layout

| Path | Contents |
|---|---|
| `skills/harden-rust/SKILL.md` | Workflow, decision points, checklist |
| `skills/harden-rust/docs/` | Deep dives per area (ci, lints, release, trusted-publishing, wasm, ...) |
| `skills/harden-rust/templates/` | Taskfiles, workflows, configs with `__PLACEHOLDER__`s and tag-only action refs |
| `skills/harden-rust/scripts/` | `pin-actions.py`, `trusted-publishing.py`, `check-branch.sh`, `check-commit-msg.py`, `lint-mermaid.py`, `review-index.py`, `zero-version.sh`, `ci-version.sh` |
| `skills/rust-style/` | Style rules and before/after examples |
| `evals/` | Trigger evals for both skills |

## Installation

```bash
ln -s "$(pwd)/skills/harden-rust" ~/.claude/skills/harden-rust
ln -s "$(pwd)/skills/rust-style" ~/.claude/skills/rust-style
```

Recommended companion: the `taskfile` / `taskfile-authoring` skills.

## Requirements (used when present)

`task`, `gh` (authenticated, for SHA pinning), `actionlint`, `zizmor`, `cargo-nextest`,
`cargo-llvm-cov`, `cargo-deny`, `cargo-hack`, `cargo-semver-checks`, `cargo-fuzz` (nightly),
`release-plz`, `typos`, `prek`, `cargo-auditable` / `auditable2cdx`, `mmdc` (mermaid-cli), `uvx` (for `reuse`), `dotnet-gitversion` and `cargo-edit` (GitVersion mode).

## License

Licensed under either of

- European Union Public Licence, Version 1.2 ([LICENSES/EUPL-1.2.txt](LICENSES/EUPL-1.2.txt))
- Mozilla Public License, Version 2.0 ([LICENSES/MPL-2.0.txt](LICENSES/MPL-2.0.txt))

at your option. Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this work by you shall be licensed as above, without any additional terms or
conditions.

# harden-rust

[![License: EUPL-1.2 OR MPL-2.0](https://img.shields.io/badge/license-EUPL--1.2%20OR%20MPL--2.0-blue.svg)](https://github.com/sunsided/harden-rust#license)
[![Claude Code skills](https://img.shields.io/badge/Claude%20Code-skills-d97757.svg)](https://www.anthropic.com/claude-code)
[![skills.sh](https://img.shields.io/badge/install-skills.sh-black.svg)](https://skills.sh)
[![Rust](https://img.shields.io/badge/for-Rust-b7410e.svg?logo=rust)](https://www.rust-lang.org)
[![unsafe forbidden](https://img.shields.io/badge/unsafe-forbidden-success.svg)](https://github.com/rust-secure-code/safety-dance/)
[![Last commit](https://img.shields.io/github/last-commit/sunsided/harden-rust.svg)](https://github.com/sunsided/harden-rust/commits/main)

[Claude Code](https://www.anthropic.com/claude-code) skills that bring Rust repositories to a
strict, consistent baseline and keep the code written in them at the same standard.

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

- **Taskfile** ([Task](https://taskfile.dev), `Taskfile.dist.yaml`, delegating to
  [`taskfile-authoring`](https://github.com/sunsided/taskfile-skills)).
  [cargo-nextest](https://nexte.st) is preferred, `task ci` mirrors CI, and `task clean` also
  cleans fuzz builds while keeping corpora and crash artifacts.
- **GitHub Actions**:
  - one job per check, SHA-pinned (`scripts/pin-actions.py`, which also flags newer majors);
  - `permissions: {}` and `persist-credentials: false`;
  - [actionlint](https://github.com/rhysd/actionlint) plus [zizmor](https://docs.zizmor.sh)
    (blocking).
- **Lints**:
  - [`clippy::pedantic`](https://doc.rust-lang.org/clippy/);
  - no `mod.rs`;
  - docs required on private items too;
  - `forbid(unsafe_code)`, with the
    [safety-dance](https://github.com/rust-secure-code/safety-dance) badge;
  - a separator-comment ban;
  - stricter complexity thresholds.
- **Supply chain**:
  - [cargo-deny](https://github.com/EmbarkStudios/cargo-deny);
  - [Dependabot](https://docs.github.com/en/code-security/dependabot), grouped by ecosystem
    and by major vs minor/patch, with ecosystem prefixes and a zizmor cooldown;
  - [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks);
  - MSRV via [cargo-hack](https://github.com/taiki-e/cargo-hack) `--rust-version`;
  - [typos](https://github.com/crate-ci/typos).
- **Coverage**: [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) plus
  [Codecov](https://about.codecov.io) via OIDC.
- **Conventions**:
  - [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) or
    [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/), never `fix/`,
    `chore/` or `deps/` (`scripts/check-branch.sh`);
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
  - a [prek](https://prek.j178.dev) / [pre-commit](https://pre-commit.com) config that calls
    Taskfile tasks;
  - Copilot
    [path-scoped review rules](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions);
  - an optional `REVIEW.md` plus `docs/review/` registry, generated and drift-checked by
    `scripts/review-index.py`.
- **Docs**:
  - README badges, absolute URLs only;
  - READMEs as crate docs or doctest modules;
  - [mermaid](https://mermaid.js.org) diagrams rendered on [docs.rs](https://docs.rs) and
    linted (`scripts/lint-mermaid.py`);
  - [doctoc](https://github.com/thlorenz/doctoc) for long docs;
  - a CONTRIBUTING.md template.
- **Licensing**: `EUPL-1.2 OR MPL-2.0` (pushed) or `MIT OR Apache-2.0`, with CC0 examples via
  [REUSE](https://reuse.software).
- **Testing**: [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) plus
  [proptest](https://github.com/proptest-rs/proptest) where feasible, plus
  [criterion](https://github.com/bheisler/criterion.rs) or
  [divan](https://github.com/nvzqz/divan) benches.
- **WASM**:
  - `wasm32-unknown-unknown`, and WASI without threads (vscode.dev);
  - [wasm-bindgen](https://github.com/wasm-bindgen/wasm-bindgen),
    [wasm-pack](https://github.com/drager/wasm-pack) and
    [trunk](https://github.com/trunk-rs/trunk);
  - [SvelteKit](https://svelte.dev/docs/kit), [Vite](https://vite.dev),
    [Yarn](https://yarnpkg.com) and [Corepack](https://github.com/nodejs/corepack) frontends;
  - [cargo-sbom](https://github.com/psastras/sbom-rs) and
    [npm trusted publishing](https://docs.npmjs.com/trusted-publishers).
- **Versioning**: [SemVer 2.0](https://semver.org/spec/v2.0.0.html), in one of two modes.
  - [release-plz](https://release-plz.dev): bot-driven, per-crate, from commits.
  - [GitVersion](https://gitversion.net) 7: human-driven, shared version.
    - `-alpha` on develop/main, `-beta` on release/hotfix, stable tags.
    - PR builds keep the target's label: `scripts/ci-version.sh`.
    - `scripts/zero-version.sh` works around the
      [cargo-edit](https://github.com/killercup/cargo-edit) `set-version` /
      [cargo-release](https://github.com/crate-ci/cargo-release) "cannot downgrade" bug.
    - `task release:tag`, plus optional cargo-release.
- **Releases**:
  - release-plz (git-only mode) tags and creates GitHub Releases.
  - `publish-crates-io.yml` publishes from the tag in a tag-restricted `crates-io`
    environment via
    [crates.io trusted publishing](https://rust-lang.github.io/rfcs/3691-trusted-publishing-cratesio.html).
  - `release-binaries.yml` builds
    [cargo-auditable](https://github.com/rust-secure-code/cargo-auditable) binaries (always
    including linux-musl), extracts SBOMs, attests binary, SBOM and archive via
    [artifact attestations](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations),
    and attaches them to the Release.
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

With the [skills CLI](https://skills.sh), for Claude Code and other agents:

```bash
npx skills add sunsided/harden-rust --skill '*' -g     # both skills, user-wide
npx skills add sunsided/harden-rust --skill rust-style  # one skill, current project only
```

Or from a clone, symlinked so that `git pull` updates them:

```bash
ln -s "$(pwd)/skills/harden-rust" ~/.claude/skills/harden-rust
ln -s "$(pwd)/skills/rust-style" ~/.claude/skills/rust-style
```

Or as `.skill` bundles for upload: `task build` writes `dist/<skill>-<version>.skill`, with the
version taken from each `SKILL.md`.

Recommended companion: the `taskfile` / `taskfile-authoring` skills from
[sunsided/taskfile-skills](https://github.com/sunsided/taskfile-skills).

## Requirements (used when present)

The skills check for each tool. Missing tools are reported and skipped, not installed.

| Tool | Used for |
|---|---|
| [Task](https://taskfile.dev) | Running the generated tasks |
| [GitHub CLI](https://cli.github.com) (`gh`, authenticated) | SHA pinning, repo settings |
| [actionlint](https://github.com/rhysd/actionlint), [zizmor](https://docs.zizmor.sh) | Workflow linting |
| [cargo-nextest](https://nexte.st), [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) | Tests, coverage |
| [cargo-deny](https://github.com/EmbarkStudios/cargo-deny), [cargo-hack](https://github.com/taiki-e/cargo-hack), [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) | Supply chain, MSRV, semver |
| [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) (nightly) | Fuzz targets |
| [release-plz](https://release-plz.dev) | release-plz mode |
| [GitVersion.Tool](https://www.nuget.org/packages/GitVersion.Tool) (`dotnet-gitversion`), [cargo-edit](https://github.com/killercup/cargo-edit) | GitVersion mode |
| [typos](https://github.com/crate-ci/typos), [prek](https://prek.j178.dev) | Spelling, git hooks |
| [cargo-auditable](https://github.com/rust-secure-code/cargo-auditable) / `auditable2cdx` | Release binaries and SBOMs |
| [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) (`mmdc`) | Diagram linting |
| [uv](https://docs.astral.sh/uv/) (`uvx reuse`) | REUSE license checks |

## License

Licensed under either of

- European Union Public Licence, Version 1.2 ([LICENSES/EUPL-1.2.txt](LICENSES/EUPL-1.2.txt),
  [eupl.eu](https://eupl.eu))
- Mozilla Public License, Version 2.0 ([LICENSES/MPL-2.0.txt](LICENSES/MPL-2.0.txt))

at your option. Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this work by you shall be licensed as above, without any additional terms or
conditions.

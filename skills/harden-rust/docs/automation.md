# Hooks, Copilot review rules, doc tooling

## Git hooks (prek preferred)

- Template: `templates/.pre-commit-config.yaml`. It uses the standard pre-commit format, so
  it works with **prek** (a fast Rust reimplementation, https://prek.j178.dev) and with
  pre-commit. Default to prek. Ask with AskUserQuestion only if the repo already uses
  pre-commit, or the user names it.
- Local hooks call `task ...`. Commands live in the Taskfile only, and the hooks just call it.
- Fast checks run on `pre-commit`: fmt, separators, README links, typos, actions, review
  index, mermaid. The commit subject is checked on `commit-msg` (`scripts/check-commit-msg.py`,
  imperative mood). Slow checks run on `pre-push`: branch name, clippy, tests.
- Copy the hook scripts the config calls (`check-commit-msg.py`, `check-branch.sh`,
  `lint-mermaid.py`, `review-index.py`) into the repo's `scripts/`.
- Fill in `rev:` with `prek auto-update --freeze` (or `pre-commit autoupdate --freeze`). That
  pins SHAs with a tag comment. Never write revs from memory.
- Install: `prek install` (it installs both hook types, via `default_install_hook_types`).
  This is a local action on the user's clone. Mention it in the Phase 6 checklist rather
  than running it, unless the user asks.
- Drop hooks for tools the repo does not use, for example doctoc, or mermaid when there are
  no diagrams.

## Mermaid lint

`scripts/lint-mermaid.py` finds every ```` ```mermaid ```` block in the git-tracked `*.md`
files and in Rust doc comments (`//!`, `///`). It renders each block with mermaid-cli (`mmdc`)
and reports the broken ones as `file:line`.

- Copy the script to `scripts/lint-mermaid.py` in the repo, so hooks and CI can call it.
- Taskfile: `lint:mermaid` runs `python3 scripts/lint-mermaid.py`. With no diagrams it
  passes without mermaid-cli. With diagrams, the script stops with an install hint when
  `mmdc` (or the `MMDC` command) is missing.
- CI (only when the repo has diagrams): add a step to the `style` job that sets
  `MMDC: npx --yes @mermaid-js/mermaid-cli@<exact version>` and `MMDC_NO_SANDBOX: "1"`.
  Resolve the version with
  `curl -s https://data.jsdelivr.com/v1/packages/npm/@mermaid-js/mermaid-cli/resolved`.
- mermaid-cli needs Node and a headless Chromium, which puppeteer downloads on first run.
  Locally, install it with `npm install -g @mermaid-js/mermaid-cli` if the user agrees.

## doctoc

Use it only where it helps: a README or doc with roughly 5 or more `##` sections. Do not
add it to short READMEs.

- Add `<!-- START doctoc -->` / `<!-- END doctoc -->` markers below the badges. The hook runs
  with `--update-only`, so only files that have the markers are touched.
- doctoc produces in-page anchors (`#usage`), which `lint:readme` allows.
- If a README is included as crate docs (`docs/documentation.md`), the TOC shows on docs.rs
  too. Its anchors work there, because rustdoc generates heading ids the same way for simple
  headings.

## GitHub Copilot review rules

Copilot code review and the Copilot cloud agent read path-scoped instruction files
(`.github/instructions/*.instructions.md`, with `applyTo` globs in the frontmatter), plus a
repo-wide `.github/copilot-instructions.md`. The rules come from the review topics in
`templates/review/` (ci, rust, docs, release):

- `ci`: `task ci` and `ci.yml` stay in sync, SHA pinning, permissions, the trusted-publishing filename.
- `rust`: the rust-style rules, condensed.
- `docs`: absolute URLs, valid and current mermaid, doctested code blocks, doctoc.
- `release`: metadata fields, separate versions, deny policy, no manual bumps.

The repo gets them either as hand-maintained Copilot files (light setup) or generated from
`docs/review/` (registry setup). See `docs/review.md` for both setups and how to choose
between them.

- Make the rules specific to the repo: name the actual CI jobs, crates and wasm targets.
  Generic rules review poorly.
- Drop topics that do not apply. For example, there is no release topic when nothing is
  published.
- To keep a file away from one agent, add `excludeAgent: "code-review"` or
  `excludeAgent: "cloud-agent"` to its frontmatter.

## typos

[typos](https://github.com/crate-ci/typos) checks spelling in code and docs, with few false
positives. Template: `templates/_typos.toml`. It excludes lockfiles, fuzz corpora, proptest
regressions and license texts.

- Taskfile: `lint:typos` runs `typos`, and is part of `lint`. `typos --write-changes` fixes
  the findings.
- Hook: the `typos` hook from `crate-ci/typos` (rev frozen via auto-update).
- CI: a `crate-ci/typos` action step in the `style` job.
- On the first run, fix the real typos. Allow-list genuine terms in
  `[default.extend-words]`, and say why for each one.

Sources: https://docs.github.com/en/copilot/tutorials/customize-code-review,
https://github.blog/changelog/2025-09-03-copilot-code-review-path-scoped-custom-instruction-file-support,
https://github.blog/changelog/2025-11-12-copilot-code-review-and-coding-agent-now-support-agent-specific-instructions/,
https://prek.j178.dev

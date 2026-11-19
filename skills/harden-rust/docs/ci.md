# CI (GitHub Actions)

Templates: `templates/.github/workflows/ci.yml` and `templates/.github/workflows/actions-lint.yml`.

## Layout

There is one job per check: `branch`, `fmt`, `clippy`, `style` (separators, README links,
typos, review index, mermaid), `doc`, `test` (OS matrix), `coverage`, `deny`, `msrv`,
`semver`, `fuzz` (build, fmt and clippy of the fuzz crate). CI deliberately does not run plain `task ci`. Separate jobs
fail separately, run in parallel, and each can be a required status check. The Taskfile
`ci` task mirrors the same steps for local use. Edit both together.

Adjust the template to the repo:

- No `fuzz/` directory: remove the `fuzz` job.
- No crate published yet: semver-checks has no baseline, so the `semver` job fails. Leave
  the job out until the first release, and note it in the Phase 6 checklist. release-plz
  runs semver checks on release PRs anyway.
- Binary-only crates: semver-checks only checks libraries, so drop the job.
- Platform-specific code: keep the OS matrix. Otherwise shrinking it to `ubuntu-latest` is fine.
- **Existing workflows:** add `ci.yml` next to them. Do not fold the template into a
  differently named file. Harden the existing workflows in place (permissions, pinning,
  `persist-credentials`), and keep every job, trigger and secret.
  - If an existing job duplicates a template job (for example `cargo test`), ask whether to
    drop the duplicate.
  - Keep user-specific test flags (for example `-- --test-threads=1`) in every test
    invocation: the Taskfile, the CI `test` and `coverage` jobs, and `publish-crates-io.yml`'s `verify`.
    nextest takes `--test-threads 1` directly.
  - Map an existing job to an existing task (a `docker` job to `task docker`). A job that
    has no task stays CI-only. Name it in the ci review topic.
  - The badge in `docs/readme.md` and the required checks use the real workflow file and
    job names.
- Binary-only crates: drop the `cargo test --doc` step (no library, no doctests).
- Tests: `NEXTEST_NO_TESTS: warn` keeps crates without tests from failing newer nextest.
- Remove the `style` steps that do not apply (review index, mermaid). `__MERMAID_CLI_VERSION__`:
  see `docs/automation.md`.

## Hardening rules (zizmor-clean)

- `permissions: {}` at the top, then the least privilege each job needs.
- Every `actions/checkout` sets `persist-credentials: false` (zizmor `artipacked`).
- **Pin every action to a full commit SHA** with the tag as a comment:
  `uses: actions/checkout@<40-hex> # v6.0.1`. Never write a SHA from memory. Run:

  ```sh
  python3 <skill>/scripts/pin-actions.py .github/workflows/*.yml
  ```

  The script (needs an authenticated `gh`) resolves each `owner/repo@ref` through `gh api` and rewrites it in place.
  It turns floating refs such as `@v6` into the most specific matching tag (`# v6.0.1`).
  It prints a note when a newer **major** exists. Read that release's notes, bump the
  template ref when it is safe, and re-pin. An inline `with: { ... }` mapping on
  `dtolnay/rust-toolchain` is left alone, with a warning to add `toolchain:` by hand.
  `dtolnay/rust-toolchain@stable` becomes `@<sha> # stable`. That is fine, because that
  action reads the toolchain from the branch name. Pinning by SHA keeps it working, but then
  pass `toolchain: stable` explicitly. The script adds that input for you.
- Dependabot (`docs/supply-chain.md`) keeps the pinned SHAs current, and updates the comment too.
- No `pull_request_target` and no `${{ github.event.* }}` interpolation inside `run:`.
  Pass such values through `env:` instead.
- `concurrency` cancels superseded PR runs. It never cancels pushes to the main branch.

## actionlint and zizmor

`actions-lint.yml` runs both on every PR. It has no path filter, so both jobs can be
required checks. Locally: `task lint:actions`. A snap-installed actionlint cannot read paths
outside `$HOME`. Use `actionlint -stdin-filename f.yml - < f.yml` per file there.
The zizmor action runs in blocking mode (`advanced-security: false`), so findings fail the
job. The alternative is SARIF upload to the Security tab: remove the input and add
`security-events: write`. That mode does not fail the job.

Fix zizmor findings; do not ignore them. If a finding is a genuine false positive, add an
inline `# zizmor: ignore[audit-name]` comment with a reason.

Sources: https://docs.zizmor.sh/integrations/, https://github.com/zizmorcore/zizmor-action

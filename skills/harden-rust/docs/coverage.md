# Coverage (codecov)

Assume the repo is public, or will be. Codecov is free for public repos.

- Collect: `cargo llvm-cov nextest --workspace --all-features --lcov --output-path lcov.info`
  (`task coverage`). Doctests are not included, because that needs nightly.
- Upload: `codecov/codecov-action` with `use_oidc: true` and the job permission `id-token: write`.
  No `CODECOV_TOKEN` secret is needed.
- **Fork PRs** get no OIDC token. The template sets `use_oidc` to false for fork PRs, and
  Codecov then accepts a tokenless upload from forks of public repos.
- **Private repo**: OIDC still works once the Codecov app is installed. The alternative is a
  `CODECOV_TOKEN` secret.
- `codecov.yml` (template): project status `auto` with a 1% threshold, patch target 80%, and a
  compact PR comment. Tune the targets with the user. Do not lower them silently.
- Badge: see `docs/readme.md`.
- Manual step: install the Codecov GitHub App (https://github.com/apps/codecov).

Sources: https://github.com/codecov/codecov-action#usage, https://docs.codecov.com/docs/codecov-tokens

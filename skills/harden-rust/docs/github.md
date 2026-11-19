# GitHub repository, branching, commits, environments

## Baseline (CONTRIBUTING.md wins where it says otherwise)

- **Branching model**:
  - **GitHub Flow** for small repos: `main` plus `feature/<topic>`.
  - **Git Flow** for larger or versioned-in-parallel repos: `main`, `develop`, `feature/*`,
    `release/*`, `hotfix/*` and `support/*`.
  - Ask with AskUserQuestion when the repo does not show a model yet (an existing `develop`
    branch means Git Flow). Recommend GitHub Flow for single-maintainer or small repos.
  - **Never** `chore/`, `fix/`, `deps/`, `docs/`, `bugfix/` or similar. A bug fix is a
    `feature/*` branch in GitHub Flow, and a `hotfix/*` or `feature/*` branch in Git Flow.
  - Bot exceptions: `release/*` (release-plz PRs, `pr_branch_prefix = "release/"`) and
    `dependabot/*` (not configurable).
  - Copilot cloud agent branches (`copilot/*`) are migrated to `feature/*` as soon as
    someone works on them (see below).
  - Enforcement: `scripts/check-branch.sh`, run by `task lint:branch`, the pre-push hook and
    the CI `branch` job. `BRANCH_FLOW` selects the model.
- **Commit style: imperative mood**, Git's own convention. Examples: "Add proptest for the
  parser round-trip", "Fix overflow in tile index". Not Conventional Commits (`feat: ...`),
  and not past tense ("Added ...").
  - Subject at most 72 characters, capitalized, no trailing period. For anything non-trivial,
    a blank line and a body that explains *why*. The hook checks the subject and the blank
    line, but not whether a body exists.
  - Enforcement: `scripts/check-commit-msg.py` as a `commit-msg` hook. release-plz maps
    imperative verbs to changelog groups and bumps (`templates/release-plz.toml`).
- **Existing history with another convention**: if the history uses another style (for
  example Conventional Commits) and CONTRIBUTING.md says nothing, ask. Recommend the
  imperative baseline from now on, without rewriting history. If the user keeps
  Conventional Commits, write that into CONTRIBUTING.md, drop the commit-msg hook and the
  custom bump regexes, and drop the commit parsers (`docs/release.md`).
- **Non-conforming branches** (for example `fix/old-thing`): list them, and ask whether to
  rename them. A local rename is `git branch -m fix/x feature/x`. Renaming on the remote
  uses the same API call as for `copilot/*` branches (below), and needs confirmation.
- **Agents follow the baseline too.** This skill's own work happens on a `feature/<topic>`
  branch (for example `feature/harden-ci`), with imperative commits. Read CONTRIBUTING.md
  first. If it defines another model or style, that wins, and the checks are adapted to it
  (or dropped).

## Migrating `copilot/*` branches

When you are about to work on a PR whose head is `copilot/<topic>`, confirm with the user,
then:

```sh
gh api -X POST repos/__OWNER__/__REPO__/branches/copilot%2F<topic>/rename -f new_name=feature/<topic>
gh pr view <number> --json headRefName   # must now show feature/<topic>
git fetch origin && git switch feature/<topic>
```

Renaming a branch on GitHub keeps open PRs attached. If `headRefName` did not change, open
a new PR from `feature/<topic>` that references the old one, and close the old one.

## Repository settings

Apply them after a confirmation, because they are outward-facing:

```sh
gh api -X PATCH repos/__OWNER__/__REPO__ \
  -F allow_merge_commit=true \
  -F allow_squash_merge=true \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY \
  -F delete_branch_on_merge=true \
  -F allow_auto_merge=<true only if required status checks exist>
```

- Leave `allow_rebase_merge` untouched.
- Turn auto-merge on only once a ruleset or branch protection requires status checks.
  Without required checks, auto-merge merges immediately.
- Under Settings, Actions, General, allow GitHub Actions to create and approve pull
  requests. release-plz needs this.
- If `gh repo view` fails, the repo does not exist yet. Do not create it. List
  `gh repo create` plus these settings in the Phase 6 checklist.

## Rulesets (required status checks)

Use `templates/github/ruleset-default-branch.json`. It protects the default branch, and
`develop` too in Git Flow (add `refs/heads/develop` to `include`). It requires a PR, blocks
force-pushes and deletion, and requires status checks.

- The required check names are the job `name:` values. With a matrix, each matrix entry is
  its own check, for example `test (ubuntu-latest)`.
- The template lists them under `required_status_checks`. Fill them in from the repo's
  actual workflows.
- Never require a job that does not report on every PR and merge-queue run. That rules out
  path-filtered workflows and jobs skipped by `if:`, such as `semver` before the first
  release. A required check that never reports blocks merging. The `branch` job runs on
  `pull_request` and `merge_group`, so it can be required.
- Apply it: `gh api -X POST repos/__OWNER__/__REPO__/rulesets --input ruleset.json`. Then turn
  on `allow_auto_merge`.

## Deployment environments

Every deployment target gets its own environment, restricted to release tags:

| Environment | Workflow / job | Tag policy | Notes |
|---|---|---|---|
| `crates-io` | `publish-crates-io.yml` / `crates-io` | `v*.*.*`, plus `*-v*.*.*` in multi-crate repos (both also match SemVer pre-releases like `v1.2.0-rc.1`) | crates.io trusted publishing names this environment |
| `npm` | publish job for the wasm package | `v*.*.*` (or the package's tag pattern) | npm trusted publishing (OIDC) names the workflow and environment |
| `github-pages` / `cloudflare` / ... | deploy job of the web app | `v*.*.*` or the default branch, as the user decides | one per target |

Create each one after a confirmation:

```sh
gh api -X PUT repos/__OWNER__/__REPO__/environments/crates-io \
  -F 'deployment_branch_policy[protected_branches]=false' \
  -F 'deployment_branch_policy[custom_branch_policies]=true'
gh api -X POST repos/__OWNER__/__REPO__/environments/crates-io/deployment-branch-policies \
  -f name='v*.*.*' -f type=tag
# multi-crate: add the same policy with -f name='*-v*.*.*'
```

- **Specific status checks per environment**: the deploy job `needs:` a verification job in
  the same workflow, which re-runs the checks that matter for that target on the tagged
  commit (`publish-crates-io.yml`'s `verify` job). Environments cannot require repository status checks
  themselves. Required reviewers or a wait timer are optional extra protection rules. Ask
  the user whether they want them.
- Secrets used only for one deployment belong to that environment, not the repo.
- The trusted-publishing config of every crate names the workflow (`publish-crates-io.yml`) and the
  environment (`crates-io`). `scripts/trusted-publishing.py` uses both as its defaults.

Sources: https://docs.github.com/en/rest/repos/repos#update-a-repository,
https://docs.github.com/en/rest/deployments/environments,
https://docs.github.com/en/rest/deployments/branch-policies,
https://docs.github.com/en/rest/repos/rules

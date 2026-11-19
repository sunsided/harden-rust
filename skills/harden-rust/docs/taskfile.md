# Taskfile

Start from `templates/Taskfile.dist.yaml` and `templates/fuzz/Taskfile.dist.yaml`. If the
`taskfile-authoring` skill is available, load it. It owns the file-naming rules
(`Taskfile.dist.yaml` first), the gitignore checks, the precondition style and the merge
behavior.

## Rules

- **Merge, never replace.** Keep the existing Taskfile's file name (`Taskfile.yml` stays
  `Taskfile.yml`). Keep existing tasks. When an existing task name clashes with a template
  task, compare the two and ask the user which one wins.
  - Carry user flags (for example `-- --test-threads=1`) into every variant: nextest,
    `cargo test` and coverage.
  - Existing tasks without preconditions get them (taskfile-authoring rule).
- **CI flags:** `ci.yml` sets no global `RUSTFLAGS`. clippy and rustdoc get `-D warnings`
  explicitly, in CI and in the tasks alike, so `task ci` and CI behave the same.
- **Task names and structure:** this template wins over taskfile-authoring's suggestions on
  names and on structure (`build` builds benches through `--all-targets` and calls `fuzz:build`; cargo itself needs
  no precondition), because
  CI, hooks, Copilot rules and CONTRIBUTING.md reference them. `doc` and `test:doc` carry
  `docs` and `test:docs` aliases.
- **nextest preferred.** The `NEXTEST` var detects `cargo nextest`. `test` uses nextest when
  it is present and falls back to `cargo test` otherwise. nextest does not run doctests, so
  `test` always runs `test:doc` too. `test:doc` skips itself for binary-only crates
  (`HAS_LIB`).
  - Test binaries with `harness = false` (for example criterion benches or custom harnesses)
    do not work with nextest's listing. Exclude them with a filterset (`-E 'not binary(name)'`).
- **`ci` mirrors CI.** Each CI job maps to one task. Change both in the same commit.
  `coverage` and `semver` are left out of `ci`: coverage only matters for the upload, and
  semver needs published baselines.
- **`clean` cleans fuzz builds too.** `fuzz:clean` removes `fuzz/target` and `fuzz/coverage`.
  Crash reproducers (`fuzz/artifacts`) and corpora (`fuzz/corpus`) are valuable and survive.
  Only the separate, prompting task `fuzz:clean:artifacts` deletes them.
- **Drop what does not apply.** Calling a missing included task fails, even though the
  `includes` entry is `optional`.
  - No `fuzz/` directory: remove `fuzz:build` from `build` and `ci`, `fuzz:lint` from `ci`, `fuzz:fmt` from
    `fmt`, and `fuzz:clean` from `clean`.
  - `lint:mermaid` and `lint:review` pass by themselves when there are no diagrams or no
    `docs/review/`. They need their scripts copied to `scripts/`.
  - `lint:branch` needs `scripts/check-branch.sh`. Set `BRANCH_FLOW` to `gitflow` for Git Flow.
- **Task's shell is not bash.** `! a | b` does not negate a pipeline there. Use
  `if a | b; then exit 1; fi` (see `lint:readme`). Env set on a task does not reach tasks
  it calls through `task:`. Run a nested `task <name>` command instead (see `test:prop`).
- **Gitignore:** make sure `.gitignore` has `/target` and `lcov.info`. Untrack build output
  that was committed by mistake (`git rm -r --cached target`). Commit `Cargo.lock`,
  for libraries too (current Cargo guidance).
- **No benches:** keep `bench` anyway, so that it is ready when benches are added.

## Optional tool installs

Preconditions print install hints. Do not install tools for the user without asking.
In CI, `taiki-e/install-action` installs them as prebuilt binaries.

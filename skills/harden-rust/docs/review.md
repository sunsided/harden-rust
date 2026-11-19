# Review rules: REVIEW.md and the docs/review/ registry

Humans and coding agents should review against the same rules, and each should read only
what is relevant to the change.

## Decide first (AskUserQuestion)

Inspect the repo, then recommend one of these:

| Repo signal | Recommend |
|---|---|
| Under ~5k lines of Rust and at most 2 crates, with no wasm or web part | **Light**: Copilot instruction files only, no registry |
| 3 or more crates, or over ~5k lines, or a wasm or web part, or several regular contributors or agents | **Registry**: `REVIEW.md` plus `docs/review/` |
| Existing `REVIEW.md` or review docs | **Registry**, migrating the existing content into topics |

Size breaks the tie. A tiny 2-crate workspace is light.

State the signals you found (crate count, line count via `tokei` or `wc -l`, areas,
contributors via `git shortlog -sn HEAD | wc -l`), and put the recommended option first.

## Light setup

Copy the topic templates you need (`templates/review/*.md`) to
`.github/instructions/<topic>.instructions.md`. Copilot reads the `applyTo` frontmatter and
ignores `title` and `summary`. Adapt each body to the repo. Point `.github/copilot-instructions.md`
at them. These files are maintained by hand.

## Registry setup

Files:

- `docs/review/<topic>.md`: one per area. Start from `templates/review/` (ci, rust, docs,
  release) and add repo-specific areas, such as `wasm.md`, `simulation.md` or `web.md`. Each
  has the frontmatter `title`, `applyTo` (comma-separated globs) and `summary`.
- `docs/review/README.md`: the registry (template). Its table between the
  `review-index` markers is generated.
- `REVIEW.md` (template): a short top-level pointer to the index.
- `.github/instructions/<topic>.instructions.md`: **generated** from the topics, so Copilot
  code review applies the same rules per path. Never edit these by hand.
- Pointers: `.github/copilot-instructions.md`, plus `CLAUDE.md` / `AGENTS.md` when present
  (ask before creating either), get a "Review" section like this:
  "Review rules: see docs/review/README.md. Read the topics whose `applyTo` matches the
  changed files."

Machinery that keeps it from drifting:

- `scripts/review-index.py` (copy it into the repo's `scripts/`) regenerates the index table
  and the Copilot files, and deletes generated files whose topic is gone.
- `--check` fails when:
  - the index or a generated file is stale;
  - a generated file has no source topic;
  - none of a topic's globs match a tracked file, which means the rule describes code that
    no longer exists.

  A single unmatched glob only warns.
- Taskfile: `review:index` runs the script, and `lint:review` runs `--check`. `lint:review` is
  part of `lint`, and therefore of `task ci`.
- Hook: a local `review-index` hook that runs `task lint:review` on changes under
  `docs/review/` and `.github/instructions/`.
- CI: a step in the `style` job that runs `python3 scripts/review-index.py --check`.
- When the skill adds an area later (for example wasm), add a topic file in the same change.

## Writing topics

- Write rules a reviewer can check from the diff: "Every CI job has a matching step in
  `task ci`". Not slogans: "Write good CI".
- Do not repeat what tools enforce (fmt, clippy, typos). Mention the tool, so reviewers
  know it is covered.
- Name the repo's real jobs, crates, modules and invariants.
- Keep topics short: roughly 10 to 25 bullets. Split a topic when it grows past that.

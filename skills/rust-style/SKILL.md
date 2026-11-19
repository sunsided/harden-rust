---
name: rust-style
description: >
  House style for writing, refactoring and reviewing Rust code. Use whenever Rust code is
  written, generated, edited, refactored or reviewed: new modules, functions, structs, enums,
  traits, tests, fuzz targets, benches, simulations or game loops, even when the user only says
  "implement X", "add a function", "fix this bug" or "review this" in a Rust project. Enforces
  doc comments on every item including private ones, no mod.rs (foo.rs + foo/), no `// ----`
  separator comments, strategic blank lines, aggressive helper extraction, and pedantic-clippy-
  clean code. Skip for non-Rust code and for repo infrastructure setup (use harden-rust).
version: 0.1.0
tags: [rust, style, documentation, clippy, refactoring]
---

# Rust style

These rules apply to every line of Rust you write or touch. Each rule says what to do and
why. `docs/examples.md` has before/after pairs for each one. When you edit an existing file,
bring the code you touch up to these rules. Do not reformat untouched code in an unrelated
change.

## 1. Doc comments on everything, private included

Every module (`//!`), type, field, enum variant, function, method, trait, associated item,
constant, static and macro gets a doc comment. Private and `pub(crate)` items too. Test
helpers too. No exceptions.

Write docs that make other developers envious:

- **Say what the name cannot.** Cover intent, invariants, units (`/// Elapsed time in
  milliseconds since the simulation started.`), valid ranges, ownership and lifetime
  expectations, and performance characteristics when they matter. `/// The name.` on a
  `name` field is worthless.
- **The first line is a summary sentence.** It shows in listings. Put details after a blank
  `///` line.
- **Sections** for public functions, where they apply: `# Errors` (every error variant and
  when it occurs), `# Panics` (every panic path), `# Safety` (on `unsafe fn`: the caller's
  obligations), and `# Examples` (a compiling doctest for the main entry points).
- **Fields and variants:** what the value means, plus any constraint ("Never empty",
  "Sorted ascending", "`None` until the first tick").
- **Intra-doc links** (``[`Grid::cell`]``) instead of bare names. They are checked by
  `rustdoc::broken_intra_doc_links`.
- `unsafe` blocks get a `// SAFETY:` comment that explains why the invariants hold.

Lints back this up: `missing_docs`, `clippy::missing_docs_in_private_items`,
`clippy::missing_errors_doc` and `clippy::missing_panics_doc` (pedantic).

## 2. No `mod.rs`

A module with children is `foo.rs` plus `foo/child.rs`, never `foo/mod.rs`. When you create a
submodule of a single-file module, keep `foo.rs` and add the `foo/` directory next to it.
`clippy::mod_module_files` denies `mod.rs`.

For integration tests, use `tests/it/main.rs` plus sibling modules, not `tests/common/mod.rs`.

## 3. No separator comments

Never write `// ------`, `// ======`, `// *** Section ***`, `//////` or similar banners. A
separator means the file has more than one concern. Split it instead: each section becomes a
submodule (`foo.rs` + `foo/section.rs`), or the section's items move to the module where they
belong. `task lint:separators` fails on them.

## 4. Strategic blank lines

Code is read in paragraphs. Separate the paragraphs:

- **Leave a blank line after the closing `}` of a block statement** (`if`, `match`, `for`,
  `while`, `loop`, a nested block) when another statement follows. Exceptions: `} else {`,
  a closing brace directly followed by another closing brace, and a tail expression that
  belongs to the block.
- **Blank lines between phases**: setup, then validation, then the main work, then building
  the result.
- **A blank line before a final tail expression or `return`** that follows multi-line logic.
- **A blank line after a group of `let` bindings** before the code that uses them.
- No blank line directly after an opening `{` or before a closing `}`. Never two blank lines
  in a row.

rustfmt keeps single blank lines and collapses doubles. Run `cargo fmt` after editing.

## 5. Extract helpers aggressively

- **One level of abstraction per function.** A function either orchestrates named steps, or
  does one low-level thing. Not both.
- If a block needs a comment to explain *what* it does, make it a function named after that
  comment, with the comment as its doc.
- **Complex loops become named steps.** Simulations, game loops, solvers and state machines are
  written as a short driver that calls documented step functions:
  `fn tick(&mut self) { self.apply_input(); self.integrate(dt); self.resolve_collisions(); self.emit_events(); }`.
- Deep nesting (more than 2 or 3 levels) is a signal: return early with guard clauses, extract
  the inner body, or turn the condition into a predicate method (`fn is_blocked(&self, ..) -> bool`).
- `match` arms longer than a few lines call a helper.
- Long parameter lists (`clippy::too_many_arguments`) become a documented struct.
- Thresholds: `too_many_lines` at 60 and `cognitive_complexity` at 15 (from `clippy.toml`).
  Hitting a threshold means: extract. Never raise the threshold.
- Helpers are private by default, documented like everything else, and placed next to their
  caller. When a group of helpers grows its own concern, it becomes a submodule (rule 2).

## 6. Pedantic clippy stays clean

Write code that passes `clippy::pedantic` with `-D warnings`. When a lint is genuinely wrong
in one spot, use a scoped `#[expect(clippy::lint_name, reason = "why this is fine here")]`
on the smallest item. Never use `#[allow]` (it never reports when it goes stale), and never
use module-level or crate-level suppression.

Common pedantic fixes:

- `must_use_candidate`: add `#[must_use]`.
- `module_name_repetitions`: rename `parser::ParserConfig` to `parser::Config`.
- Casts: use `From`/`TryFrom`, or `expect` with the invariant spelled out.
- `missing_errors_doc`: add `# Errors`.
- `needless_pass_by_value`: borrow.

## 7. Safe by default

Crate roots start with `#![forbid(unsafe_code)]`, unless the crate has a documented reason
to use unsafe. Reach for a safe API or crate first. Where unsafe is unavoidable:

- put `#[expect(unsafe_code, reason = "...")]` on the smallest item;
- write one unsafe operation per block;
- give each block a `// SAFETY:` comment;
- wrap it in a safe abstraction with documented invariants.

## 8. Diagrams in docs

Where structure or flow is non-obvious, add a ```` ```mermaid ```` block to the module or type
docs: state machines, pipelines, the step order of a simulation tick, a module graph. Keep it
under about 15 nodes, and update it in the same change as the code it describes.

## Before you finish

- Do all items you added or changed have doc comments, private ones included?
- No `mod.rs`, no separator comments, no new unsafe without `// SAFETY:`?
- Blank lines after block statements and between phases?
- Does any function mix abstraction levels, or need a "what" comment? Extract.
- Do `cargo fmt`, `cargo clippy --all-targets -- -D warnings` and `cargo doc --document-private-items`
  pass? (Use `task lint` and `task doc` if a Taskfile exists.)

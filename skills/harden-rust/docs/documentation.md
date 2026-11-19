# Documentation: diagrams and tested Markdown

## Mermaid diagrams

Diagrams are welcome wherever they explain structure or flow better than prose. Write them
as ```` ```mermaid ```` blocks. GitHub renders those natively, and with the setup below
docs.rs does too.

Good candidates (add them where they apply, and do not decorate):

| Diagram | Mermaid type | Where |
|---|---|---|
| Crate or module architecture, dependency graph | `flowchart` | Workspace README, `ARCHITECTURE.md`, crate-root docs |
| Data flow or pipeline (parse, then validate, then emit) | `flowchart LR` | Module docs of the pipeline |
| State machines (game states, protocol states) | `stateDiagram-v2` | Docs of the state enum |
| Call sequence or protocol exchange | `sequenceDiagram` | Docs of the client/server module |
| Simulation or game-loop step order, call graph of the tick | `flowchart TD` | Docs of the `tick`/`update` driver |
| Type relationships | `classDiagram` | Crate-root docs, if the type graph is non-obvious |
| Roadmap / milestones | `timeline` or `gantt` | README or `ROADMAP.md` |
| Release flow | `flowchart` | `CONTRIBUTING.md` or `RELEASING.md` |

Keep diagrams small (roughly 15 nodes or fewer). Split anything bigger. A diagram must match the
code. When you change the structure it shows, update the diagram in the same commit.

### docs.rs and local rendering

rustdoc emits a ```` ```mermaid ```` block as `<pre class="language-mermaid">`, and does not
doctest it. A small header script turns those blocks into diagrams:

1. Copy `templates/docs/mermaid.html` to `docs/mermaid.html` at the repo root. This applies
   only to library crates, because docs.rs renders those. Binary crates can still use
   mermaid in READMEs and other Markdown, which GitHub renders.
   In a workspace, each library crate packages its own `docs/mermaid.html` as a **symlink**
   to the root copy (`crates/foo/docs/mermaid.html -> ../../../docs/mermaid.html`). cargo
   follows it when packaging, and there is a single file to update. Replace `__MERMAID_VERSION__` with an exact version:
   `curl -s https://data.jsdelivr.com/v1/packages/npm/mermaid/resolved?specifier=11`.
   Never write the version from memory.
2. In each crate's `Cargo.toml`:

   ```toml
   [package.metadata.docs.rs]
   all-features = true
   rustdoc-args = ["--html-in-header", "docs/mermaid.html"]
   ```

   Also make sure `docs/mermaid.html` is packaged: `cargo package --list` must show it. If
   the crate uses `include`, add the file there.
3. Local `task doc` passes the same flag through `RUSTDOCFLAGS`, using the root copy
   (`--html-in-header {{.ROOT_DIR}}/docs/mermaid.html`). CI's `doc` job does the same.

The script loads mermaid from jsdelivr at view time. Offline doc viewing shows the diagram
source as a code block, which is still readable.

## README and Markdown as tested documentation

Code examples in Markdown rot unless they compile. Be sensible about which of the two
setups below fits:

- **The crate README is the crate docs** (a single-crate library whose README is written for
  users of that crate). In `lib.rs`:

  ```rust
  #![doc = include_str!("../README.md")]
  ```

  The README then renders on docs.rs, and its Rust code blocks run as doctests. Badges and
  absolute links work there too.
- **The README serves a different audience** (a workspace overview, a binary, an app README
  with screenshots, or a README that starts with install instructions). Test its examples
  without rendering it, using a private, doctest-only module:

  ```rust
  /// Doctests for the code examples in README.md (not part of the API).
  #[cfg(doctest)]
  #[doc = include_str!("../README.md")]
  mod readme_doctests {}
  ```

  Use the same pattern for guides (`docs/*.md`) that contain Rust examples, with one
  module per file. A guide that users should read on docs.rs can become a public,
  documented module instead: `pub mod guide { #![doc = include_str!("../docs/guide.md")] }`.
- **No Rust code in the Markdown, or only pseudo-code:** neither setup is needed.

Rules for Markdown that gets included:

- Tag non-Rust code blocks (` ```sh `, ` ```toml `, ` ```text `). An untagged block is
  doctested as Rust.
- Rust snippets that are not meant to run: ` ```rust,ignore ` with a reason in the
  surrounding text, ` ```rust,no_run ` (compiles, does not run), or ` ```rust,compile_fail `.
  Prefer making them compile, with hidden setup lines (`# use my_crate::Thing;`).
- Paths in `include_str!` are relative to the source file. A README outside the crate
  directory (the workspace root) is not packaged, so it breaks `cargo publish`. Only include
  files inside the crate.
- Workspace: each crate includes its own README. The root README stays GitHub-only.

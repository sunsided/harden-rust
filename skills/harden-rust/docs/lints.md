# Lints

## Lint table

Put the lint table from `templates/Cargo.lints.toml` into the root `Cargo.toml`. In a
workspace it goes under `[workspace.lints.*]`. Every member then inherits it with:

```toml
[lints]
workspace = true
```

A single crate without a workspace uses `[lints.*]` directly.

| Lint | Level | Why |
|---|---|---|
| `clippy::pedantic` | warn, `priority = -1` | Pedantic baseline. The priority lets single lints override the group. |
| `clippy::mod_module_files` | deny | Forbids `mod.rs`. rustfmt has no option for this, so clippy enforces it. |
| `missing_docs` | warn | Docs on every public item. |
| `clippy::missing_docs_in_private_items` | warn | Docs on private items too. No exceptions. |
| `clippy::allow_attributes_without_reason` | warn | Every `#[allow]` / `#[expect]` must say why. |
| `clippy::allow_attributes` | warn | Prefer `#[expect]`: it warns once it becomes stale. |
| `unsafe_code` | forbid (default) or deny | Safe by default (see "Unsafe code" below). |
| `clippy::undocumented_unsafe_blocks` | warn | Every `unsafe` block needs a `// SAFETY:` comment. |
| `clippy::multiple_unsafe_ops_per_block` | warn | One unsafe operation per block, each with its own justification. |
| `clippy::cognitive_complexity` | warn | Push toward helper extraction (threshold in `clippy.toml`). |
| `clippy::too_many_lines` | (pedantic) | Function length limit (threshold in `clippy.toml`). |
| `rustdoc::broken_intra_doc_links` | deny | Doc links must resolve. |
| `rustdoc::private_intra_doc_links` | allow | Private docs may link to private items. |

CI and `task lint` run `cargo clippy --workspace --all-targets --all-features -- -D warnings`.
So every warning fails the build, and the levels above mean "error in CI".

`cargo doc` runs with `--document-private-items` and `RUSTDOCFLAGS="-D warnings"`. That keeps
private docs valid too.

## Unsafe code

Safe by default: lean into `forbid` wherever it can be determined that no unsafe is needed,
and always on a new project.

- **Inventory:** run
  `grep -rnwE --include='*.rs' --exclude-dir=target 'unsafe|no_mangle|export_name|link_section' .`.
  The `unsafe_code` lint also flags those attributes.
- **No hits:** set `unsafe_code = "forbid"` in the workspace lints. Also put
  `#![forbid(unsafe_code)]` at the top of every crate root (`lib.rs`, `main.rs`, `bin/*.rs`).
  That attribute is what tools and readers look for, and it survives copy-paste out of the
  workspace. Add the safety-dance badge to the README (`docs/readme.md`).
- **Some crates need unsafe** (FFI, SIMD, allocators): ask which ones, and check whether a
  safe alternative exists. Set the workspace level to `deny`. In those crates only, put
  `#[expect(unsafe_code, reason = "...")]` on the smallest item or module. Every block needs
  `// SAFETY:` (`undocumented_unsafe_blocks`). The other crates still get
  `#![forbid(unsafe_code)]` and the badge.
- **Macro-generated unsafe:** `#[wasm_bindgen]` builds under `forbid` (checked with
  wasm-bindgen 0.2.130 on the host and `wasm32-unknown-unknown`). Other FFI or binding macros
  can expand to unsafe that `forbid` rejects. If a binding crate fails to build under
  `forbid`, give that crate `deny` with a scoped `#[expect]` around the bindings, and keep
  the core crate on `forbid`.
- Crates with unsafe benefit from Miri in CI (`cargo +nightly miri test`). Suggest it.

## No `mod.rs`

- Module `foo` with children: `src/foo.rs` plus `src/foo/bar.rs`. Never `src/foo/mod.rs`.
- Migrate: `git mv src/foo/mod.rs src/foo.rs`. Nothing else changes, because `mod foo;` resolves either way.
- **Integration tests.** With `--all-targets`, `mod_module_files` also flags `tests/common/mod.rs`.
  Use a single integration-test crate instead:

  ```text
  tests/
    it/
      main.rs      // mod common; mod parsing; mod roundtrip;
      common.rs
      parsing.rs
      roundtrip.rs
  ```

  Cargo treats `tests/it/main.rs` as the test target `it`. This layout also compiles one test
  binary instead of N, so builds are faster.

## Separator ban

Comments like `// -----`, `// =====`, `//////`, `// *****` mean a file holds several concerns.
Split the file into a module instead. Enforce the ban with `task lint:separators`:

```sh
! grep -rnE --include='*.rs' --exclude-dir=target --exclude-dir=.git \
    '^[[:space:]]*//+[[:space:]]*[-=*#~_/]{4,}' .
```

The regex matches comment lines that start with 4 or more separator characters. It uses POSIX
ERE, so the same command works with GNU and BSD grep, locally and in CI.

## clippy.toml

See `templates/clippy.toml`. Its thresholds are stricter than clippy's defaults
(`too-many-lines-threshold = 60`, `cognitive-complexity-threshold = 15`). Lower them further
for game or simulation code that tends to sprawl. Never raise them to silence a finding:
extract helpers instead.

## rustfmt.toml

See `templates/rustfmt.toml`. Use stable options only, so `cargo fmt` works on stable.
rustfmt cannot enforce blank lines after blocks or the no-`mod.rs` rule. `rust-style` covers
the blank lines, and clippy covers `mod.rs`.

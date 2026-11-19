# Licensing

Always ask with AskUserQuestion, unless the repo already has a license the user chose.
In that case, keep it and only fill in missing files.

## Schemes

| Option | `license =` | When |
|---|---|---|
| **EUPL/MPL (pushed)** | `"EUPL-1.2 OR MPL-2.0"` | Default suggestion. Promotes EUPL adoption. MPL-2.0 keeps it usable everywhere, because file-level copyleft lets proprietary code depend on the crate unmodified. |
| MIT/Apache (baseline) | `"MIT OR Apache-2.0"` | Ecosystem-foundational crates, or when the user wants zero friction. This is the Rust ecosystem convention. |

Ask like this: put "EUPL-1.2 OR MPL-2.0" first, note in one line what it means for users of
the crate, and offer "MIT OR Apache-2.0" as the baseline alternative.

**Examples as CC0-1.0** (optional, ask only when `examples/` exists, or examples are being
added now; otherwise drop the CC0 override from `REUSE.toml` and the CC0 note): make code under `examples/` (and, if wanted,
snippets in the README) public domain, so readers can copy them into anything. Express this
with REUSE (https://reuse.software) instead of a second Cargo `license` field. Cargo has one
license expression per crate.

## Files

- `LICENSES/<SPDX-ID>.txt` for every license used. Fetch the texts with
  `uvx reuse download --all` after writing `REUSE.toml`. Never type license texts from memory.
  If `uvx` is unavailable or not allowed, download the texts from SPDX:
  `curl -fsSo LICENSES/<ID>.txt https://raw.githubusercontent.com/spdx/license-list-data/main/text/<ID>.txt`.
- `REUSE.toml` (template): it maps paths to licenses. `__AUTHOR__` comes from `authors` in
  `Cargo.toml`, the git history's main author (`git shortlog -sne | head -1`), or "The
  <project> contributors". Ask when unsure. `__YEAR__` is the year of the first commit, or the
  current year for new projects. The default rule covers the whole repo
  with the project license, and an override marks `examples/**` as `CC0-1.0`.
- `Cargo.toml`: in a workspace, set `license = "..."` in `[workspace.package]` and
  `license.workspace = true` in members. In a single crate, set `license = "..."` in
  `[package]`. Do not set `license-file`.
- Published crates must ship the license texts. In a workspace, each member directory needs
  the texts too (`cargo package` only includes files inside the crate directory). Symlink
  them, for example `crates/foo/LICENSES -> ../../LICENSES`. cargo follows symlinks when
  packaging.
- README: add a "License" section stating the expression, and the CC0 note for examples.
  Add the standard contribution clause, adapted to the expression: "Unless you explicitly
  state otherwise, any contribution intentionally submitted for inclusion in this work by
  you shall be dual licensed as above, without any additional terms or conditions."
- Check: `uvx reuse lint` passes. `cargo deny check licenses` passes (it needs the project
  licenses in `deny.toml`). `cargo package --list -p <crate>` shows the `LICENSES/` files:
  dangling symlinks are silently skipped.

## Relicensing

Relicensing an existing project with outside contributors requires every contributor's
consent. Warn the user, and do not change the license expression of such a repo without
their explicit confirmation.

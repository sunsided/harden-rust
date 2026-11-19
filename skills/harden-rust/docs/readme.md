# README

Each published crate has its own README (`readme = "README.md"` in its `Cargo.toml`).
crates.io and docs.rs render it outside GitHub. So:

## Absolute URLs only

Every link to a repo file, and every image or screenshot, uses an absolute URL:

- Images: `https://raw.githubusercontent.com/__OWNER__/__REPO__/__BRANCH__/docs/screenshot.png`
- Files: `https://github.com/__OWNER__/__REPO__/blob/__BRANCH__/CONTRIBUTING.md`
- Directories: `https://github.com/__OWNER__/__REPO__/tree/__BRANCH__/examples`

In-page anchors (`#usage`) and `mailto:` are fine. A relative link whose target does not
exist is a dead link. Do not make it absolute; ask whether to remove it or create the target. `task lint:readme` and the CI `style` job
fail on relative `](...)` and `src="..."` targets in any `README.md`.

## Badges

Put them in one line under the title. Replace `__CRATE__` per crate.

```markdown
[![crates.io](https://img.shields.io/crates/v/__CRATE__.svg)](https://crates.io/crates/__CRATE__)
[![docs.rs](https://img.shields.io/docsrs/__CRATE__)](https://docs.rs/__CRATE__)
[![CI](https://github.com/__OWNER__/__REPO__/actions/workflows/ci.yml/badge.svg)](https://github.com/__OWNER__/__REPO__/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/__OWNER__/__REPO__/graph/badge.svg)](https://codecov.io/gh/__OWNER__/__REPO__)
[![MSRV](https://img.shields.io/crates/msrv/__CRATE__)](https://crates.io/crates/__CRATE__)
[![License](https://img.shields.io/crates/l/__CRATE__)](https://github.com/__OWNER__/__REPO__#license)
[![unsafe forbidden](https://img.shields.io/badge/unsafe-forbidden-success.svg)](https://github.com/rust-secure-code/safety-dance/)
```

- The "unsafe forbidden" badge goes only on crates whose root has `#![forbid(unsafe_code)]`.
- A crate that is not published yet: keep the crates.io, docs.rs and MSRV badges anyway. They
  render once the first release exists.
- Binary-only crates: drop the docs.rs badge.
- Workspace root README: CI and codecov badges, plus a static license badge, because the
  root is not a crate. For example:
  `https://img.shields.io/badge/license-EUPL--1.2%20OR%20MPL--2.0-blue`. Add a table of the
  member crates with their own crates.io badges.

## Sections

Title and badges, a one-paragraph pitch, Install / Usage (a short, compiling example),
Features (Cargo features, if any), MSRV, License (`docs/licensing.md`), Contributing.

README code examples are doctested, either as the crate docs or through a private
`#[cfg(doctest)]` module. Mermaid diagrams are welcome. See `docs/documentation.md`.

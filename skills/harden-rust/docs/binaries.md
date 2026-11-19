# Release binaries, SBOMs and attestations

Applies to repos that ship executables (a `[[bin]]` crate users install or download).
Template: `templates/.github/workflows/release-binaries.yml`.

## What it does

On the binary crate's release tag (pushed by release-plz):

1. **Build with `cargo auditable`** for each target. cargo auditable embeds the resolved
   dependency tree in the binary, so `cargo audit bin`, `syft` and `trivy` can scan the
   shipped artifact, not just `Cargo.lock`.
2. **Extract the SBOM from the binary itself** with `auditable2cdx <binary> > <bin>.cdx.json`
   (CycloneDX). Because it comes from the binary, the SBOM matches what ships.
3. **Attest (public repos):**
   - build provenance for the binary;
   - an SBOM attestation that binds `<bin>.cdx.json` to the binary;
   - build provenance for the archive.

   All three use `actions/attest`, with permissions `id-token: write`,
   `attestations: write` and `artifact-metadata: write`. Attestation is skipped on private
   repos, where it needs GitHub Enterprise Cloud.
4. **Package** the binary, its SBOM, the README and `LICENSES/`: a `.tar.gz` for Unix and a
   `.zip` for Windows. Name the archive `<bin>-<tag>-<target>`.
5. **Attach** every archive to the GitHub Release that release-plz created (the job waits
   for the Release to appear).

Users verify a download with:

```sh
gh attestation verify <archive-or-binary> --repo __OWNER__/__REPO__
```

Put that line in the README's install section.

## Targets

Ask with AskUserQuestion (multiSelect) which platforms to ship, and recommend the full list.
**`x86_64-unknown-linux-musl` is always included**: it is statically linked, so it runs on any
Linux regardless of glibc version. If an aarch64 Linux build ships, its musl twin
(`aarch64-unknown-linux-musl`) ships too.

| Target | Runner | Notes |
|---|---|---|
| `x86_64-unknown-linux-gnu` | `ubuntu-latest` | |
| `x86_64-unknown-linux-musl` | `ubuntu-latest` | always; `taiki-e/setup-cross-toolchain-action` provides the musl toolchain |
| `aarch64-unknown-linux-gnu` | `ubuntu-24.04-arm` | native arm runner |
| `aarch64-unknown-linux-musl` | `ubuntu-24.04-arm` | with the aarch64 gnu build |
| `aarch64-apple-darwin` | `macos-latest` | |
| `x86_64-apple-darwin` | `macos-latest` | cross-compiled on the arm runner |
| `x86_64-pc-windows-msvc` | `windows-latest` | `.exe`, `.zip` |

C dependencies (openssl-sys and similar) can break the musl builds. Prefer rustls, or use
vendored features. Otherwise `setup-cross-toolchain-action` handles most cases.

## Placeholders

- `__BIN__` is the binary name.
- `__BIN_CRATE__` is its package.
- `__BIN_TAG_PATTERN__` is that crate's tag: `v[0-9]+.[0-9]+.[0-9]+` for a single crate, or
  `<crate>-v[0-9]+.[0-9]+.[0-9]+` in a workspace.

Several binaries: add a matrix dimension, or put a second job behind its own tag pattern.

## Local

`task dist` (add it when this workflow is used) builds the host binary with
`cargo auditable build --release --locked`. `task dist:sbom` writes the SBOM with
`auditable2cdx`. Preconditions point to `cargo install --locked cargo-auditable auditable2cdx`.

## WASM is different

Do **not** use cargo auditable for wasm. `auditable2cdx` cannot extract the data from a
`.wasm` module, and the embedded section only adds size to a download that users fetch
on every page load. Use **cargo-sbom** instead, which builds the SBOM from Cargo metadata:

```sh
cargo sbom --cargo-package <wasm-crate> --output-format cyclone_dx_json_1_6 > <crate>.cdx.json
```

Attest the `.wasm` file (or the npm tarball) with that SBOM, the same way. See
`docs/wasm.md`.

Sources: https://github.com/rust-secure-code/cargo-auditable,
https://github.com/actions/attest, https://github.com/psastras/sbom-rs,
https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations

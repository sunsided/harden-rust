# WASM (browser, WASI, web frontends)

Applies when the inventory finds any of these: `crate-type = ["cdylib"]`, `wasm-bindgen`,
`Trunk.toml`, a `package.json` next to or above a crate, `wasm32-*` in `.cargo/config.toml`
or CI.

## Decision: which targets (AskUserQuestion, multiSelect)

| Target | Runtime | Notes |
|---|---|---|
| `wasm32-unknown-unknown` + wasm-bindgen | Browsers, Vite/SvelteKit apps, trunk apps | No WASI, no threads, no filesystem. |
| `wasm32-wasip1` | WASI hosts **without threads**, for example the VS Code WASI host in vscode.dev / github.dev, wasmtime | Never assume threads. Threaded code needs a cargo feature that is off for this target. |
| `wasm32-wasip1-threads` | WASI hosts with thread support | Only if the user names a host that supports it. |
| `wasm32-wasip2` | Component-model hosts (wasmtime, WASI 0.2 runtimes) | Only on request. |

## Code rules for wasm-compatible crates

- **No threads by default.** Put `std::thread`, `rayon` and blocking channels behind a
  `parallel` (or `threads`) feature, and keep it out of wasm builds. CI checks the wasm
  target with that feature off.
- **Time:** `std::time::Instant::now()` panics on `wasm32-unknown-unknown`. Use `web-time`
  (drop-in) in code that runs in the browser.
- **Randomness:** `getrandom` 0.3 on `wasm32-unknown-unknown` needs the `wasm_js` feature
  **and** `--cfg getrandom_backend="wasm_js"` (in `.cargo/config.toml`, scoped to that target).
  WASI targets need neither.
- **No panicking on unsupported platforms at runtime.** Prefer `cfg(target_family = "wasm")` /
  `cfg(target_os = "wasi")` at compile time, so a target either compiles correctly or
  fails to compile.
- Keep the wasm-bindgen surface in a thin `*-wasm` crate (`cdylib`) on top of a pure-Rust core
  crate. The core keeps nextest, coverage, fuzz and proptest. The binding crate gets
  wasm-bindgen tests.

## Tooling

- **wasm-bindgen CLI version must match the `wasm-bindgen` crate in `Cargo.lock` exactly.**
  Install it pinned, for example in CI with `taiki-e/install-action` and
  `tool: wasm-bindgen-cli@<version from Cargo.lock>`. Bump both together; Dependabot groups
  help with that.
- **wasm-pack** is fine for existing setups (`wasm-pack build --target web|bundler`,
  `wasm-pack test --headless --firefox`). The rustwasm working group was sunset in 2025, and
  wasm-pack moved to new maintainers. For new setups, `cargo build --target
  wasm32-unknown-unknown` + `wasm-bindgen` CLI + `wasm-opt` (binaryen) gives the same result
  with fewer moving parts. Ask if unsure.
- **trunk** for pure-Rust frontends (Leptos, Yew, egui/eframe): `Trunk.toml` at the crate,
  `trunk build --release`, `trunk serve` locally. CI builds with `trunk build --release`.
- **WASI tests:** run `cargo test` under wasmtime:
  `CARGO_TARGET_WASM32_WASIP1_RUNNER=wasmtime cargo test --target wasm32-wasip1 -p <core>`.
  nextest does not run wasm targets.
- **Browser tests:** `wasm-bindgen-test` with `wasm-bindgen-test-runner` (or `wasm-pack test`)
  in headless Firefox or Chrome.

## SvelteKit / Vite / yarn / corepack

- **Package manager:** respect `packageManager` in `package.json` (for example
  `"yarn@4.x.y+sha512..."`). Never switch to npm or pnpm. Run `corepack enable` before any
  `yarn` call, in CI *before* `actions/setup-node` with `cache: yarn` (the cache step runs
  yarn). Node 25 and later no longer bundle Corepack. Locally, install it
  (`npm install -g corepack`) or use an LTS that still ships it. In CI, the runner's
  preinstalled Node provides it. Avoid `npm install -g` in workflows (zizmor `adhoc-packages`).
- **Install:** `yarn install --immutable` in CI.
- **Wiring the wasm package in:**
  - `wasm-pack build --target web --out-dir ../web/src/lib/wasm` (or a `pkg/` referenced as
    `"my-wasm": "portal:../crates/my-wasm/pkg"` / `"link:"` in Yarn Berry). Generated output is
    gitignored and rebuilt by a `wasm:build` task that the web `dev`/`build` tasks depend on.
  - `--target web` needs no Vite plugin: `import init, { f } from '$lib/wasm/my_wasm.js'`, then
    `await init()`. `--target bundler` needs `vite-plugin-wasm` (+ `vite-plugin-top-level-await`
    for older browsers).
  - **SSR:** SvelteKit renders on the server in Node, where browser wasm-bindgen glue fails.
    Load the module only in the browser (`onMount`, or `if (browser)`), or set
    `export const ssr = false` on routes that need it.
  - Vite dev server: allow serving the wasm output dir (`server.fs.allow`) when it sits
    outside the web root.
- **Taskfile:** include the web project as a namespace (`web:`). If the `taskfile-authoring`
  skill is available, follow its monorepo and web-yarn examples. Add `wasm:check`,
  `wasm:test` and `wasm:build`, and make `web:build` depend on `wasm:build`. Add the wasm and
  web checks to `task ci`.
- **Dependabot:** add an `npm` ecosystem entry for the web directory. It handles yarn
  lockfiles. Use the same cooldown and grouping.
- **README / badges:** if the app is deployed (GitHub Pages, Cloudflare), add a live-demo
  link, as an absolute URL.

## Publishing to npm, SBOM, attestation

A wasm package that ships to npm gets its own `publish-npm.yml`, following the pattern of
`publish-crates-io.yml`:

- It runs on the package's release tag, in an `npm` environment that is restricted to that
  tag pattern (`docs/github.md`).
- It has a `verify` job, and the publish job `needs:` it.
- The publish job runs `npm publish --provenance` with npm trusted publishing (OIDC,
  `id-token: write`, no `NPM_TOKEN`). That needs the package's trusted-publisher setting on
  npmjs.com to name `publish-npm.yml` and the `npm` environment.
- SBOM: `cargo sbom --cargo-package <crate> --output-format cyclone_dx_json_1_6`
  (**cargo-sbom**; not cargo auditable, see `docs/binaries.md`). Attest the `.wasm`
  file and the packed tarball with `actions/attest` (provenance, plus `sbom-path`), and
  attach the tarball and SBOM to the GitHub Release.
- Write it when the user asks for npm publishing. Lint and pin it like the other workflows.

## CI

Template: `templates/.github/workflows/wasm.yml`. It runs clippy per wasm target (with the
threads feature off), WASI tests under wasmtime, a browser test via wasm-bindgen-test, and
the web build. Delete the jobs that do not apply, and set `__WASM_CRATE__` / `__CORE_CRATE__` /
`__WEB_DIR__`. Keep it a separate workflow, so wasm failures are easy to spot. Add its job
names to the branch-protection list.

Sources: Corepack bundling ends before Node 25 (https://github.com/nodejs/corepack#readme);
getrandom's `wasm_js` backend (https://docs.rs/getrandom/latest/getrandom/); `web-time` as an
`Instant` replacement (https://docs.rs/web-time/latest/web_time/); wasm-bindgen's new home
(https://github.com/wasm-bindgen/wasm-bindgen), wasm-pack's (https://github.com/drager/wasm-pack),
and the archived rustwasm org (https://github.com/rustwasm). Re-check these when applying,
because they move fast.

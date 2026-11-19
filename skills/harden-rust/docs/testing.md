# Fuzzing, property tests, benchmarks

## Decision (ask the user to confirm the candidates)

Preference order: **fuzz + proptest**, then **either one**, then **none**. Find candidates by
reading the public API:

| Signal in the code | Use |
|---|---|
| Parses or decodes untrusted bytes or strings (`&[u8]`, `&str`, `Read`) | fuzz target, plus proptest round-trips |
| Encode/decode or serialize/deserialize pairs | proptest round-trip (`decode(encode(x)) == x`), fuzz the decoder |
| Data structures with invariants (sorted, balanced, bounded) | proptest over operation sequences, optionally fuzz with `arbitrary` |
| Numeric or algorithmic code with an oracle or reference implementation | proptest against the oracle |
| State machines, simulations, games (step functions) | proptest invariants over random action sequences; fuzz `Arbitrary` action lists |
| Thin glue, I/O wrappers, CLI arg plumbing | none; say so in the gap table |

Present the candidates with AskUserQuestion (multiSelect), with the recommended ones first.

## Fuzzing (cargo-fuzz)

- Run `cargo +nightly fuzz init` in the **crate** directory, then
  `cargo +nightly fuzz add <target>`, and delete the placeholder `fuzz_target_1`.
  - **Virtual workspace:** init from the crate that is fuzzed, then move the generated
    `fuzz/` to the repo root, or keep it next to the crate and adjust the include,
    `ci.yml`, Dependabot and `codecov.yml` paths. The templates assume root `fuzz/`.
  - Fix the dependency `path` to point at the crate.
  - Make sure `fuzz/Cargo.toml` has an empty `[workspace]` table. Recent cargo-fuzz versions
    do not always add it, and without it cargo complains that the package believes it is in
    a workspace.
  - Keep it out of the root workspace's `members`.
  - Add `[lints]` to `fuzz/Cargo.toml` (copy the table; `workspace = true` does not reach a
    separate workspace). `task fuzz:lint` and the CI `fuzz` job run fmt and clippy there.
- Targets use `libfuzzer_sys::fuzz_target!`. For structured input, use
  `arbitrary::Arbitrary` derives. Add an `arbitrary` feature to the library rather than a
  hard dependency.
- Add `templates/fuzz/Taskfile.dist.yaml`. The root Taskfile includes it as `fuzz:`.
- Keep the `.gitignore` that cargo-fuzz generates (`target`, `corpus`, `artifacts`,
  `coverage`). Generated corpora are not committed. Curated seed inputs that are worth
  keeping go in with `git add -f fuzz/corpus/<target>/<file>`. A crash reproducer becomes a
  regular regression test in the crate.
- CI builds the targets (`fuzz` job). Real fuzzing runs locally (`task fuzz:smoke` or
  `task fuzz:run TARGET=...`), or in a scheduled job if the user wants one.
- Fuzz targets follow `rust-style` too: doc comments on the target and its helpers.

## Property tests (proptest)

- `proptest` as a dev-dependency. Put strategies in a `tests/it/strategies.rs` module, or in a
  `#[cfg(test)]` module next to the type.
- Keep `PROPTEST_CASES` at the default in CI. `task test:prop` raises it (default 10000) for
  deeper local runs.
- Commit the `proptest-regressions/` files. They are reproducible failure seeds.

## Benchmarks

- Default: `criterion` for statistically sound comparisons. `divan` is fine for simple
  micro-benchmarks.
- Put them in `benches/<name>.rs`, with a `[[bench]] name = "<name>" harness = false` entry in
  `Cargo.toml`.
- **criterion without its macros:** `criterion_group!` and `criterion_main!` generate
  undocumented functions, which fail `missing_docs`. Write a documented `main` instead:

  ```rust
  /// Runs every benchmark in this file with criterion's command-line flags.
  fn main() {
      let mut criterion = Criterion::default().configure_from_args();

      bench_step(&mut criterion);
      criterion.final_summary();
  }
  ```
- proptest strategies and assertions need `Debug` on the types involved. Derive it, and
  document why when the derive exists only for tests.
- Benchmark the hot paths named by the user or found in the code (parsers, simulation steps,
  solvers). Do not benchmark trivial getters.
- Run with `task bench`. CI compiles the benches (`--all-targets` in clippy and build) but does
  not run them, because shared runners are too noisy.

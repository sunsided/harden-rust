# Repository and crate metadata

Every repo and every publishable crate has a proper description and keywords. They show up
in crates.io search, on docs.rs, in GitHub search and on the repo page.

## Where they live

| Place | Fields | Limits |
|---|---|---|
| `Cargo.toml` (each publishable crate) | `description`, `keywords`, `categories`, `repository`, `homepage` (optional), `documentation` (optional; docs.rs is the default) | `keywords`: at most 5, each at most 20 chars, ASCII letters/digits/`_`/`-`/`+`. `categories`: valid slugs from https://crates.io/api/v1/category_slugs, at most 5. |
| GitHub repo | description, topics, website | Topics: lowercase, hyphens, at most 50 chars each, at most 20 topics. |

Shared values may go in `[workspace.package]` (`repository`, `homepage`; `keywords` and
`categories` too, if they truly fit every crate). Each crate keeps its own `description`.

## Missing GitHub repo

If `gh repo view` fails, the repo does not exist yet (or the remote points somewhere
else). Draft the description and topics anyway, and put `gh repo create` plus
`gh repo edit` in the Phase 6 checklist. Never create the repo without explicit
confirmation.

## Inventory

```sh
cargo metadata --no-deps --format-version 1   # description, keywords, categories per package
gh repo view --json description,repositoryTopics,homepageUrl
```

## Rules

1. **Missing:** draft the values from the README pitch and the public API, then add them.
   For Cargo.toml this is a normal file change, covered by the Phase 2 plan confirmation.
2. **Deviating strongly:** this covers four cases:
   - the GitHub description and the main crate's `description` say different things;
   - keywords and topics do not overlap;
   - the metadata describes an old scope of the project;
   - the categories do not match what the crate does.

   Do not overwrite. Suggest an aligned version with AskUserQuestion, showing current vs
   proposed side by side.
3. **Minor wording differences** are fine. Do not churn them.
4. **Description style:** one sentence, under about 100 chars, says what it does and for whom.
   No "A Rust crate for...", and no trailing period in GitHub descriptions.
5. **Keywords and topics:** domain terms users would search for. Not `rust` as a crate
   keyword, since every crate is Rust. `rust` is a fine GitHub topic. Reuse the crate keywords
   as topics, and add ecosystem topics (`wasm`, `sveltekit`, `cli`) where they apply.
6. **Applying GitHub changes is outward-facing.** Confirm first, then:

   ```sh
   gh repo edit --description "..." --homepage "..." --add-topic a --add-topic b
   ```

   If the user prefers to do it themselves, list it in the Phase 6 checklist instead.

Workspace root README and GitHub description describe the whole repo. Member crates
describe themselves.

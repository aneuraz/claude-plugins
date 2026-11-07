# The facts gate judges every runner from test reports

Date: 2026-11-07. Status: approved by the owner, revised after an independent review. **Revises** `2026-11-06-claude-plugins-design.md`, *The tooling package*, `facts`: the package does not absorb `capture`'s execution machinery (its cargo/swift output counters, parallel pool, timeouts); it absorbs `candle-pseudo`'s `--exclude-requires` with the meaning given below.

## Why

Plan 3 moves `candle-app`, `candle-pseudo`, `capture`, `fhirforge`, `fouille` and `korps` onto the marketplace and, where they have a facts gate, onto `cpt facts`. Measured 2026-11-07:

- **`capture`** (Rust workspace, Swift package, Tauri front end) has its own 988-line checker that *runs* each `@implemented` fact's check through a shell and counts the tests the output reports. `cpt facts` would fault 129 of its 130 checks as unknown runners (one is `@draft`), `--orphans` included.
- **`candle-app`** (TypeScript) judges its 146 `@implemented` vitest and Playwright facts from reports its own `runner_reports.py` converts; `cpt facts --reports` reads only pytest reports.
- **`candle-pseudo`** runs its gate in local mode in CI (`facts_check.py --exclude-requires parhaf,baseline`).

## The rule (owner, 2026-11-07)

**A facts gate never runs a fact's check.** As in `candle`, each CI test job writes a report of its tests' outcomes, and the gate judges each fact from those reports (`cpt facts --reports DIR`). A check is a *selector*: it names, in the runner's own syntax, the tests that prove the fact, so a developer can run it by hand.

- **Local mode stays, as a developer tool, never as a gate** (owner, 2026-11-07). `cpt facts` without `--reports` runs selected checks (pytest, vitest and, new, cargo); it gains `--only <ID>` (repeatable; an unknown id is an error). Every repository's CI gates with `--reports`, `candle-pseudo`'s included.
- **`--exclude-requires <list>`** applies in reports mode: a fact whose `requires:` names a listed resource is printed as *not run* with its requirement, and is not red. When the flag is given, each fact's `-m` markers must equal its `requires` (as `candle-pseudo` audits today).
- **`capture`'s checks that are not test selectors** (`grep` on files, `[ -z "$(cargo run …)" ]`, `[ "$(npm … vitest …)" = N ]`) are **rewritten as tests** in `capture` (owner, 2026-11-07); the fact's `check` names those tests. A check that is not a test selector is a fault.
- **Whole-file vitest selections** (`capture`'s UI facts) keep the general rule, *at least one entry, all passed*; their exact test counts are not carried over (owner, 2026-11-07).

## Reports

- **One normalized format**, a JSON file per CI job: `{"<id>": {"title": "<own title>", "outcome": "<outcome>", "file": "<repo-relative file>", "binary": "<binary id>"}}`, `file` and `binary` present when the runner has them. `candle`'s pytest plugin format (`{"<node id>": "<outcome>"}`) stays readable unchanged.
- **Converters**, `cpt facts report <runner> <raw> <out>` (a subcommand group under `facts`; `cpt facts --orphans` and `--reports` keep working):
  - `vitest`: vitest JSON (`testResults[].name`, `assertionResults[].{ancestorTitles,title,status}`); id `<file>::<describe> > … > <title>`; an optional `--root <dir>` makes `file` relative to the repository when vitest runs in a subdirectory (`capture`'s `app/`).
  - `playwright`: Playwright JSON (`suites[]` recursively, `specs[].{title,file,tests[].status}`, file relative to the configured test directory, given by `--test-dir`).
  - `nextest`: cargo-nextest JUnit XML; `binary` = `<package>::<test binary>` for an integration test, `<package>` for a `--lib` binary; id `<binary>::<test path>`; `title` = the test path. Ignored tests are not entries.
- Outcome mapping as in `candle-app`'s converter (flaky → failed; pending/todo → skipped); a duplicate id keeps the worse outcome.
- No Swift converter in this plan: `capture`'s CI gates its `core` (Rust) facts only, as today (`--owner core`); its `agent` (Swift) facts stay ungated.

## Matching a check to report entries

A check part selects entries; a fact is green when **every** part selects at least one entry and **every** selected entry passed. Parts are joined by `&&`.

| Runner | Check form | Selected entries |
|---|---|---|
| pytest | as today, the forms of `[facts] check_forms` | as today |
| vitest / Playwright, by id | `pnpm exec vitest run <file> -t "<ID>"`, `pnpm exec playwright test <file> -g "<ID>"` (forms configurable) | entries whose `file` is `<file>` and whose own title starts with `"<ID> "`; the `-t`/`-g` pattern is not evaluated |
| vitest, whole files | `npm --prefix <dir> exec vitest run <file> [<file> …]`, optionally `-t "<pattern>"` | entries whose `file` is one of the files (relative to `<dir>`), filtered by the pattern as vitest does (substring of the full name) when given |
| cargo | `cargo test -p <pkg> (--test <bin> \| --lib) [--release] [-- <f1> … <fn>]` | entries whose `binary` is `<pkg>::<bin>` (or `<pkg>` for `--lib`), in the reports of the matching profile; with filters, **each** filter selects ≥ 1 entry (substring of the test path, as libtest without `--exact`); without filters, every entry of the binary |

`--release` checks read only the reports listed in `[facts] release_reports`; other cargo checks read only the others.

**Static audit**, in every mode including `--orphans`: the form is one the project declares; for cargo, the `--test <bin>` file `crates/<pkg>/tests/<bin>.rs` (or the crate's `src/` for `--lib`) exists and each filter literal appears in it; `--exact`, `--ignored`, `--nocapture`, `--features` and other flags are refused; for vitest/Playwright by id, the id in the check equals the fact's id and at least one test in the file carries it (`candle-app`'s audit).

## Per-project configuration (`.claude/project.toml`, `[facts]`)

- `check_forms` generalizes to forms per runner (pytest, vitest, playwright, cargo).
- `release_reports`: report names produced by release-profile jobs.
- `orphans`: `"design-text"` (default: an id appears in its sibling `-design.md`) or `"facts-lines"` (`capture`'s: ids cited on `*Facts :*` lines of any spec; ids may carry a letter suffix like `OCR-007a`; prefixes may contain digits; ranges `X-NNN à|to X-NNN`; an id cited but defined by no fact is a *dangling* fault).
- `owner = true`: facts carry an `owner` field; `cpt facts --owner <name>` keeps those facts.
- `schema`: allowed and required field lists and the closed set of statuses; an `@implemented` fact without a `check`, an unknown field or status, and a duplicate id are faults. `capture`'s `timeout` field is allowed and ignored (nothing is executed).

Facts not judged under `--implemented` are listed as pending, with their status.

## CI for `capture`

- A separate **gate job**, `needs:` the test jobs, downloads their report artifacts and runs `uvx --from "claude-plugins-tools @ git+https://github.com/aneuraz/claude-plugins@<sha>" cpt facts --reports reports --implemented --owner core` on the self-hosted macOS runner; uv comes from `astral-sh/setup-uv` and fetches Python 3.14. `--orphans` runs the same way in the `core` job.
- Rust tests run under **cargo-nextest** with one JUnit profile per run: the debug run, the release proptest run (`PROPTEST_CASES=1000 … --release -- prop_`) and the release bench (`p95_under_100ms`, run alone), each its own report. `cargo test --doc` stays as its own step (nextest runs no doctests; no fact names one). The front end's vitest writes a JSON report converted with `--root app`.
- nextest runs test binaries concurrently and each test in its own process: the load-sensitive tests (STO-005, the debug bench guard, the keychain tests) get a serial test group in the nextest profile.
- **Shadow run before switching:** the old gate and the new one run side by side on the same commit; every fact's verdict must agree, or the difference is explained (a stricter filter rule that turns a fact red is a real finding).

## Not in scope

- `candle-legacy` (`candle-qa` locally) is not touched (owner, 2026-11-07).
- `capture`'s and `fhirforge`'s `SECURITY.md` stay as they are (owner, 2026-11-07).
- A Swift report converter; `capture`'s `--list`, `--self-test`, `--jobs`, `--timeout`.
- `cpt wiki search` ranking.

## Left to the builder

How each rewritten `capture` shell check becomes a test (a Rust test reading a file, a test running the i18n emit check, a vitest test); the nextest profile names and the serial group's membership; the wording of new faults.

## Amendments after the plan review (2026-11-07)

- **`check_forms` stays readable as a flat list** of strings (the pytest forms, as `candle` declares it today); per-runner forms are optional sub-tables (`[facts.check_forms] vitest = […]`).
- **Swift checks** have a declared `swift` form that the static audit checks (form only) and the gate never judges; `capture`'s `agent` facts stay ungated. `--orphans` traces every fact; the form audit applies to every fact.
- **Cargo audit paths** come from `cargo metadata` (workspace members' manifest directories), not a fixed `crates/<pkg>/`; a filter containing `::` is checked by its last segment.
- **`--only` is repeatable.** When `--exclude-requires` is given, the markers audit (`-m` markers equal `requires`) runs in reports mode too.
- **Whole-file vitest**: the form is the project's own command (`npm --prefix app test -- <files…> [-t <regex>]` for `capture`, verified on the runner); `-t` is a regex over the full name, as vitest; a check that names no file is not a whole-file form and is rewritten to name its files. vitest's `testResults[].name` is absolute; the converter makes it relative to the repository root.
- **`capture`'s `SECURITY.md` §7**: only the lines that name the gate's command change, to describe `cpt facts --reports` (owner, 2026-11-07); the rest of the file and its numbering stay.

# The facts gate judges every runner from test reports

Date: 2026-11-07. Status: draft, for plan 3. Extends `2026-11-06-claude-plugins-design.md` (*The tooling package*, `facts`).

## Why

Plan 3 moves `candle-app`, `candle-pseudo`, `capture`, `fhirforge`, `fouille` and `korps` onto the marketplace and, where they have a facts gate, onto `cpt facts`. Two of them cannot use `cpt facts` today (measured 2026-11-07):

- **`capture`** (Rust workspace, Swift package, a Tauri front end) has its own 988-line checker that *runs* each `@implemented` fact's check through a shell, counts the tests the output reports (`cargo test` result lines; XCTest `Executed N tests`), refuses a command that certified nothing, and runs facts in parallel with timeouts. `cpt facts` would fault every one of its 130 checks as an unknown runner, `--orphans` included.
- **`candle-app`** (TypeScript) judges its 146 `@implemented` vitest and Playwright facts from reports its own `runner_reports.py` converts; `cpt facts --reports` reads only pytest reports, so every one would read `not run`.

## The rule (owner, 2026-11-07)

**`cpt facts` never runs a fact's check.** As in `candle`, each CI test job writes a report of its tests' outcomes, and the gate judges each fact from those reports (`cpt facts --reports DIR`). A check is a *selector*: it names the tests that prove the fact, in the runner's own command syntax, so a developer can still run it by hand.

Consequences:

- `capture`'s execution machinery (shell runs, output counting, parallel pool, `--jobs`, `--timeout`, prebuild) is not ported.
- `capture`'s checks that are not test selectors — `grep` on files, `[ -z "$(cargo run …)" ]`, `[ "$(npm … vitest …)" = N ]` — are **rewritten as tests** in `capture` (owner, 2026-11-07), and the fact's `check` names those tests. A check that is not a test selector is a fault.

## Reports

- **One normalized format** read by the gate: a JSON file per CI job, `{"<test id>": {"title": "<own title>", "outcome": "passed" | "failed" | "skipped" | …}}`. `candle`'s pytest plugin format (`{"<node id>": "<outcome>"}`) stays readable unchanged.
- **Converters**, a subcommand `cpt facts report <runner> <raw> <out>`, write that format from the runner's own output:
  - `vitest`: vitest JSON (`testResults[].name`, `assertionResults[].{ancestorTitles,title,status}`); id `<repo-relative file>::<describe> > … > <title>` (as `candle-app`'s converter).
  - `playwright`: Playwright JSON (`suites[]` recursively, `specs[].{title,file,tests[].status}`, file relative to the configured test directory); the same id form.
  - `nextest`: cargo-nextest JUnit XML; id `<binary id>::<test path>` where the binary id is `<package>::<test binary>` for an integration test and `<package>` for a `--lib` binary.
  - `swift`: `swift test` xUnit XML (`--xunit-output`), or its console lines when xUnit is unavailable (to measure on the runner); id `<Target>.<Class>/<method>`.
- Outcome mapping per runner as in `candle-app`'s converter (flaky → failed; pending/todo → skipped); when one id appears twice, the worse outcome wins.

## Matching a check to report entries

Per runner, a check part selects report entries; a fact is green when **every** part selects at least one entry and **every** selected entry passed. A part joined by `&&` is one more part.

| Runner | Check form | Selected entries |
|---|---|---|
| pytest | as today (`<file>::<function>`, the fixed forms of `[facts] check_forms`) | as today |
| vitest / Playwright | `pnpm exec vitest run <file> -t "<ID>"`, `pnpm exec playwright test <file> -g "<ID>"` (forms configurable) | entries of `<file>` whose own title starts with `"<ID> "` (`candle-app`'s rule; the `-t`/`-g` pattern itself is not evaluated) |
| cargo | `cargo test -p <pkg> (--test <bin> \| --lib) [--release] [-- <f1> … <fn>]` | entries of binary `<pkg>::<bin>` (or `<pkg>`) in the report of the matching profile; with filters, **each** filter must select ≥ 1 entry (substring of the test path), stronger than today's "count ≥ number of filters"; without filters, every entry of the binary |
| swift | `swift test --package-path <dir> --filter '<regex>'` | entries whose id matches the regex (unanchored search, as SwiftPM) |

`--release` selects the report of a job run with the release profile (named by `[facts] release_report`).

## Per-project configuration (`.claude/project.toml`, `[facts]`)

- `check_forms` (existing, pytest) generalizes to forms per runner.
- `orphans`: `"design-text"` (default, today's: an id must appear in its sibling `-design.md`) or `"facts-lines"` (`capture`'s: ids cited on `*Facts :*` lines of any spec, ids may carry a letter suffix like `OCR-007a`, prefixes may contain digits, and an id cited but defined by no fact is a *dangling* fault).
- `owner`: whether facts carry an `owner` field; `cpt facts --owner <name>` keeps those facts (`capture`'s CI gates `core`).
- `schema`: optional allowed and required field lists, refused fields and duplicate ids reported (`capture`'s closed schema).

`--reports` mode keeps today's flags; `capture` and `candle-app` pass `--implemented` (both gate `@implemented` facts only, report others as pending).

## CI for `capture`

The self-hosted macOS runner installs uv (`astral-sh/setup-uv`, macOS ARM64) and runs `uvx --from "claude-plugins-tools @ git+https://github.com/aneuraz/claude-plugins@<sha>" cpt facts …`; uv fetches Python 3.14. The runner gains cargo-nextest; Rust tests run under nextest with a JUnit profile, Swift tests with `--xunit-output`, the front end's vitest with a JSON reporter. Whether nextest's process-per-test model and SwiftPM's xUnit output (historically tied to `--parallel`) change any test's behaviour is measured before switching.

## Not in scope

- `candle-legacy` (renamed `candle-qa` locally) is not touched (owner, 2026-11-07).
- `capture`'s and `fhirforge`'s `SECURITY.md` stay as they are; replacing their sections by pack citations is a later plan (owner, 2026-11-07).
- `cpt wiki search` ranking.

## Left to the builder

The exact normalized id escaping; the converter of SwiftPM console output if xUnit is unavailable; how a rewritten `capture` shell check is turned into a test (Rust test reading the file, a test running the emit check, vitest tests with the count asserted inside); the wording of new faults.

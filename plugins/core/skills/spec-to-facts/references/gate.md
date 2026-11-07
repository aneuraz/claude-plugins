# The report and the gate

Two parts. Each test job writes a report of its tests' outcomes, and one gate job reads every report. The gate runs no test, so a suite is never re-run to re-prove a fact.

## Part 1, the report

A report is a JSON file per test job, written when the job's test session ends, and uploaded as an artifact named after the job. Two formats, which one directory may mix:

- `{test_id: outcome}`: the test id is the runner's own, in the form the `check` of a fact uses; the outcome is one of `passed`, `skipped`, `failed`, `error`, `xfailed`, `xpassed`. pytest writes it with a plugin (`rules-python:facts-report-plugin`).
- `{id: {"title", "outcome", "file", "binary"}}`: the normalized format, with `file` (repository-relative) and `binary` when the runner has them. A runner that writes its own format is converted: `cpt facts report vitest|playwright|nextest <raw> <out>` (`--root DIR` for vitest run in a subdirectory, `--test-dir DIR` for Playwright). A flaky test converts to `failed`, a pending or todo one to `skipped`, and a duplicate id keeps the worse outcome.

The job passes the report path through its environment, so the job's command, and so each fact's `check`, is unchanged.

## Part 2, the gate

**The gate never runs a check.** A `check` is a selector: it names, in the runner's own syntax, the tests that prove the fact, so a developer can run it by hand. The gate judges each fact from the reports (`facts --reports DIR`, through the project's `cpt` command). Local mode, `facts` without `--reports`, runs the selected checks one process each: it is a developer tool, never the gate. A check that is not a test selector (a `grep`, a `[ -z "$(…)" ]`, a count of a runner's output) is a fault; rewrite it as a test and name that test.

`facts` parses `docs/superpowers/specs/*-facts.md` and exits non-zero on any red fact, any orphan fact (not traced to the specs, Step 2b), and any dangling or schema fault the project configures.

A fact is green when every part of its `check` (parts are joined by `&&`) selects at least one report entry and every selected entry passed. Otherwise it is red, with a reason: `not run` (nothing selected, or no report), `skipped`, `failed`, or the other outcome. Two reports with the same file name fail the gate. A missing or empty DIR makes every fact `not run`. What each runner's check selects:

- pytest: the node ids it names; a bare selector (a test without a case) stands for the test and each parametrised case.
- vitest and Playwright, by id: the entries of the named file whose own title starts with the fact's id (`<ID> `); the `-t`/`-g` pattern is not evaluated, and the id must be the fact's own.
- vitest, whole files: the project's own command prefix, then the files (relative to the prefix's directory), then optionally `-t <regex>` over the full name (ancestor titles and title joined by spaces, as vitest does). At least one entry, all passed; no counts. A check naming no file is a fault.
- cargo: `cargo test -p <pkg> (--test <bin> | --lib) [--release] [-- <filter> …]`; each filter must select at least one entry of that binary, and without filters every entry of the binary. `--release` checks read only the project's `release_reports`.
- swift: audited for its declared form only; no report holds it, so the fact prints `not gated (swift)`.

Every mode, `--orphans` included, audits each check statically: the form is one the project declares in `.claude/project.toml` (`docs/project-toml.md`), the files and functions it names exist, and each selector names one definition.

- `facts --orphans`: traceability and the static audits only, no reports needed (extraction time, pre-commit, every push). `--implemented` does not affect it. A project traces by its design text (an id appears in the sibling `-design.md`) or by the `*Facts :*` lines of its specs (`orphans = "facts-lines"`; an id cited there and defined by no fact is dangling).
- `--implemented`: only `@implemented` facts are judged (the gate at a milestone boundary); the others are listed as `- pending: <id> [<status>]`.
- `--only ID` (repeatable) and `--owner NAME` (projects with `owner = true`) narrow the facts judged; an unknown `--only` id is an error.
- `--exclude-requires LIST`: a fact whose `requires:` names a listed resource prints `not run (requires: …)` and is not red (never silent). When given, each fact's `-m` markers must equal its `requires`.
- `--runner LIST`: local mode only; the runners whose checks it executes (`pytest`, `vitest`, `cargo`; `playwright` only when named).
- `--root DIR`: the repository root the spec directory is resolved from.

## CI wiring, in outline

Each test job sets the report path in its environment and uploads the report directory (artifact name prefix `facts-report-`, `if: !cancelled()`, `overwrite: true`, short retention, `if-no-files-found: error`). One gate job `needs` every test job, runs with `if: !cancelled()` (a red suite then also names the facts it turns red), downloads all `facts-report-*` artifacts into one directory, and runs `facts --reports <directory>`. The gate reads every test job: a job that did not run leaves no report, and its facts read `not run`. The full GitHub Actions template is `rules-python:ci-facts-gate`.

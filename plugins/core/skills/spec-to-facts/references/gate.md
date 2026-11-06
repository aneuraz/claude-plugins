# The report and the gate

Two parts. Each test job writes a report of its tests' outcomes, and one gate job reads every report. The gate runs no test, so a suite is never re-run to re-prove a fact.

## Part 1, the report

A report is a JSON object `{test_id: outcome}`, one file per test job, written when the job's test session ends. The test id is the runner's own, in the same form the `check` of a fact uses; the outcome is one of `passed`, `skipped`, `failed`, `error`, `xfailed`, `xpassed`. Each language writes it with its own mechanism (for pytest, a plugin: `rules-python:facts-report-plugin`). The job passes the report path through its environment so the job's command, and so each fact's `check`, is unchanged, and uploads the report directory as an artifact named after the job.

## Part 2, the gate

`facts` (through the project's `cpt` command) parses `docs/superpowers/specs/*-facts.md` and exits non-zero on any red fact **or on any orphan fact** (id absent from its sibling design doc, Step 2b).

- `facts --orphans`: traceability only, no reports needed (extraction time, pre-commit, every push). `--implemented` restricts the listing to `@implemented` facts.
- `facts --reports DIR`: reads the JSON files under DIR, one per job, and runs no check. A fact that is not `@draft` or `@superseded` is green when every test its `check` names appears in a report and every appearance is `passed`. Otherwise it is red, with a reason: `not run` (in no report), `skipped`, `failed`, or the other outcome. Two reports with the same file name (one job reported twice) fail the gate. A missing or empty DIR makes every fact `not run`. `--runner LIST` names the selector syntaxes the `check` commands may use; `--exclude-requires LIST` leaves out facts that need a named capability the job does not have; `--root DIR` sets the repository root the spec directory is resolved from.
- Without `--orphans` or `--reports`: runs each non-`@draft` check verbatim, one process each, for local use.

A bare selector (a test without a case) stands for the test and each of its parametrised cases. A `check` with no selector the reports can hold is `not run`.

## CI wiring, in outline

Each test job sets the report path in its environment and uploads the report directory (artifact name prefix `facts-report-`, `if: !cancelled()`, `overwrite: true`, short retention, `if-no-files-found: error`). One gate job `needs` every test job, runs with `if: !cancelled()` (a red suite then also names the facts it turns red), downloads all `facts-report-*` artifacts into one directory, and runs `facts --reports <directory>`. The gate reads every test job: a job that did not run leaves no report, and its facts read `not run`. The full GitHub Actions template is `rules-python:ci-facts-gate`.

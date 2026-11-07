# Migrate the other repositories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `cpt facts` judges pytest, vitest, Playwright and cargo facts from test reports; then `candle-pseudo`, `candle-app`, `capture`, `fhirforge`, `fouille` and `korps` take their skills, rules and (where they have them) facts and wiki tooling from `claude-plugins`, each through its own PR with green CI.

**Architecture:** Part A extends the package in `claude-plugins` (branch `plan3/facts-reports`) and publishes a pin. Part B migrates one repository per task, each in a worktree at its `origin/main` (`git -C <repo> worktree add <repo>/.claude/worktrees/plugins-migrate -b plugins/migrate origin/main`), never in the repository's own checkout (`capture`, `fhirforge` and `fouille` hold unrelated uncommitted work). Plan 2 (`candle`) is the model for every migration.

**Tech Stack:** Python 3.14 (package), uv, pytest; vitest, Playwright; Rust stable 1.98 with cargo-nextest; GitHub Actions (hosted Ubuntu; self-hosted macOS ARM64 for `capture`).

**Specs:** `docs/superpowers/specs/2026-11-06-claude-plugins-design.md` and `docs/superpowers/specs/2026-11-07-facts-gate-from-reports-design.md` with its *Amendments after the plan review* (binding; the latter revises the former's *The tooling package*). Plan 2: `docs/superpowers/plans/2026-11-06-migrate-candle.md`.

## Owner's rulings (2026-11-07)

- `candle-legacy` (`candle-qa` locally) is not touched.
- `capture`'s and `fhirforge`'s `SECURITY.md` stay as they are, except the lines of `capture`'s §7 that name the gate's command, which now describe `cpt facts --reports`.
- Tooling moves in every repository that has it, `capture` included.
- A facts gate never runs checks; local mode is a developer tool. `capture`'s shell checks are rewritten as tests; whole-file vitest selections are judged "at least one entry, all passed".
- `capture`'s CI installs uv with `astral-sh/setup-uv`.
- The owner pushes `fouille`'s two local commits before Task B5.

## Global Constraints

- **Language.** `fhirforge` and `fouille` keep French in their own texts. `capture`: new writing (tests, CI comments, config, commits, PR) is English, per its `CLAUDE.md` §9 rule 18; amendments follow the language of the document they amend (its `CLAUDE.md` and fact-set amendments in French). Dated documents are archives; their facts change only `status`/`superseded_by`, except `capture`'s fact-set checks, rewritten by ruling.
- **Pin.** A Python repository's dev group gets `claude-plugins-tools` from git at Part A's SHA, with a trace row in its dependency documentation (`candle`'s rule on vetting direct dependencies). `capture` runs it with `uvx --from "claude-plugins-tools @ git+https://github.com/aneuraz/claude-plugins@<sha>" cpt …`.
- **Audit step.** Any `uv export … | pip-audit` gains `--no-emit-package claude-plugins-tools` (git requirements carry no hash), with plan 2's comment.
- **Reports directory** is `reports/facts/`, gitignored; never a directory that already holds other JSON.
- **The report plugin** is declared where the repository's tests load plugins (`tests/conftest.py` when there is no root `conftest.py`); a test that spawns pytest strips `PYTEST_ADDOPTS` (plan 2's FGT-011 lesson).
- **Facts on deleted tests** are superseded by facts of a small migration design and fact-set in the repository (plan 2's `PLM-*` pattern), never left dangling.
- **`archive_until`** in the repository's `.claude/project.toml` is the migration date before `migrate_citations.py` runs.
- **`.claude/settings.json`** declares `datazard-plugins` and enables `core` plus the packs listed per task; plugins already enabled stay (`fhirforge`'s `c4m@c4-model-skill`).
- **Skills** in `core` are removed; others (`suivi-github-project`, `impeccable`, `archify`) stay.
- **`CLAUDE.md`** loses what `base.md` carries; a section cited by number elsewhere keeps its numbered heading as a one-line stub naming the base rule that now holds it (in the file's language), as `candle`'s `CLAUDE.md` does; gains the main-session stop line (translated for French files).
- **Before every commit**: the repository's CI commands, package rows in fresh `UV_PROJECT_ENVIRONMENT`s.
- **Owner stops**: every push, every PR (draft), anything outside the worktrees.

## Review Focus

1. **A verdict that changes** (cargo's "each filter selects ≥ 1 entry"; facts newly judged from reports): each tooling task's shadow comparison lists every change and its cause.
2. **A missing report** (cancelled job, artifact name): `not run`, never green.
3. **A gate job skipped because a test job failed**: the gate runs `if: ${{ !cancelled() }}` and checks each `needs.*.result`.
4. **A numbered citation into a reduced `CLAUDE.md`**: every `CLAUDE.md §N` citation still resolves (grep before committing).
5. **A dated document rewritten**: `archive_until` set first; the script reports skipped archives.

---

## Part A — `claude-plugins` (branch `plan3/facts-reports`)

### Task A1: Normalized reports, configurable forms, the by-id JS rule

**Files:** `src/claude_plugins_tools/facts/` (split `check.py` into `check.py`, `reports.py`, `selectors.py` once it passes ~600 lines), `project.py`, `docs/project-toml.md`; tests `tests/facts/test_reports.py`, `test_js_by_id.py`, `tests/test_project.py`.

**Interfaces:** `load_reports(directory) -> Reports` reads the pytest format and the normalized one (`Entry(id, title, outcome, file, binary)`); `[facts] check_forms` stays a flat list (pytest) and accepts the optional sub-table `[facts.check_forms]` with `vitest`, `playwright`, `vitest-files`, `cargo`, `swift`.

- [ ] Tests first: both formats in one directory; the by-id rule (own title starts with `"<ID> "`, ≥ 1, all passed; `not run`); static faults (id ≠ fact id; no test carries the id); `candle-app`'s two forms pass; `candle`'s flat `check_forms` still parses. Run (FAIL), implement, run the suite (PASS), commit.

### Task A2: Converters

**Files:** `facts/convert.py`, `__main__.py` (`cpt facts report vitest|playwright|nextest <raw> <out> [--test-dir DIR]`); `tests/facts/test_convert.py`, `tests/facts/fixtures/`.

- [ ] Install cargo-nextest locally (`cargo install cargo-nextest --locked`, version resolved, not written from memory) and generate fixtures from real runs in a scratch directory: vitest 4 and 5 JSON, Playwright 1.61 JSON, a nextest JUnit from a workspace with one `--lib` and one integration test, one test failed and one ignored. Commit the fixtures.
- [ ] Tests first: `candle-app`'s `runner_reports.py` outputs reproduced on the same inputs; vitest file paths relative to the repository root; nextest `binary` (`pkg::bin` vs `pkg`); ignored tests absent; flaky → failed; worse outcome wins; `--test-dir`. Implement, run, commit.

### Task A3: The cargo and swift forms

**Files:** `selectors.py`/`check.py`; `tests/facts/test_cargo.py`.

- [ ] Tests first: filters as substrings of the test path in the selected binary; each filter ≥ 1 entry; no filter = the binary's entries; `--lib` selects binary `pkg` only; `--release` reads only `[facts] release_reports`; `&&` conjunction; static audit (package directory from `cargo metadata`; the `--test` file exists; each filter literal appears in it, a `::` filter by its last segment; refused flags); the `swift` form audited, never judged; local mode runs a cargo check by exit code. Implement, run, commit.

### Task A4: Whole-file vitest, `--exclude-requires`, and the facts options

**Files:** `check.py`, `project.py`, `docs/project-toml.md`, `plugins/core/skills/spec-to-facts/references/gate.md`, `plugins/rules-python/…` facts rules; `tests/facts/test_options.py`.

- [ ] Tests first: the whole-file form (declared command prefix, files relative to the repository, `-t` as a regex over the full name; a check with no file is a fault); `--exclude-requires` in reports mode lists not run and is not red, and the markers audit runs; `--only` repeatable, unknown id an error; `--owner`; `orphans = "facts-lines"` (letter suffixes, digit prefixes, `à|to` ranges, dangling faults); `schema`; pending facts listed under `--implemented`. Implement; update the docs; run; commit.

### Task A5: The citation script's deferred fixes

- [ ] Tests first in `tests/tools/test_migrate_citations.py`: link titles kept; image links to moved pages unmapped; events by line; bare sibling targets after `"`/`'`/`( ` caught; indented code blocks and over-indented fences are code. Implement, run, commit.

### Task A6: Publish the pin

- [ ] Whole-branch final review and its fixes; ask the owner to confirm pushing `main`; push; record the SHA.

---

## Part B — one task per repository

Each task ends: local CI run, commit(s); a task review; then, after the owner's confirmation, push and draft PR, CI report.

### Task B1: `candle-pseudo`

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`.
- **Migration facts:** a `PLM-*` design and fact-set (`docs/superpowers/specs/<date>-plugins-migration-…`): the gate is `cpt facts --reports` at the pin; `--exclude-requires` lists not run in reports mode; the report plugin is the package's. The two `@implemented` facts on `tests/unit/test_facts_check.py` (`2026-10-13-foundation-and-benchmark-facts.md:1262-1271`) become `@superseded` by them.
- **Facts CI:** the pytest job writes `--facts-report=reports/facts/<job>.json` (plugin in `tests/conftest.py`); `tests/contracts/test_integration_markers.py`'s `run_probe` strips `PYTEST_ADDOPTS`; a gate step runs `cpt facts --reports reports/facts --implemented --exclude-requires parhaf,baseline`; `--orphans` stays. Shadow-compare with the old checker on the same commit. `scripts/facts_check.py` and `tests/unit/test_facts_check.py` go; `scripts/facts_promote.py` stays (port its import if it uses the old checker). Audit step: the flag. `reports/facts/` gitignored (`reports/` holds committed benchmark JSON).
- **Rules:** compare each of the 44 pages' **bodies** (ignoring `sources`) with `candle`'s at `275bce0`: identical bodies leave via `migrate_citations.py --source candle`; split pages are reduced to `candle-pseudo`'s application (as plan 2 Task B2 step 3), `data-classification` keeping its own rows; `documentation-chain` and `project-tracking` keep `candle-pseudo`'s application and point to `core`. Hubs, the `SECURITY.md` paragraph, a log entry, the index. `hubs/toolchain-and-dependencies.md:41` and `howto/running-the-benchmark.md:84-87` stop naming `facts_check.py`.
- **Wiki tooling:** `[wiki] tooling = "cpt"` and `cpt wiki check` in CI, faults fixed (recorded); or, if they are many and unrelated, `tooling = "none"` with the count recorded.
- `CLAUDE.md` §7 *Real data* stays; §1–§4 stubs only if cited (grep).

### Task B2: `candle-app`

- Plugins: `core`, `rules-security`, `rules-typescript`, `rules-health-data`.
- **Facts:** `cpt facts report vitest|playwright` (unit and e2e jobs, `--test-dir tests/e2e`) and `cpt facts --reports reports/facts --implemented` (gate); `--orphans` in checks; `[facts.check_forms]` declares its two forms. Shadow-compare. `scripts/facts_check.py`, `scripts/runner_reports.py`, `tests/tooling/test_facts_check.py` go; the CI step `uv run pytest tests/tooling -rf` goes; `pytest`, `pyyaml` and `pythonpath = ["."]` leave if nothing else needs them. Audit step: the flag.
- **Wiki:** `scripts/wiki` gives way to `cpt wiki`; index regenerated; `cpt wiki check` in CI.
- **Rules:** `migrate_citations.py --source candle` (it also rewrites `contracts/candle.example.toml:5`, a citation of a `candle` rule); its three pages follow `candle`'s split.
- The private `aneuraz/candle` dependency and `CANDLE_READ_TOKEN` unchanged; `docker build` checked.

### Task B3: `capture`

- Plugins: `core`, `rules-security`, `rules-rust`, `rules-swift`, `rules-health-data`, `rules-untrusted-parsing`.
- **Shell checks → tests** (English): every `@implemented` part that is not a cargo, swift or whole-file vitest selector — PRJ-003's `grep`, ENC-001, I18N-004's emit check, UI-002…007's npm counts (UI-002 rewritten to name its files) — becomes a Rust or vitest test; the fact's `check` (in French) selects it. Each rewrite reviewed against the fact's statement.
- **Reports:** cargo-nextest installed in CI as `cargo-audit`/`cargo-deny` are (version resolved; recorded in `docs/dependencies.md` if `capture`'s rules require); one JUnit profile per run (debug; release proptests; release bench alone), a serial group for STO-005, the debug bench guard and the keychain tests; `cargo test --doc` kept; front-end vitest JSON report. A new gate job (`needs:` the test jobs, `if: ${{ !cancelled() }}`, checks each `needs.*.result`) runs `uvx … cpt facts --reports reports/facts --implemented --owner core`; `--orphans` in `core` (with `setup-uv`); the core job's Node/`npm ci` steps for the old gate go. `[facts]`: forms (cargo, swift, vitest-files), `release_reports`, `orphans = "facts-lines"`, `owner = true`, `schema` from `capture`'s checker. `reports/facts/` gitignored.
- **Shadow run** (alone, not beside another test job — `CLAUDE.md` §6): old and new gates on the same commit; every verdict agrees or the difference is explained (note OCR-012, `owner: store`, ungated both ways). Then `scripts/facts_check.py`, `scripts/facts_trace.py` and the venv step go; `scripts/enc001_check.sh` stays.
- **Documents:** `SECURITY.md` §7's command lines (`:330-331`) describe `cpt facts --reports`; `README.md:613-618`, `CLAUDE.md` §6 (`--only`) and §7.1 (`--orphans`), `crates/project/tests/export_markdown.rs:117` updated. `CLAUDE.md` (French) keeps §1–§3 as stubs (`CLAUDE.md §2` is cited ten times) and §0, §4–§9.
- `suivi-github-project` stays.

### Task B4: `fhirforge`

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`, `rules-untrusted-parsing`; `c4m@c4-model-skill` stays.
- No tooling (`requires-python >=3.13`).
- `CLAUDE.md` (French): §1–§3 kept as stubs (cited in `src/fhirforge/llm/client.py:5`, `fhir/mapping.py:623`, `terminology/index.py:82`, `scripts/bench_extraction_stability.py:115`, `docs/evaluation-normalisation.md:331`, `tests/observability/test_access.py:99`); §4/§4.1 and §6 stay (its own completion gate, cited at `api/fhir_schemas.py:91`, `tests/pipeline/test_orchestrator.py:169`, `pyproject.toml:136`); §5, §7–§9 stay. `SECURITY.md` untouched. `suivi-github-project` stays.

### Task B5: `fouille` (after the owner pushes its two local commits)

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`. No CI, no tooling.
- `docs/regles-securite.md` and `docs/regles-python.md`: each section restating a pack rule is replaced by its citation, keeping its numbered heading as a stub so `CLAUDE.md:46` (§1.10), `:58` (§1), `regles-python.md:27-29` (§3.2, §4.1, §3.1 with anchors) and `SECURITY.md:21` still resolve; `fouille`'s own text stays. `docs/chaine-documentaire.md` and `docs/suivi-projet.md` point to `core:spec-to-facts` and `core:github-project-tracking` for their generic parts.
- `CLAUDE.md` (French) reduced; the `codebase-design` copy goes (in `core`). Committed `.DS_Store` files removed; `.DS_Store` added to `.gitignore`.

### Task B6: `korps`

- Plugins: `core` only. Its `unslop` copy goes; the vendored `impeccable` skill and its four agents stay. No `CLAUDE.md` (accepted: no stop line there).

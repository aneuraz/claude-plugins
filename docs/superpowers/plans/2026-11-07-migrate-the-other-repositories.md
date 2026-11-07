# Migrate the other repositories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `cpt facts` judges pytest, vitest, Playwright and cargo facts from test reports; then `candle-pseudo`, `candle-app`, `capture`, `fhirforge`, `fouille` and `korps` take their skills, rules and (where they have them) facts and wiki tooling from `claude-plugins`, each through its own PR with green CI.

**Architecture:** Part A extends the package in `claude-plugins` (branch `plan3/facts-reports`) and publishes a pin. Part B migrates one repository per task, each in a worktree at its `origin/main` (`git -C <repo> worktree add <repo>/.claude/worktrees/plugins-migrate -b plugins/migrate origin/main`; the local checkouts of `capture`, `fhirforge` and `fouille` hold unrelated uncommitted work that must not be touched). `candle` (plan 2) is the model for every migration.

**Tech Stack:** Python 3.14 (package), uv, pytest; vitest, Playwright; Rust stable 1.98 with cargo-nextest; GitHub Actions (hosted Ubuntu and self-hosted macOS ARM64).

**Specs:** `docs/superpowers/specs/2026-11-06-claude-plugins-design.md` and `docs/superpowers/specs/2026-11-07-facts-gate-from-reports-design.md` (binding; the latter revises the former's *The tooling package*). Plan 2 (`docs/superpowers/plans/2026-11-06-migrate-candle.md`) for the migration pattern.

## Owner's rulings (2026-11-07)

- `candle-legacy` (`candle-qa` locally) is not touched.
- `capture`'s and `fhirforge`'s `SECURITY.md` stay as they are.
- Tooling moves in every repository that has it, `capture` included.
- A facts gate never runs checks; local mode is a developer tool. `capture`'s shell checks are rewritten as tests; whole-file vitest selections are judged "at least one entry, all passed".
- `capture`'s CI installs uv with `astral-sh/setup-uv`.

## Global Constraints

- Every migrated repository keeps its working language; `capture`, `fhirforge` and `fouille` stay French in their own texts. Their dated specs, fact-sets and plans are archives except where a ruling says otherwise (`capture`'s fact-set checks are rewritten, by ruling).
- Pin: each Python repository's dev group gets `claude-plugins-tools` from git at Part A's published SHA; a repository without Python (`capture`) runs it with `uvx --from "claude-plugins-tools @ git+https://github.com/aneuraz/claude-plugins@<sha>" cpt …`.
- Package suite rows in a workspace get the package through the dependency every row installs (plan 2's lesson: `--package X --exact` installs only that package's dev group).
- `.claude/settings.json` declares `datazard-plugins` (`{"source": {"source": "github", "repo": "aneuraz/claude-plugins"}}`) and enables `core` plus the packs listed per task; plugins the repository already enables stay (`fhirforge`'s `c4m@c4-model-skill`).
- Skills that exist in `core` are removed from the repository; skills that do not (`suivi-github-project`, `impeccable`, `archify`) stay.
- Each `CLAUDE.md` loses what `core`'s `base.md` carries (think before coding, simplicity, surgical changes, the completion-gate principle, the unslop line, the independent-review points), keeps everything the repository owns, keeps section numbers that other files cite, and gains the main-session stop line of `candle`'s `CLAUDE.md`. Translate the stop line for a French `CLAUDE.md`.
- Every repository's citations to a moved rule are rewritten with `tools/migrate_citations.py`; archives are skipped.
- Before every commit in a repository: its CI's commands, run locally in fresh environments for package rows (`UV_PROJECT_ENVIRONMENT` set to a new directory).
- Pushing, opening each PR (draft), and anything outside the worktrees wait for the owner's confirmation.

## Review Focus

1. **A fact that was green under the old gate turns red under the new one** (cargo's "each filter selects ≥ 1 entry"; candle-pseudo's facts once judged from reports): the shadow comparison in each tooling task lists every verdict change and its cause.
2. **A report missing for a job** (a cancelled job, an artifact name typo): the gate reports `not run`, never green.
3. **A Python floor below 3.14** (`fhirforge` ≥ 3.13, `fouille` ≥ 3.12): these repositories take plugins only, never the package.
4. **A `CLAUDE.md` section cited by number elsewhere** (`capture` and `fhirforge` cite `CLAUDE.md §N`): numbers kept, or the citations rewritten in the same commit.
5. **A CI job that copies `scripts/` into an image** (`candle-app`'s Dockerfile `COPY . ./`): the build still succeeds after the scripts leave.

---

## Part A — `claude-plugins` (branch `plan3/facts-reports`)

### Task A1: Normalized reports and the by-id JS rule

**Files:** Modify `src/claude_plugins_tools/facts/check.py` (split into `check.py`, `reports.py`, `selectors.py` if it grows past ~600 lines), `src/claude_plugins_tools/project.py`, `docs/project-toml.md`; Test `tests/facts/test_reports.py`, `tests/facts/test_js_by_id.py`, `tests/test_project.py`

**Interfaces:** Produces `load_reports(directory: Path) -> Reports` reading both the pytest format and the normalized format (`Entry(id, title, outcome, file, binary)`); `[facts] check_forms` per runner (`pytest`, `vitest`, `playwright`, `cargo`, `vitest-files`), each a list of command prefixes with placeholders documented in `docs/project-toml.md`.

- [ ] **Step 1: Failing tests:** a normalized report and a pytest report in one directory are both read; a vitest-by-id fact is green when the file's entries whose own title starts with `"<ID> "` all passed and there is ≥ 1; red when one failed; `not run` when none; a check whose id differs from the fact's is a static fault; a file with no test carrying the id is a static fault; `candle-app`'s two forms configured in a fixture `project.toml` pass the audit.
- [ ] **Step 2:** Run; expected FAIL. **Step 3:** Implement. **Step 4:** Run the full suite; PASS. **Step 5:** Commit.

### Task A2: Converters

**Files:** Create `src/claude_plugins_tools/facts/convert.py`; Modify `__main__.py` (subcommand `cpt facts report vitest|playwright|nextest <raw> <out> [--root DIR] [--test-dir DIR]`); Test `tests/facts/test_convert.py` with fixtures copied from real outputs (vitest 4/5 JSON, Playwright 1.61 JSON, nextest JUnit)

- [ ] **Step 1:** Generate the fixtures from real runs in a scratch directory (a two-test vitest project, a two-test Playwright project, a small cargo workspace with one `--lib` and one integration test, one of each ignored/failed); commit them under `tests/facts/fixtures/`.
- [ ] **Step 2: Failing tests** reproducing `candle-app`'s `runner_reports.py` outputs on the same inputs (port its tests if it has any), the nextest `binary` field (`pkg::bin` vs `pkg`), ignored tests absent, flaky → failed, worse outcome wins, `--root` and `--test-dir`.
- [ ] **Steps 3–5:** Implement, run, commit.

### Task A3: The cargo form

**Files:** Modify `selectors.py`/`check.py`; Test `tests/facts/test_cargo.py`

- [ ] **Step 1: Failing tests:** filters as substrings of the test path within the selected binary; each filter must select ≥ 1 entry; no filter = every entry of the binary; `--lib` selects binary `pkg` only, never `pkg::*`; `--release` reads only `[facts] release_reports`; `&&` conjunction; static audit (the `tests/<bin>.rs` file exists, each filter literal appears in it, refused flags); local mode runs a cargo check and judges by exit code.
- [ ] **Steps 2–5:** Run (FAIL), implement, run (PASS), commit.

### Task A4: Whole-file vitest, `--exclude-requires` in reports mode, and the facts options

**Files:** Modify `check.py`, `project.py`, `docs/project-toml.md`; Test `tests/facts/test_options.py`

- [ ] **Step 1: Failing tests:** whole-file form (`npm --prefix <dir> exec vitest run <files…> [-t <p>]`), "≥ 1 entry, all passed", `-t` as vitest's substring of the full name; `--exclude-requires` in reports mode lists the fact as not run with its requirement and exits 0 for it; `--only ID` (local mode; unknown id is an error); `--owner NAME` with `[facts] owner = true`; `[facts] orphans = "facts-lines"` (cited on `*Facts :*` lines of any spec, letter suffixes, digit prefixes, `à|to` ranges, dangling ids are faults); `[facts] schema` (allowed/required fields, closed statuses, `@implemented` without `check`, duplicate ids); pending facts listed under `--implemented`.
- [ ] **Steps 2–5:** Run, implement, run, commit. Update `plugins/core/skills/spec-to-facts/references/gate.md` and `rules-python`'s facts rules for the new forms and flags.

### Task A5: The citation script's deferred fixes

**Files:** Modify `tools/migrate_citations.py`; Test `tests/tools/test_migrate_citations.py`

- [ ] **Step 1:** Tests first for: a link title is kept (`[t](p "T")`); an image link to a moved page is unmapped (no stray `!`); events ordered by line; bare sibling targets after `"`/`'` and `( ` caught by the residual scan; indented code blocks and fences indented > 3 spaces treated as code.
- [ ] **Steps 2–5:** Run, implement, run, commit.

### Task A6: Publish the pin

- [ ] **Step 1:** Final review of Part A (the whole branch), its fixes.
- [ ] **Step 2:** Ask the owner to confirm pushing `main`; fast-forward and push; record the SHA.

---

## Part B — one task per repository

Each task: worktree at `origin/main`; `.claude/project.toml` (only the sections the repository uses); `.claude/settings.json`; core-duplicate skills removed; `CLAUDE.md` reduced; citations rewritten; CI changed; local CI run; commit(s); then, after the owner's confirmation, push and open a draft PR, and report its CI. A task-scoped review gates each task before its push.

### Task B1: `candle-pseudo`

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`.
- **Rules:** its 44 wiki rule pages are `candle`'s copies: run `migrate_citations.py --source candle` (slugs are `candle`'s); for any page whose text differs from `candle`'s, keep it as a `candle-pseudo` page and record why. `--source candle` must not delete a page that holds `candle-pseudo`'s own application.
- **Wiki tooling:** none today. Set `[wiki] tooling = "cpt"`, add `cpt wiki check` to CI, and fix the faults it reports (record them), or, if the faults are numerous and unrelated to the migration, set `tooling = "none"` and record the count for a later plan.
- **Facts:** CI switches from local mode to reports: the pytest job writes `--facts-report` (the package plugin, loaded from `conftest.py`), and a gate step runs `cpt facts --reports … --implemented --exclude-requires parhaf,baseline`. Shadow-compare with the old `facts_check.py` verdicts on the same commit. `tests/unit/test_facts_check.py` and `scripts/facts_check.py` go; `scripts/facts_promote.py` stays if it does not import the old checker (else port its import).
- `CLAUDE.md` §7 *Real data* stays.

### Task B2: `candle-app`

- Plugins: `core`, `rules-security`, `rules-typescript`, `rules-health-data`.
- **Facts:** `scripts/facts_check.py` and `scripts/runner_reports.py` give way to `cpt facts report vitest|playwright` (unit and e2e jobs, `--test-dir tests/e2e`) and `cpt facts --reports reports/facts --implemented` (gate job); `[facts] check_forms` declares its two forms. Shadow-compare verdicts. `tests/tooling/test_facts_check.py` goes; `pythonpath = ["."]` goes if nothing else needs it.
- **Wiki:** its older `scripts/wiki` gives way to `cpt wiki`; regenerate the index; run `cpt wiki check`.
- **Rules:** its three rule pages (`documentation-chain`, `project-tracking`, `typescript-rules`) follow `candle`'s split.
- The private `aneuraz/candle` dependency and `CANDLE_READ_TOKEN` are unchanged; `docker build` still succeeds after `scripts/wiki` and the facts scripts leave (the Dockerfile copies the tree).

### Task B3: `capture`

- Plugins: `core`, `rules-security`, `rules-rust`, `rules-swift`, `rules-health-data`, `rules-untrusted-parsing`.
- **Shell checks → tests:** list every `@implemented` check part that is not a cargo or vitest selector (PRJ-003's `grep`, ENC-001, I18N-004's emit check, UI-002…007's npm counts); write each as a test (Rust or vitest) and rewrite the fact's `check` to select it. Each rewritten check is reviewed against the fact's statement.
- **Reports:** nextest with one JUnit profile per run (debug; release proptests; release bench), a serial group for the load-sensitive tests, `cargo test --doc` kept; vitest JSON report in the front-end job; a new gate job (`needs:` the test jobs) runs `uvx … cpt facts --reports reports --implemented --owner core`; `--orphans` in the `core` job. `.claude/project.toml` `[facts]`: forms for cargo and vitest-files, `release_reports`, `orphans = "facts-lines"`, `owner = true`, `schema` from `capture`'s checker.
- **Shadow run:** before removing the old gate, run both on the same commit; every verdict agrees or the difference is explained. Then `scripts/facts_check.py`, `scripts/facts_trace.py` and the venv step go; `scripts/enc001_check.sh` stays (history).
- `CLAUDE.md` (French) loses §1–§3 and the generic part of §6, keeps §0, §4–§5, §7–§9 and their numbers (`capture` cites them); its §8 GitHub Project stays. `SECURITY.md` untouched. `suivi-github-project` stays.

### Task B4: `fhirforge`

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`, `rules-untrusted-parsing`; `c4m@c4-model-skill` stays enabled.
- No facts or wiki tooling; `requires-python >=3.13` — no package dependency.
- `CLAUDE.md` (French) reduced as in the global constraints; its §5 *Dépendances*, §7–§9 stay with their numbers. `SECURITY.md` untouched. `suivi-github-project` stays.

### Task B5: `fouille`

- Plugins: `core`, `rules-security`, `rules-python`, `rules-health-data`.
- No CI and no facts or wiki tooling.
- `docs/regles-securite.md` and `docs/regles-python.md` are French copies of pack rules: each section that restates a pack rule is replaced by its pack citation; the two citations of `regles-securite.md §1` and `§1.10` are rewritten in the same commit; what is `fouille`'s own stays. `docs/chaine-documentaire.md` and `docs/suivi-projet.md` point to `core:spec-to-facts` and `core:github-project-tracking` for their generic parts.
- `CLAUDE.md` (French) reduced. The committed `.DS_Store` files are removed and `.DS_Store` is added to `.gitignore`.

### Task B6: `korps`

- Plugins: `core` only (a Hugo site with no code rules).
- Its copied `unslop` skill goes; the vendored `impeccable` skill and its four agents stay.
- No `CLAUDE.md` today: add none (the base rules come from `core`).

# Migrate candle onto claude-plugins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `candle` uses the `datazard-plugins` marketplace and the `claude-plugins-tools` package instead of its copied skills, its `scripts/wiki`, `scripts/facts_check.py`, `scripts/facts_report.py` and the rule pages the packs now hold, with its CI green; and `core` and the tooling receive what this first migration needs.

**Architecture:** Two repositories, in order. Part A changes `claude-plugins` (`~/git/claude-plugins`, branch `migrate/candle-prereqs`) and publishes a commit; Part B migrates `candle` in a worktree at `origin/main` (`git -C ~/git/candle worktree add .claude/worktrees/plugins-migrate -b plugins/migrate origin/main`), pinned to that commit. A one-off script, kept in `claude-plugins/tools/` for the later migrations, rewrites citations from `claude-plugins`'s `docs/rule-classification.md`.

**Tech Stack:** Python 3.14, uv workspaces, pytest, the `cpt` CLI, GitHub Actions, Claude Code plugins.

**Spec:** `~/git/claude-plugins/docs/superpowers/specs/2026-11-06-claude-plugins-design.md` (*What stays in each project*, *Citing a rule that left the wiki*, *The `qa` agent*, *Detecting a session without its rules*). Plan 1: `docs/superpowers/plans/2026-11-06-build-claude-plugins.md` (*Left for plan 2*, and the owner's decision at its end).

## Owner's rulings for this plan (2026-11-06)

- **Facts on deleted tests:** a small migration design and fact-set in `candle` state that the wiki lint, the facts gate and the report plugin are `claude-plugins-tools` at the pin; the 43 archived facts whose tests leave `candle` become `@superseded` by them. `candle` keeps no copy of the package's tests.
- **Dated documents:** `[wiki] archive_until` in `candle`'s `.claude/project.toml` becomes the migration date, so every dated spec and plan written before it is an archive and is not rewritten.
- **`tracking/priority-and-size`:** its *Priority and size* section (and its log entry) enter this migration in Task B3.

## Global Constraints

- `candle`'s working language is English. Archives (dated files under `docs/superpowers/` on or before `archive_until`) are not rewritten; their facts may only change `status` and gain `superseded_by` (`candle`'s `docs/superpowers/README.md`).
- Pin: `candle`'s root `[dependency-groups] dev` gets `claude-plugins-tools`, with `[tool.uv.sources] claude-plugins-tools = { git = "https://github.com/aneuraz/claude-plugins", rev = "<Part A's published SHA>" }`; never a branch or tag.
- Plugin ids: `<plugin>@datazard-plugins`. `candle` enables `core`, `rules-security`, `rules-python`, `rules-typescript`, `rules-health-data`, `rules-untrusted-parsing`.
- A rule page whose classification row targets a pack and is not `split` leaves `candle`'s wiki; a `split` page stays at its slug with the project's application only, citing the pack rule; a `stays` page stays.
- Citations: in code and configuration, `wiki:rules/<slug>` → `<pack>:<slug>`; in Markdown, a link whose target resolves (against its file's directory) to `docs/wiki/rules/<slug>.md` → `<link text> (`<pack>:<slug>`)`. `docs/wiki/log.md` is never rewritten (append-only).
- Skills are named with their plugin prefix (`core:updating-the-wiki`).
- `candle`'s `CLAUDE.md` carries the line that stops a session without `core`'s base rules.
- **The CI set**, run locally before every `candle` commit (`ci.yml` at `origin/main`): `uv sync --locked --all-packages`; `uv run ruff check`; `uv run ruff format --check`; `uv run ty check`; `uv run lint-imports`; `uv run cpt facts --orphans`; `uv run cpt wiki check --base origin/main`; the audit step's `uv export … | uv run pip-audit …` as `ci.yml` writes it; `uv run pytest -q`. Task B5 also runs every suite row with its `--facts-report` and then `uv run --locked cpt facts --reports reports`.
- Pushing either repository, and opening the `candle` PR, waits for the owner's confirmation.

## Review Focus

1. **A citation the script cannot map** (a slug with no classification row, a link with an anchor): listed, left untouched, exit 1 — never guessed.
2. **A link in `docs/wiki/log.md` to a moved page**: kept, and `cpt wiki check` does not fault it (Task A4).
3. **A `split` page's sibling links** (bare file names inside `docs/wiki/rules/`, e.g. `data-classification.md`, `python-rules.md`): resolved and rewritten like any other.
4. **A session in `candle` without the marketplace**: the `CLAUDE.md` line makes the agent stop and say so (Task B4's real-session check).
5. **A GitHub runner**: `uv sync --locked` fetches the public git dependency, and the audit does not choke on its missing hash (Task B1, proven in B5).

---

## Part A — `claude-plugins`

### Task A1: Deferred fixes the first migration meets

**Files:** Modify `plugins/core/skills/updating-the-wiki/SKILL.md`, `plugins/core/skills/qa/SKILL.md`, `plugins/core/skills/qa/METHOD.md`

- [ ] **Step 1:** `updating-the-wiki`: move the `[wiki] tooling` / `[tooling] command` key check from step 5 to step 0.
- [ ] **Step 2:** `qa` SKILL.md step 7: the hand-over names `down_respect_keep` for a kept run, `down` otherwise.
- [ ] **Step 3:** `qa` METHOD.md: restore the row "Read, Grep, Glob inside the worktree"; add that the project's agent file carries its command-writing rules (quoting, one-line questions).
- [ ] **Step 4:** Run `uv run pytest tests/test_layout.py tests/wiki/test_skills.py -q` and `claude plugin validate plugins/core`. Expected: PASS.
- [ ] **Step 5:** Commit `fix(core): what the first migration meets`.

### Task A2: The generic halves of `documentation-chain` and `project-tracking` into `core`

**Files:** Modify `plugins/core/skills/github-project-tracking/SKILL.md`, `plugins/core/skills/spec-to-facts/SKILL.md`, `docs/rule-classification.md`

- [ ] **Step 1:** Read `git -C ~/git/candle show origin/main:docs/wiki/rules/project-tracking.md` and `…/documentation-chain.md`; list each section as generic or `candle`'s own.
- [ ] **Step 2:** `github-project-tracking` gains *What you discover along the way* (four discoveries, four destinations; a debt's unacceptability clause; none is settled in silence) and *Closing a decision* (closed by a decision page with its reason; the commit linked before closing), without `candle` names.
- [ ] **Step 3:** `spec-to-facts` gains in its lifecycle: the milestone's cross-cutting consistency review before the PR leaves draft; every milestone ends with a documentation task; what git does not track does not exist.
- [ ] **Step 4:** `docs/rule-classification.md`: the two rows become `split`, `target` = `core:github-project-tracking` / `core:spec-to-facts`, with a note naming the sections. `tests/test_packs.py::test_every_classified_rule_exists` checks only `rules-*` targets: confirm it ignores `core:` targets (adjust the test if not).
- [ ] **Step 5:** Run `uv run pytest -q`, `claude plugin validate plugins/core`. Expected: PASS.
- [ ] **Step 6:** Commit `feat(core): the generic halves of documentation-chain and project-tracking`.

### Task A3: The citation migration script

**Files:** Create `tools/migrate_citations.py`; Test `tests/tools/test_migrate_citations.py`

**Interfaces:**
- Produces: `uv run python tools/migrate_citations.py --repo <path> --source <name> [--apply]`. Reads the classification from **this repository's** `docs/rule-classification.md`, rows whose `source` is `<name>:<slug>` with a slug form (rows like `candle:CLAUDE.md#…`, `candle:SECURITY.md` are skipped). Prints one line per rewrite, kept citation, unmapped citation and page to delete. **Exit 1 whenever a citation is unmapped** (dry run or `--apply`; with `--apply` nothing is written then), else 0. Functions: `load_classification(path: Path, source: str) -> Mapping[str, Target]`, `Target(pack_citation: str | None, split: bool)`; `rewrite(text: str, file: Path, repo: Path, kind: Literal["code", "markdown"], table: Mapping[str, Target]) -> tuple[str, list[Event]]`.
- Files scanned: `git -C <repo> ls-files` text files, minus `docs/wiki/log.md`, minus files `claude_plugins_tools.wiki.archive` treats as archived under the repo's `.claude/project.toml` (reuse its `is_archived`), minus the pages being deleted.

- [ ] **Step 1: Write the failing tests:** `test_code_citation_rewritten`; `test_markdown_link_rewritten` with `../rules/x.md`, `../../docs/wiki/rules/x.md` from `examples/README.md`, `wiki/rules/x.md` from `docs/*.md`, and a bare `x.md` from inside `docs/wiki/rules/`; `test_split_slug_kept`; `test_stays_slug_kept`; `test_non_slug_rows_skipped`; `test_unknown_slug_unmapped_exit_1`; `test_anchor_link_unmapped`; `test_log_md_skipped`; `test_archived_file_skipped` (a dated file on or before `archive_until`) and `test_dated_file_after_archive_rewritten`; `test_apply_deletes_moved_pages_only`; `test_apply_writes_nothing_when_unmapped`; `test_dry_run_changes_nothing`.
- [ ] **Step 2: Run** `uv run pytest tests/tools -q`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the tests, then a dry run against a `git -C ~/git/candle worktree add --detach "$TMPDIR/candle-dry" origin/main` checkout carrying the `candle` example `.claude/project.toml` with `archive_until` set to today. Expected: PASS; the dry run lists rewrites and 0 unmapped (or lists them for Task B2). Remove the worktree.
- [ ] **Step 5:** Commit `feat(tools): the citation migration script`.

### Task A4: The wiki lint keeps the log's history

**Files:** Modify `src/claude_plugins_tools/wiki/check.py` (rule 3); Test `tests/wiki/test_wiki.py`

- [ ] **Step 1: Write the failing tests:** `test_log_link_to_a_removed_page_on_base_is_not_a_fault` (a log line present on `--base` links a page deleted since); `test_new_log_link_to_a_missing_page_is_a_fault` (a line added on the branch).
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement:** rule 3 skips links on `docs/wiki/log.md` lines already present on the base branch (rule 10 already reads the base's log).
- [ ] **Step 4: Run** `uv run pytest -q`. Expected: PASS.
- [ ] **Step 5:** Commit `fix(tools): rule 3 keeps the log's history`.

### Task A5: Publish the pin

- [ ] **Step 1:** Ask the owner to confirm pushing `main` (fast-forward from `migrate/candle-prereqs`, with the unpushed `87b6afc`).
- [ ] **Step 2:** `git switch main && git merge --ff-only migrate/candle-prereqs && git push origin main`; record `git rev-parse HEAD` as the pin.

---

## Part B — `candle` (worktree `.claude/worktrees/plugins-migrate`, branch `plugins/migrate`)

### Task B1: Tooling from the package, and the facts that record it

**Files:**
- Create: `.claude/project.toml` (the `candle` example of `claude-plugins`'s `docs/project-toml.md` at the pin, with `archive_until` = the migration date and `.claude/skills/qa` removed from `[qa] tooling_paths`); `docs/superpowers/specs/<date>-plugins-migration-design.md` and `…-facts.md` (facts `PLM-001` the wiki lint is `cpt wiki check` from the pinned package, check `tests/contracts/test_ci.py::test_ci_runs_the_wiki_check`-style test; `PLM-002` the facts gate is `cpt facts` from the package, check the `test_ci.py` test of the facts steps; `PLM-003` the report plugin is `claude_plugins_tools.facts.report`, check the `test_ci.py` conftest test; each `@implemented`, check in the fixed form `[facts] check_forms` accepts)
- Modify: `pyproject.toml`, `uv.lock`, `conftest.py:6`, `.github/workflows/ci.yml:84,94,109,233` (the audit's `uv export` gains `--no-emit-package claude-plugins-tools`, with a comment: git requirements carry no hash; its own dependencies stay audited), `tests/contracts/test_ci.py:43,96,113`, `tests/contracts/test_port.py:10-11`, `tests/contracts/test_layers.py:16`, `tests/test_distributions.py:31,425,441`, `docs/wiki/reference/development-dependencies.md` (trace the new dependency; `pyyaml` stays, its reason becomes the tests that parse YAML), `docs/wiki/howto/application-tests.md:11,23`, `docs/wiki/rules/ci-gates.md:15`, `docs/wiki/rules/documentation-chain.md:36`, `docs/wiki/rules/typescript-rules.md:25`, `docs/wiki/lessons/code-span-link-text-is-prose.md:13` (link → permalink to `scripts/wiki/markdown.py` at `275bce0`), the 40 archived facts on `tests/contracts/test_facts_check.py` and on the engine tests of `test_wiki.py` (`docs/superpowers/specs/2026-10-28-facts-gate-from-suite-reports-facts.md`, `2026-10-13-p1a-port-facts.md`): `status: "@superseded"`, `superseded_by` the PLM fact that binds in its place
- Rename: `tests/helpers/wiki.py` → `tests/helpers/git.py`, keeping only its `git` helper (stripped stdout, fixture identity flags), importers and the exemptions in `test_distributions.py` updated
- Delete: `scripts/wiki/`, `scripts/facts_check.py`, `scripts/facts_report.py`, `tests/contracts/test_facts_check.py`, and the engine tests of `tests/contracts/test_wiki.py`, keeping, under their names, `test_no_test_reads_a_moved_document`, `test_the_repository_wiki_passes_check`, `test_the_repository_tracks_no_french_twin`, `test_ci_runs_the_wiki_check`, `test_the_entry_points_link_to_existing_files` (calling `cpt`)
- Regenerate: `docs/wiki/index.md`

- [ ] **Step 1:** Write the PLM design and fact-set, and edit `test_ci.py` to expect the new conftest line, the `uv run cpt …` steps and the audit flag. Run `uv run pytest tests/contracts/test_ci.py -q`. Expected: FAIL.
- [ ] **Step 2:** Make the other changes listed. `test_port.py` imports `expand_ranges` from `claude_plugins_tools.facts.check`.
- [ ] **Step 3: Run** the CI set. Expected: all pass (`cpt facts --orphans` green with the supersessions; `cpt wiki check` green with the regenerated index).
- [ ] **Step 4: Check the release image:** `docker build --target candle .` (or the Dockerfile's release target) succeeds: `uv sync --locked --no-dev` must not need git for a dev-only git source. If it fails, report BLOCKED with the error.
- [ ] **Step 5:** Commit `build: the wiki and facts tools come from claude-plugins-tools`.

### Task B2: Rule pages leave the wiki

**Files:** every file the script rewrites; the moved rule pages (deleted); the six `split` pages; the hubs listing rules (`docs/wiki/hubs/*`); `SECURITY.md`; `docs/wiki/log.md` (one appended entry); `docs/wiki/index.md`

- [ ] **Step 1:** Dry run `uv run --project ~/git/claude-plugins python ~/git/claude-plugins/tools/migrate_citations.py --repo . --source candle`; settle each unmapped citation by hand (listed in the commit message).
- [ ] **Step 2:** `--apply`.
- [ ] **Step 3:** Reduce each `split` page to `candle`'s application: title states the application, first line cites the pack rule, generic text goes.
- [ ] **Step 4:** Hubs: a hub left with no `candle` page stays, listing the pack rules it frames. `SECURITY.md`'s *Code security rules* paragraph names the enabled packs and the security hub.
- [ ] **Step 5:** Append the log entry "Rules moved to the datazard-plugins packs" (`core:updating-the-wiki`'s form); regenerate the index.
- [ ] **Step 6: Run** the CI set, and `uv run cpt wiki search sql injection`. Expected: pass; the search lists `rules-security:parameterised-sql`.
- [ ] **Step 7:** Commit `docs(wiki): rule pages held by the packs leave the wiki`.

### Task B3: `documentation-chain` and `project-tracking` keep `candle`'s application

**Files:** `docs/wiki/rules/documentation-chain.md`, `docs/wiki/rules/project-tracking.md`, `docs/wiki/log.md`

**Interfaces:** Consumes Task A2's sections.

- [ ] **Step 1:** Bring in the *Priority and size* section from `~/git/candle/.claude/worktrees/priority-and-size/docs/wiki/rules/project-tracking.md` (uncommitted there) with its reworded Urgent line, and its log entry.
- [ ] **Step 2:** Remove from both pages the sections Task A2 moved; each page names, in prose, the `core` skill and section that hold them (e.g. "`core:github-project-tracking`, *What you discover along the way*").
- [ ] **Step 3:** Log entry; regenerate the index; run the CI set. Expected: pass.
- [ ] **Step 4:** Commit `docs(wiki): documentation-chain and project-tracking keep candle's application`.

### Task B4: Skills from the plugins, `CLAUDE.md` reduced, the QA guard reaches the packs

**Files:**
- Create: `.claude/settings.json` (`extraKnownMarketplaces.datazard-plugins = {"source": {"source": "github", "repo": "aneuraz/claude-plugins"}}`; `enabledPlugins` as in the global constraints)
- Delete: `.claude/skills/{codebase-design,domain-modeling,github-project-tracking,qa,reading-the-wiki,spec-to-facts,unslop,updating-the-wiki,writing-for-agents}` (the `archify` symlink stays)
- Modify: `.claude/agents/qa.md` (body: the surfaces table with the new `wiki search` / `wiki show` row, the command-writing rules, "follow the method in your delegation prompt"; frontmatter unchanged); `scripts/qa/guard.py` (allow `uv run cpt wiki search …` and `uv run cpt wiki show <citation>`); `tests/test_qa_guard.py` (cases for both, and a refused `uv run cpt wiki index`); `CLAUDE.md`; `tests/contracts/test_wiki_skills.py` (its skill-file tests go; `test_the_rules_point_to_the_wiki_skills` expects `core:updating-the-wiki`); `tests/contracts/test_wiki.py` `_ENTRY_POINTS` (the deleted skill files out); `docs/wiki/debts/skills-moved-out-of-their-checker.md`, `docs/wiki/lessons/engine-interface-redone-before-execution.md` (prefixed skill names); the 3 archived facts on `test_wiki_skills.py` tests that go (`2026-10-13-p1a-port-facts.md`): `@superseded` by a `PLM-004` fact "the wiki skills are `core:reading-the-wiki` and `core:updating-the-wiki` from the enabled `core` plugin", check `test_the_rules_point_to_the_wiki_skills` (added to the PLM design and fact-set)

- [ ] **Step 1: `CLAUDE.md`:** remove §1–§3 and the unslop line (now `core`'s `base.md`); §4 keeps "the CI is authoritative" and points to `rules-python:ruff-and-noqa-discipline`; §5–§7 stay; add the stop line; the routing table points to pack rules and `core:` skills. Under 3,000 characters.
- [ ] **Step 2:** The other edits listed; write the guard tests first (fail, then pass).
- [ ] **Step 3: Real-session checks** in the worktree: `claude plugin marketplace update datazard-plugins`, then `claude plugin install <each plugin>@datazard-plugins --scope project`; `claude -p "List the skills whose name starts with core:, and quote the first heading of your base rules."` → names `core:updating-the-wiki` and quotes `# Base rules`; `claude --settings '{"enabledPlugins":{"core@datazard-plugins":false}}' -p "Summarise your base rules."` → the answer says the plugins did not load and stops. Record both in the commit message. Undo the project-scope installs if they wrote files outside the worktree.
- [ ] **Step 4: Run** the CI set. Expected: pass.
- [ ] **Step 5:** Commit `chore: skills come from the datazard-plugins marketplace`.

### Task B5: Prove it in CI

- [ ] **Step 1:** Run each `ci.yml` suite row locally with its `--facts-report=reports/<job>.json`, then `uv run --locked cpt facts --reports reports`. Expected: green.
- [ ] **Step 2:** Ask the owner to confirm pushing `plugins/migrate` and opening a **draft** PR on `aneuraz/candle`.
- [ ] **Step 3:** Push; `gh pr create --draft` with a body listing Parts A–B, the pin and the rulings. Every job but the facts gate (which waits for ready-for-review) must pass, `uv sync --locked` and the audit included.
- [ ] **Step 4:** Report the run's link and result. Ready-for-review and the merge stay the owner's.

---

## Part C — the owner's user configuration

### Task C1: The declaration stays the project's, and one source for writing guidance

- [ ] **Step 1:** In a scratch directory with a `.claude/settings.json` enabling only `core@datazard-plugins`: `claude plugin install rules-rust@datazard-plugins --scope user`, `claude plugin list --json`, then `claude plugin uninstall rules-rust@datazard-plugins --scope user`. Record whether user scope adds the pack to that project. If it does, add to `claude-plugins`'s root `README.md` "never install a `rules-*` pack at user scope", and to `core`'s `session_start.py` a line naming any `rules-*` pack enabled at user scope (tests first); commit and push (owner's confirmation). Plugins are not pinned, so `candle` needs no re-pin.
- [ ] **Step 2:** Ask the owner to confirm moving `~/.claude/skills/humanizer` to `~/.claude/skills.retired/humanizer`, and to turn off `anthropic-skills:unslop` in `/skills` themselves.

---

## Added during execution

### Task A6: Base rules reach subagents

Measured in Task B4: `core`'s `SessionStart` context reaches the main session only; a subagent's context has no `# Base rules`, while before the migration subagents inherited `CLAUDE.md` §1–§3. The documented `SubagentStart` hook (`hookSpecificOutput.additionalContext`, 10,000-character cap, fires for built-in, project and plugin agents) closes the gap.

**Files:** Create `plugins/core/hooks/subagent_start.py`; Modify `plugins/core/hooks/hooks.json`, `plugins/core/base.md` (section markers if needed); Test `tests/hooks/test_subagent_start.py`, `tests/hooks/test_hooks_json.py`

- [ ] **Step 1: Write the failing tests:** emits JSON with `hookEventName == "SubagentStart"` and `additionalContext` = `base.md` without its independent-review section (a subagent never dispatches reviews; its controller does); silent on internal error; runs under Python 3.9; `hooks.json` pins the `SubagentStart` entry (no matcher, command path).
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement**, following `session_start.py`'s pattern (3.9, stdlib, one `try`, `except BaseException` silent). No pack check in subagents.
- [ ] **Step 4: Real check:** `claude --plugin-dir ~/git/claude-plugins/plugins/core -p "Dispatch one general-purpose subagent with the prompt: 'Answer yes or no: does your context contain a section headed # Base rules? Then stop.' and report its answer verbatim."` → yes. Record it in the commit message.
- [ ] **Step 5:** Commit `feat(core): base rules reach subagents`.

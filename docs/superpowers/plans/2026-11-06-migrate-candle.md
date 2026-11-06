# Migrate candle onto claude-plugins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `candle` uses the `datazard-plugins` marketplace and the `claude-plugins-tools` package instead of its copied skills, its `scripts/wiki`, `scripts/facts_check.py`, `scripts/facts_report.py` and the rule pages the packs now hold, with its CI green; and `core` receives what this first migration needs.

**Architecture:** Two repositories, in order. Part A changes `claude-plugins` (`~/git/claude-plugins`, branch `migrate/candle-prereqs`) and publishes a commit; Part B migrates `candle` (`~/git/candle`, branch `plugins/migrate`, from `origin/main`) pinned to that commit. A one-off migration script, kept in `claude-plugins/tools/` for the later migrations, rewrites `candle`'s citations from `docs/rule-classification.md`.

**Tech Stack:** Python 3.14, uv workspaces, pytest, the `cpt` CLI, GitHub Actions, Claude Code plugins.

**Spec:** `~/git/claude-plugins/docs/superpowers/specs/2026-11-06-claude-plugins-design.md` (sections *What stays in each project*, *Citing a rule that left the wiki*, *The `qa` agent*, *Detecting a session without its rules*). Plan 1: `docs/superpowers/plans/2026-11-06-build-claude-plugins.md` (its *Left for plan 2* section and the owner's decision recorded at its end).

## Global Constraints

- `candle`'s working language is English; its dated specs and plans under `docs/superpowers/` are archives and are **not rewritten**.
- Pin: `candle`'s `pyproject.toml` gets `claude-plugins-tools` in its root `[dependency-groups] dev` and `[tool.uv.sources] claude-plugins-tools = { git = "https://github.com/aneuraz/claude-plugins", rev = "<Part A's published SHA>" }`; never a branch or tag.
- Plugin ids: `<plugin>@datazard-plugins`. `candle` enables `core`, `rules-security`, `rules-python`, `rules-typescript`, `rules-health-data`, `rules-untrusted-parsing`.
- A rule page whose classification row says `target = rules-<pack>:<slug>` and no `split` leaves `candle`'s wiki (deleted; git keeps it). A `split` page stays at its slug with the project's application only, citing the pack rule. A `stays` page stays.
- Citations: a moved rule is cited `<pack>:<slug>` — in code and configuration as the bare token; in Markdown, a link `[<text>](<path to rules/<slug>.md>)` becomes `<text> (`<pack>:<slug>`)`.
- Skill text and `CLAUDE.md` name skills with their plugin prefix (`core:updating-the-wiki`).
- `candle`'s `CLAUDE.md` carries the line that stops a session without `core`'s base rules (spec *Detecting a session without its rules*).
- Every `candle` commit runs the CI's commands locally first: `uv run cpt facts --orphans`, `uv run cpt wiki check --base origin/main`, `uv run pytest -q` (non-integration), `uv run ruff check`, `uv run ruff format --check`.
- Pushing either repository, and opening the `candle` PR, waits for the owner's confirmation.

## Review Focus

1. **A citation the script cannot map** (a `wiki:rules/<slug>` whose slug has no classification row, or a link with an anchor `rules/<slug>.md#x`): the script must list it and leave it untouched, never guess; `cpt wiki check` then reports it.
2. **A citation inside a dated archive** (`docs/superpowers/**`): the script must skip it; the archive rule keeps it valid.
3. **A `split` page cited from elsewhere**: its slug survives, so citations to it stay as they are (the script reports them as kept, not rewritten).
4. **A session in `candle` where the marketplace did not load**: the `CLAUDE.md` line must make the agent stop and say so (Task B4's real-session check runs it with the plugins disabled).
5. **CI on a GitHub runner**: `uv sync --locked` must fetch the pinned git dependency without credentials (public repository) — checked by a pushed draft PR's run, Task B5.

---

## Part A — `claude-plugins`

### Task A1: Deferred fixes the first migration meets

**Files:** Modify `plugins/core/skills/updating-the-wiki/SKILL.md`, `plugins/core/skills/qa/SKILL.md`, `plugins/core/skills/qa/METHOD.md`

- [ ] **Step 1:** `updating-the-wiki`: move the `[wiki] tooling` / `[tooling] command` key check from step 5 to step 0, so a missing key stops the ingest before any page or log is written.
- [ ] **Step 2:** `qa` SKILL.md step 7: the hand-over names `down_respect_keep` for a kept run, `down` otherwise.
- [ ] **Step 3:** `qa` METHOD.md: restore the worktree read row ("Read, Grep, Glob inside the worktree") and add a sentence that the project's agent file carries its command-writing rules (quoting, one-line questions).
- [ ] **Step 4:** Run `uv run pytest tests/test_layout.py tests/wiki/test_skills.py -q` and `claude plugin validate plugins/core`. Expected: PASS.
- [ ] **Step 5:** Commit `fix(core): what the first migration meets`.

### Task A2: The generic halves of `documentation-chain` and `project-tracking` into `core`

**Files:** Modify `plugins/core/skills/github-project-tracking/SKILL.md`, `plugins/core/skills/spec-to-facts/SKILL.md`; Modify `docs/rule-classification.md`

- [ ] **Step 1:** Read `git -C ~/git/candle show origin/main:docs/wiki/rules/project-tracking.md` and `…:docs/wiki/rules/documentation-chain.md`. List each section as generic or `candle`'s own (the owner's decision at the end of plan 1 names the generic ones).
- [ ] **Step 2:** `github-project-tracking` gains a section *What you discover along the way* (the four discoveries and their four destinations, the debt's unacceptability clause, "none is settled in silence") and *Closing a decision* (closed by a decision page with its reason, the commit linked before closing), written as `candle`'s page states them, without `candle` names.
- [ ] **Step 3:** `spec-to-facts` gains, in its lifecycle: the milestone's cross-cutting consistency review before the PR leaves draft; every milestone ends with a documentation task; what git does not track does not exist (check what you write is committed).
- [ ] **Step 4:** `docs/rule-classification.md`: the two rows become `split` with a note naming where the generic halves went.
- [ ] **Step 5:** Run `uv run pytest -q` and `claude plugin validate plugins/core`. Expected: PASS.
- [ ] **Step 6:** Commit `feat(core): the generic halves of documentation-chain and project-tracking`.

### Task A3: The citation migration script

**Files:** Create `tools/migrate_citations.py`; Test `tests/tools/test_migrate_citations.py`

**Interfaces:**
- Produces: `uv run python tools/migrate_citations.py --repo <path> --source <name> [--apply]` — reads `docs/rule-classification.md` rows whose `source` starts with `<name>:`; without `--apply` prints the plan (one line per rewrite, per kept citation, per unmapped citation, per page to delete) and exits 0; with `--apply` rewrites files and deletes moved pages; exit 1 if any citation is unmapped. Functions: `load_classification(path: Path, source: str) -> Mapping[str, Target]` with `Target(pack_citation: str | None, split: bool)`; `rewrite(text: str, kind: Literal["code", "markdown"], table) -> tuple[str, list[Event]]`.

- [ ] **Step 1: Write the failing tests:** `test_code_citation_rewritten` (`# wiki:rules/parameterised-sql` → `# rules-security:parameterised-sql`); `test_markdown_link_rewritten` (`[Every SQL query MUST be parameterised](../rules/parameterised-sql.md)` → `Every SQL query MUST be parameterised (`rules-security:parameterised-sql`)`, any number of `../`, and `docs/wiki/rules/…` from the repository root); `test_split_slug_kept`; `test_stays_slug_kept`; `test_unknown_slug_reported_unmapped`; `test_anchor_link_reported_unmapped`; `test_archives_skipped` (any path under `docs/superpowers/`); `test_apply_deletes_moved_pages_only`; `test_dry_run_changes_nothing`.
- [ ] **Step 2: Run** `uv run pytest tests/tools -q`. Expected: FAIL.
- [ ] **Step 3: Implement.** Files scanned: `git -C <repo> ls-files` text files, minus `docs/superpowers/**`, minus the pages being deleted. Markdown = `*.md`; everything else = code.
- [ ] **Step 4: Run** the tests and `uv run python tools/migrate_citations.py --repo ~/git/candle --source candle` (dry run). Expected: PASS; the dry run lists the rewrites and reports 0 unmapped, or lists the unmapped ones for Task B2 to settle.
- [ ] **Step 5:** Commit `feat(tools): the citation migration script`.

### Task A4: Publish the pin

- [ ] **Step 1:** Ask the owner to confirm pushing `main` (fast-forward from `migrate/candle-prereqs`, with the earlier unpushed `87b6afc`).
- [ ] **Step 2:** `git switch main && git merge --ff-only migrate/candle-prereqs && git push origin main`.
- [ ] **Step 3:** Record `git rev-parse HEAD` as the pin for Part B.

---

## Part B — `candle` (branch `plugins/migrate` from `origin/main`)

### Task B1: Tooling from the package

**Files:**
- Modify: `pyproject.toml` (dev group + source pin), `uv.lock`, `conftest.py:6`, `.github/workflows/ci.yml:84,94,233`, `tests/contracts/test_ci.py:43,96,113`, `tests/contracts/test_port.py:10`, `docs/wiki/reference/development-dependencies.md` (trace the new dependency; drop the `pyyaml` line if no `candle` code imports `yaml` any more), `docs/wiki/howto/application-tests.md:11,23`
- Create: `.claude/project.toml` (the `candle` example of `claude-plugins`'s `docs/project-toml.md`, at the pin)
- Delete: `scripts/wiki/`, `scripts/facts_check.py`, `scripts/facts_report.py`, `tests/contracts/test_facts_check.py`, `tests/helpers/wiki.py`, and the engine tests of `tests/contracts/test_wiki.py` and `tests/contracts/test_wiki_skills.py`
- Regenerate: `docs/wiki/index.md` (`uv run cpt wiki index`)

- [ ] **Step 1:** Edit `test_ci.py` to expect `pytest_plugins = ("claude_plugins_tools.facts.report",)` and the `uv run cpt facts …` / `uv run cpt wiki check …` steps (`--reports reports` keeps `--locked`). Run it. Expected: FAIL.
- [ ] **Step 2:** Make the changes listed. `test_port.py` imports `expand_ranges` from `claude_plugins_tools.facts.check`. Keep in `tests/contracts/test_wiki.py` only the five tests that check `candle` itself (plan 1 Task 10 names them), calling `cpt` instead of `scripts.wiki`; delete the rest and `test_wiki_skills.py`'s engine tests.
- [ ] **Step 3: Run** the global constraints' commands and `uv run pytest tests/contracts -q`. Expected: all pass; `cpt wiki check` passes with the regenerated index.
- [ ] **Step 4:** Commit `build: the wiki and facts tools come from claude-plugins-tools`.

### Task B2: Rule pages leave the wiki

**Files:** Modify every file the script rewrites; Delete the moved rule pages; Modify the six `split` pages, the hubs that list rules (`docs/wiki/hubs/*`, 11 files), `SECURITY.md`; Append `docs/wiki/log.md`; Regenerate `docs/wiki/index.md`

- [ ] **Step 1:** Dry run `uv run --project ~/git/claude-plugins python ~/git/claude-plugins/tools/migrate_citations.py --repo . --source candle`; settle every unmapped citation by hand (record each in the commit message).
- [ ] **Step 2:** `--apply`.
- [ ] **Step 3:** Reduce each `split` page to `candle`'s application: its title states the application, its first line cites the pack rule, the generic text goes.
- [ ] **Step 4:** Hubs: each list item of a moved rule becomes `<title> (`<pack>:<slug>`)`; a hub left with no `candle` page is kept, listing the pack rules it frames. `SECURITY.md`'s *Code security rules* paragraph names the packs `candle` enables and the security hub.
- [ ] **Step 5:** `docs/wiki/log.md`: one ingest entry "Rules moved to the datazard-plugins packs" listing the touched pages (`core:updating-the-wiki`'s form). Regenerate the index.
- [ ] **Step 6: Run** the global constraints' commands, and `uv run cpt wiki search sql injection` from `candle`. Expected: all pass; the search lists `rules-security:parameterised-sql`.
- [ ] **Step 7:** Commit `docs(wiki): rule pages held by the packs leave the wiki`.

### Task B3: `documentation-chain` and `project-tracking` keep `candle`'s application

**Files:** Modify `docs/wiki/rules/documentation-chain.md`, `docs/wiki/rules/project-tracking.md`, `docs/wiki/log.md`

**Interfaces:** Consumes Task A2's sections in `core:github-project-tracking` and `core:spec-to-facts`.

- [ ] **Step 1:** Remove from both pages the sections Task A2 moved; each page cites the core skill section that now holds them. If the `tracking/priority-and-size` branch has been merged by then (owner's call, see *Before execution*), keep its *Priority and size* section untouched.
- [ ] **Step 2:** Log entry; regenerate the index; run the global constraints' commands. Expected: pass.
- [ ] **Step 3:** Commit `docs(wiki): documentation-chain and project-tracking keep candle's application`.

### Task B4: Skills from the plugins, `CLAUDE.md` reduced

**Files:**
- Create: `.claude/settings.json` (`extraKnownMarketplaces.datazard-plugins = {"source": {"source": "github", "repo": "aneuraz/claude-plugins"}}`, `enabledPlugins` as in the global constraints)
- Delete: `.claude/skills/{codebase-design,domain-modeling,github-project-tracking,qa,reading-the-wiki,spec-to-facts,unslop,updating-the-wiki,writing-for-agents}` (the `archify` symlink stays)
- Modify: `.claude/agents/qa.md` (body: the surfaces table, the command-writing rules, "follow the method in your delegation prompt"; frontmatter unchanged), `CLAUDE.md`, the pages naming skills without prefix (`docs/wiki/debts/skills-moved-out-of-their-checker.md`, `docs/wiki/lessons/engine-interface-redone-before-execution.md`, `tests/contracts/test_wiki.py` if any expectation names a skill)

- [ ] **Step 1: `CLAUDE.md`:** remove §1–§3 and the unslop line (now `core`'s `base.md`); §4 keeps "the CI is authoritative" and points to `rules-python:ruff-and-noqa-discipline`; §5–§7 stay; add the stop line; the routing table points to pack rules and `core:` skills. Target: under 3,000 characters.
- [ ] **Step 2:** The other edits listed.
- [ ] **Step 3: Real-session checks** in `candle` (after `claude plugin marketplace update datazard-plugins`): `claude -p "List the skills you have whose name starts with core:, and quote the first heading of your base rules."` → names `core:updating-the-wiki` and quotes `# Base rules`; `claude --disable-plugins -p "Summarise your base rules."` (or the documented way to start without plugins) → the answer says the plugins did not load and stops. Record both answers in the commit message.
- [ ] **Step 4: Run** the global constraints' commands. Expected: pass.
- [ ] **Step 5:** Commit `chore: skills come from the datazard-plugins marketplace`.

### Task B5: Prove it in CI

- [ ] **Step 1:** Ask the owner to confirm pushing `plugins/migrate` and opening a **draft** PR on `aneuraz/candle`.
- [ ] **Step 2:** `git push -u origin plugins/migrate`; `gh pr create --draft` with a body listing Parts A–B, the pin, and the rulings. Watch the run; every job except the facts gate (which waits for ready-for-review) must pass, `uv sync --locked` included.
- [ ] **Step 3:** Report the run's link and result. Moving the PR to ready and merging stay the owner's.

---

## Part C — the owner's user configuration

### Task C1: One source for writing guidance, and the declaration stays the project's

- [ ] **Step 1: Check the declaration cannot be widened:** in a scratch directory with a `.claude/settings.json` enabling only `core@datazard-plugins`, enable `rules-rust@datazard-plugins` at user scope (`claude plugin enable rules-rust@datazard-plugins --scope user`), run `claude plugin list --json`, then disable it again. Record whether the user scope adds the pack to that project. If it does, add to `docs/project-toml.md`'s neighbour `README.md` the rule "never enable a `rules-*` pack at user scope" and to `core`'s `session_start.py` a line naming any `rules-*` pack enabled at user scope (test first); commit in `claude-plugins` and re-pin `candle` (Task A4's steps).
- [ ] **Step 2: Ask the owner** to confirm retiring the user-level `~/.claude/skills/humanizer` (moved to `~/.claude/skills.retired/humanizer`, not deleted) and to turn off `anthropic-skills:unslop` in `/skills` themselves (a claude.ai account setting; the spec leaves deleting it there to the owner).

---

## Before execution — the owner decides

- The `tracking/priority-and-size` branch of `candle` (uncommitted *Priority and size* section in `docs/wiki/rules/project-tracking.md`): commit and merge it first, or fold it into Task B3.

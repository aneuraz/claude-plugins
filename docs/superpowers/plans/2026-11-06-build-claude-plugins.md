# Build claude-plugins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `claude-plugins` repository: the marketplace, the `core` plugin, the seven `rules-*` packs and the `cpt` tooling package, ready for the first project to migrate (plan 2).

**Architecture:** One repository is at once a Claude Code marketplace (`.claude-plugin/marketplace.json`, plugins under `plugins/`) and a Python package (`pyproject.toml` at the root, code in `src/claude_plugins_tools/`). The package's wheel bundles the packs' rule files, so CI and confined agents resolve and search rules without the plugins installed. Hooks are small Python scripts run with the system `python3`, standard library only.

**Tech Stack:** Python 3.14 (package), Python ≥ 3.11 standard library (hooks: `tomllib`, `json`, `subprocess`), uv, hatchling, pytest, ruff, PyYAML.

**Spec:** `docs/superpowers/specs/2026-11-06-claude-plugins-design.md`

**Sources:** `candle` at `origin/main` = `275bce0` (`~/git/candle`), `candle-qa` (`~/git/candle-qa`), `candle-pseudo` (`~/git/candle-pseudo`), `capture` (`~/git/capture`). Read sources with `git -C ~/git/candle show 275bce0:<path>`; never edit those repositories in this plan.

## Global Constraints

- The repository is public; no secret, no real data, no personal path in any committed file.
- Everything in the plugins is written in English.
- Plugin names: `core`, `rules-security`, `rules-python`, `rules-rust`, `rules-typescript`, `rules-swift`, `rules-health-data`, `rules-untrusted-parsing`. Marketplace name: `claude-plugins`. No `version` field in any `plugin.json` or marketplace entry (the commit SHA is the version).
- A `SessionStart` `additionalContext` string stays under 10,000 characters; `base.md` targets 6,000 or fewer.
- Hooks: standard library only, run as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<script>.py"`, and never fail a session: on any internal error they exit 0 with no output.
- A skill never links out of the plugin with a relative path; a project file is named by its path from the repository root.
- A pack file holds no link into any project. A pack rule is never renamed or removed without a `superseded_by` entry keeping its old slug resolvable.
- `.claude/project.toml` is the only project-side facts file; every reader treats a missing file or key as "not configured" and says so, never guesses.
- Package distribution name `claude-plugins-tools`, import `claude_plugins_tools`, one console script `cpt` with subcommands `facts` and `wiki`.

## Review Focus

1. **A project with no `.claude/project.toml`** (korps, or a repository not migrated yet): every hook and `cpt` command must say "not configured" and exit cleanly, never crash or invent defaults that point at `candle`.
2. **`claude plugin list --json` unavailable, slow or changed in shape**: the `SessionStart` hook must still emit `base.md` and drop only the pack check (timeout 5 s).
3. **A citation to a renamed pack rule**: `cpt wiki check` must resolve it through `superseded_by` and report the new citation, not fail.
4. **A non-ASCII or very long `base.md`** after an edit: the size test counts characters, not bytes, and fails above 10,000.
5. **A skill invoked whose name is not one of the review points, or a hook input with no `tool_input.skill`**: the review hook stays silent.

---

## File structure

```
claude-plugins/
├── .claude-plugin/marketplace.json
├── .github/workflows/ci.yml
├── LICENSE                                  (owner's choice, Task 1)
├── README.md
├── pyproject.toml
├── docs/project-toml.md                     the project-side facts schema
├── plugins/
│   ├── core/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── base.md
│   │   ├── hooks/hooks.json
│   │   ├── hooks/session_start.py
│   │   ├── hooks/review_reminder.py
│   │   └── skills/{unslop,writing-for-agents,codebase-design,domain-modeling,
│   │              spec-to-facts,reading-the-wiki,updating-the-wiki,qa,
│   │              github-project-tracking}/SKILL.md (+ their reference files)
│   └── rules-<pack>/
│       ├── .claude-plugin/plugin.json
│       └── skills/<pack>/SKILL.md, skills/<pack>/rules/<slug>.md
├── src/claude_plugins_tools/
│   ├── __main__.py                          `cpt` entry point
│   ├── project.py                           reads .claude/project.toml
│   ├── packs.py                             loads bundled pack rules
│   ├── facts/{check.py,report.py}
│   └── wiki/{…ported modules…, search.py}
└── tests/
    ├── test_layout.py
    ├── hooks/test_session_start.py, test_review_reminder.py
    ├── facts/…, wiki/…, test_packs.py, test_project.py
```

---

### Task 1: Repository skeleton, marketplace and layout test

**Files:**
- Create: `.claude-plugin/marketplace.json`, `plugins/core/.claude-plugin/plugin.json`, `pyproject.toml`, `README.md`, `LICENSE`, `.github/workflows/ci.yml`, `.gitignore`
- Test: `tests/test_layout.py`

**Interfaces:**
- Produces: the layout every later task fills; `tests/test_layout.py` is extended by later tasks only through its parametrisation (it discovers plugins and skills on disk).

- [ ] **Step 1: Ask the owner which licence the public repository carries** (MIT, Apache-2.0, or another). Do not pick one. Write it to `LICENSE`.
- [ ] **Step 2: Write the failing layout test** `tests/test_layout.py`:
  - `test_marketplace_lists_every_plugin`: the `name`s in `marketplace.json`'s `plugins` equal the directory names under `plugins/`; each entry's `source` is `./plugins/<name>`; no entry and no `plugin.json` has a `version` key.
  - `test_plugin_manifest(plugin)` (parametrised over `plugins/*`): `.claude-plugin/plugin.json` parses, its `name` equals the directory name, and nothing but `plugin.json` sits in `.claude-plugin/`.
  - `test_skill_frontmatter(skill)` (parametrised over `plugins/*/skills/*/SKILL.md`): YAML frontmatter with non-empty `name` equal to the directory name and non-empty `description`.
  - `test_no_relative_link_out_of_a_plugin(md)` (parametrised over every `.md` under `plugins/`): every relative Markdown link resolves to a file inside the same plugin directory.
- [ ] **Step 3: Run** `uv run pytest tests/test_layout.py -v`. Expected: FAIL (no `marketplace.json`).
- [ ] **Step 4: Create the files.** `marketplace.json`: `name: "claude-plugins"`, `owner: {"name": "aneuraz"}`, `plugins: [{"name": "core", "source": "./plugins/core", "description": …}]`. `pyproject.toml`: hatchling, `requires-python = ">=3.14"`, dependency `pyyaml`, dev group `pytest`, `ruff`; `[project.scripts] cpt = "claude_plugins_tools.__main__:main"`; ruff config copied from `candle`'s root `pyproject.toml` (`git show 275bce0:pyproject.toml`). `ci.yml`: on push and pull request, `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`. `README.md`: what the repository is, how a project declares it (the `extraKnownMarketplaces` / `enabledPlugins` block of the spec), and that each user turns on auto-update once in `/plugin`.
- [ ] **Step 5: Run** `uv run pytest tests/test_layout.py -v` and `claude plugin validate plugins/core`. Expected: PASS, and validate reports no error.
- [ ] **Step 6: Commit** `feat: marketplace skeleton and layout test`.

### Task 2: `base.md` and the `SessionStart` hook

**Files:**
- Create: `plugins/core/base.md`, `plugins/core/hooks/hooks.json`, `plugins/core/hooks/session_start.py`
- Test: `tests/hooks/test_session_start.py`

**Interfaces:**
- Consumes: `.claude/project.toml` is not read here; the declared packs come from the project's `.claude/settings.json`.
- Produces: `session_start.main(stdin: str, env: Mapping[str, str], list_plugins: Callable[[Path], list[dict] | None]) -> str` returning the hook's stdout (a JSON string, or `""`); the script's `__main__` calls it with `sys.stdin.read()`, `os.environ` and the real lister.

- [ ] **Step 1: Write `base.md`** from `candle`'s `CLAUDE.md` §1–§4 (`git show 275bce0:CLAUDE.md`), generic parts only: think before coding, simplicity first (with the comment rule), surgical changes, completion gate reduced to "the CI is authoritative; checks pass locally before a task is declared done" (the ruff paragraph goes to `rules-python`, Task 11). Add:
  - a condensed `unslop`: the numbered list of tells from `candle`'s `unslop/SKILL.md`, one line each, no examples;
  - the three independent-review points, worded as in the spec's *Independent reviews around superpowers*;
  - one line: "Rules for this project's languages and data come from the `rules-*` packs it enables; find one with `cpt wiki search <terms>` or by invoking the pack's skill."
- [ ] **Step 2: Write the failing tests:**
  - `test_base_md_fits`: `len(base.md text) <= 6000` characters.
  - `test_emits_base_md`: `main('{"source":"startup"}', env_with_plugin_root, lister_returning([]))` returns JSON whose `hookSpecificOutput.hookEventName == "SessionStart"` and whose `additionalContext` starts with `base.md`'s text.
  - `test_reports_missing_pack`: a temp project with `.claude/settings.json` enabling `rules-python@claude-plugins` and `core@claude-plugins`; a lister returning only `core@claude-plugins` as enabled for that project → `additionalContext` ends with a line naming `rules-python@claude-plugins` as declared but not loaded.
  - `test_lister_unavailable`: lister returns `None` → `base.md` emitted, no pack line.
  - `test_context_stays_under_cap`: the emitted `additionalContext` is under 10,000 characters for 7 missing packs.
  - `test_internal_error_is_silent`: `env` without `CLAUDE_PLUGIN_ROOT` → returns `""`.
- [ ] **Step 3: Run** `uv run pytest tests/hooks/test_session_start.py -v`. Expected: FAIL (module missing).
- [ ] **Step 4: Implement `session_start.py`.** Declared packs: keys of `enabledPlugins` in `$CLAUDE_PROJECT_DIR/.claude/settings.json` whose value is `true` and whose name ends `@claude-plugins`. Loaded: the real lister runs `claude plugin list --json` with `cwd=project`, timeout 5 s, and keeps entries with `enabled` true; any failure returns `None`. `hooks.json`: one `SessionStart` entry, no matcher (all sources), command `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"`.
- [ ] **Step 5: Run** the tests. Expected: PASS.
- [ ] **Step 6: Check in a real session:** `claude plugin marketplace add ~/git/claude-plugins` then, in a scratch directory with a `.claude/settings.json` enabling `core@claude-plugins`, `claude -p "Quote the first heading of the base rules in your context."`. Expected: the answer quotes `base.md`'s first heading. Remove the marketplace afterwards (`claude plugin marketplace remove claude-plugins`).
- [ ] **Step 7: Commit** `feat(core): base rules injected at session start`.

### Task 3: The review-reminder hook

**Files:**
- Create: `plugins/core/hooks/review_reminder.py`; Modify: `plugins/core/hooks/hooks.json`
- Test: `tests/hooks/test_review_reminder.py`

**Interfaces:**
- Produces: `review_reminder.main(stdin: str) -> str`; `REVIEW_POINTS: Final[Mapping[str, str]]` mapping a skill name to its reminder.

- [ ] **Step 1: Measure the hook input.** Add a temporary `PostToolUse` hook, matcher `Skill`, command `cat >> "$TMPDIR/skill-hook.jsonl"`, to a scratch project's `.claude/settings.json`; run `claude -p "Use the superpowers:writing-plans skill on nothing; stop after loading it."`. Record the `tool_input` shape. Expected: it carries the skill's name (the tool's parameters are `skill` and `args`). If it does not, stop this task, keep `base.md`'s rule alone, and record the finding in the spec's *Independent reviews* bullet.
- [ ] **Step 2: Write the failing tests** with the measured shape:
  - `test_reminds_after_writing_plans`: input for `superpowers:writing-plans` → JSON `hookSpecificOutput.hookEventName == "PostToolUse"`, `additionalContext` naming an independent review of the plan by a fresh agent handed the plan.
  - `test_reminds_for_each_point`: same for `superpowers:brainstorming` (the spec), `superpowers:subagent-driven-development`, `superpowers:executing-plans` and `superpowers:finishing-a-development-branch` (the branch's diff, before finishing).
  - `test_silent_for_other_skills`: `core:unslop` → `""`.
  - `test_silent_without_skill_name` and `test_silent_on_bad_json` → `""`.
- [ ] **Step 3: Run** them. Expected: FAIL.
- [ ] **Step 4: Implement**, and add the `PostToolUse` entry (matcher `Skill`) to `hooks.json`.
- [ ] **Step 5: Run** the tests. Expected: PASS.
- [ ] **Step 6: Commit** `feat(core): remind the independent review at the three points`.

### Task 4: The project-side facts schema and its reader

**Files:**
- Create: `docs/project-toml.md`, `src/claude_plugins_tools/project.py`, `src/claude_plugins_tools/__init__.py`
- Test: `tests/test_project.py`

**Interfaces:**
- Produces: `load_project(root: Path) -> Project` (missing file → every field `None` or empty); `ProjectError(Exception)` for a malformed file, naming the file and the key. `Project` is a frozen dataclass, one field per key below, plus `root: Path`.

| Section | Key | Type | Meaning |
|---|---|---|---|
| `[repository]` | `name` | str | `owner/repo` |
| | `siblings` | list[str] | `owner/repo` of the repositories it cites |
| | `issue_reference` | str | format of an issue reference in prose, with `{repo}` and `{n}` (`candle`: `"candle-legacy#{n}"`) |
| | `foreign_commit_url` | str | format with `{repo}`, `{commit}`, `{path}` |
| `[wiki]` | `path` | str | the wiki's directory (`docs/wiki`) |
| | `tooling` | `"cpt"` or `"none"` | `none`: the index is kept by hand |
| `[tracking]` | `project` | str | the tracking Project's title |
| | `rule_page` | str | the project's tracking rule page, from the root |
| `[qa]` | `up`, `down`, `status`, `guard` | str | command lines |
| | `keep` | str | flag that leaves the stack up, optional |
| | `errors_dir` | str | directory of stack-error files for the Monitor, optional |
| | `tooling_paths` | list[str] | paths whose change by the branch stops the run to ask |

- [ ] **Step 1: Write `docs/project-toml.md`**: the table above, each key with `candle`'s value as the example (from `candle`'s `updating-the-wiki`, `github-project-tracking` and `qa` copies). Skills cite the schema by its keys, not by path.
- [ ] **Step 2: Write the failing tests:** `test_missing_file_is_unconfigured`, `test_reads_candle_example` (the example of `docs/project-toml.md` parsed into the expected `Project`), `test_malformed_names_key` (`siblings = "x"` → `ProjectError` whose message names `repository.siblings`), `test_unknown_key_refused` (an unknown key is an error, naming it).
- [ ] **Step 3: Run** them. Expected: FAIL.
- [ ] **Step 4: Implement** `load_project` with `tomllib`.
- [ ] **Step 5: Run** them. Expected: PASS.
- [ ] **Step 6: Commit** `feat(tools): the project-side facts file`.

### Task 5: Skills moved as they are

**Files:**
- Create: `plugins/core/skills/{unslop,writing-for-agents,codebase-design,domain-modeling}/` with their reference files (`codebase-design/DEEPENING.md`, `DESIGN-IT-TWICE.md`; `domain-modeling/ADR-FORMAT.md`, `CONTEXT-FORMAT.md`; `writing-for-agents/SKILL-MECHANICS.md`)

- [ ] **Step 1: Copy** each from `candle` at `275bce0`. For `codebase-design`, diff `fhirforge`'s `DESIGN-IT-TWICE.md` against `candle`'s and keep `candle`'s unless `fhirforge`'s holds content `candle`'s lacks; if so, merge it and say so in the commit message.
- [ ] **Step 2: Remove repository specifics**: any mention of `candle`, `CLAUDE.md` sections by number, or a project path. `unslop`'s description stays "Cut AI tells from any writing"; drop "Must always apply" (`base.md` carries the always-on part).
- [ ] **Step 3: Run** `uv run pytest tests/test_layout.py -v` and `claude plugin validate plugins/core`. Expected: PASS.
- [ ] **Step 4: Commit** `feat(core): unslop, writing-for-agents, codebase-design, domain-modeling`.

### Task 6: The wiki skills and `github-project-tracking`, generic

**Files:**
- Create: `plugins/core/skills/{reading-the-wiki,updating-the-wiki,github-project-tracking}/SKILL.md`

**Interfaces:**
- Consumes: the keys of `docs/project-toml.md` (Task 4); `cpt wiki index|check|search|show` (Tasks 9–10).

- [ ] **Step 1: Write `reading-the-wiki`** from `candle`'s copy: step 0 reads `.claude/project.toml`; when `[wiki]` is absent the skill says the project has no wiki and goes to the packs only. Search order: the project's wiki through its index, then `cpt wiki search <terms>`, which also covers the enabled packs. The skill answers "no rule covers this" only after both. Its description keeps the trigger words of `candle`'s ("why something is built the way it is, which rule governs it, or how to run a procedure") and adds "before concluding that no rule applies".
- [ ] **Step 2: Write `updating-the-wiki`** from `candle`'s copy, with the issue-reference form, the foreign-commit URL and the tooling commands read from `.claude/project.toml` (`cpt wiki index`, `cpt wiki check`); the `candle-legacy` migration step (`doctrine-map`) does not move (that repository stays frozen); `candle-pseudo`'s hand-written index step applies when `[wiki]` says `tooling = "none"`.
- [ ] **Step 3: Write `github-project-tracking`** from `candle`'s copy: the Project's title from `[tracking] project`, else ask; the programme's repositories from `[repository] siblings`; the link to `project-tracking.md` named as the project's tracking rule page from `[tracking] rule_page`.
- [ ] **Step 4: Run** `uv run pytest tests/test_layout.py -v` and `grep -rn "candle" plugins/core/skills/{reading-the-wiki,updating-the-wiki,github-project-tracking}`. Expected: PASS, and `candle` appears only as an example value.
- [ ] **Step 5: Commit** `feat(core): wiki and tracking skills read the project-side facts`.

### Task 7: `spec-to-facts`, split

**Files:**
- Create: `plugins/core/skills/spec-to-facts/SKILL.md` and `references/` (method parts); the pytest parts go to `plugins/rules-python/skills/rules-python/rules/` in Task 11, listed here.

- [ ] **Step 1: Split `candle`'s `spec-to-facts`** (`SKILL.md`, `references/test-patterns.md`): the method (fact levels, extraction, the zero-orphan condition, the lifecycle `@draft`/`@spec`/`@implemented`/`@superseded`, the `check` contract "a command whose exit code 0 is the truth condition, naming its test") stays in `core`; `cpt facts` replaces `python scripts/facts_check.py` in every command. The pytest-specific parts (the `<file>::<function>` form, the report plugin, the CI gate job template) are written to a list in the task's commit message for Task 11.
- [ ] **Step 2: Check** the other templates in `test-patterns.md` (Jest, fast-check, Pact, icontract, Hypothesis): language-specific ones go to their pack's list too (Hypothesis and icontract → `rules-python`; Jest and fast-check → `rules-typescript`); Pact stays (cross-language).
- [ ] **Step 3: Run** `uv run pytest tests/test_layout.py -v`. Expected: PASS.
- [ ] **Step 4: Commit** `feat(core): spec-to-facts, the method`.

### Task 8: The `qa` skill, generic

**Files:**
- Create: `plugins/core/skills/qa/SKILL.md`, `plugins/core/skills/qa/METHOD.md`

- [ ] **Step 1: Write `METHOD.md`**: the body of `candle`'s `.claude/agents/qa.md` without its surfaces table and its `candle` paths: orient, write `scenarios.md` once, run, explore (hostile input included), confirm (`confirmed`/`intermittent`), report with the template; pack rules read through `cpt wiki search` and `cpt wiki show <citation>`; the report states the `core` version the session loaded.
- [ ] **Step 2: Write `SKILL.md`**: the orchestration merged from `candle`'s and `candle-qa`'s skills, with every command read from `[qa]` in `.claude/project.toml` (`up`, `down`, `status`, and optional `keep`, `errors_dir`): check variables, stop and ask when the branch changes the QA tooling (the paths come from `[qa] tooling_paths`), start the stack in the background, arm the stack-error Monitor when `errors_dir` is set, delegate to the project's `qa` agent, keep the report, tear down (`--keep` respected), hand over. It states that the agent file stays in the project and that its body must tell the agent to read `METHOD.md` from this skill.
- [ ] **Step 3: Run** `uv run pytest tests/test_layout.py -v`. Expected: PASS.
- [ ] **Step 4: Commit** `feat(core): qa, the method and the orchestration`.

### Task 9: `cpt facts`

**Files:**
- Create: `src/claude_plugins_tools/facts/{__init__,check,report}.py`, `src/claude_plugins_tools/__main__.py`
- Test: `tests/facts/` ported from `candle`'s `tests/contracts/test_facts_check.py`

**Interfaces:**
- Produces: `cpt facts [--orphans] [--implemented] [--runner LIST] [--reports DIR] [--exclude-requires LIST] [--root DIR]`; `claude_plugins_tools.facts.report` as a pytest plugin (`pytest_plugins = ("claude_plugins_tools.facts.report",)`), option `--facts-report PATH` unchanged.

- [ ] **Step 1: Port the tests** of `candle`'s `test_facts_check.py` to call `cpt facts` with `--root <fixture repo>`; add `candle-pseudo`'s cases for `--exclude-requires` and `requires_fault` (from `candle-pseudo/scripts/facts_check.py` and its tests).
- [ ] **Step 2: Run** `uv run pytest tests/facts -v`. Expected: FAIL.
- [ ] **Step 3: Port** `candle`'s `facts_check.py` and `facts_report.py`; `ROOT` becomes `--root` (default: the current directory); add `--exclude-requires` and the `requires` audit from `candle-pseudo`, so that a run without the flag behaves as `candle`'s.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Check equivalence on `candle`:** in a scratch copy of `candle` at `275bce0`, `uv run --with ~/git/claude-plugins cpt facts --orphans --root .` prints the same verdict as `uv run python scripts/facts_check.py --orphans`.
- [ ] **Step 6: Commit** `feat(tools): cpt facts`.

`capture`'s `cargo test`/`swift test` counters are not ported here: plan 2 adds them when `capture` migrates.

### Task 10: `cpt wiki`

**Files:**
- Create: `src/claude_plugins_tools/wiki/` (ported modules), `src/claude_plugins_tools/wiki/search.py`, `src/claude_plugins_tools/packs.py`
- Test: `tests/wiki/` ported from `candle`'s `tests/contracts/test_wiki.py` and `tests/helpers/wiki.py`; `tests/test_packs.py`

**Interfaces:**
- Consumes: `load_project` (Task 4).
- Produces: `cpt wiki index|check [--base REF]|search TERMS…|show CITATION [--root DIR]`; `packs.load_packs() -> Mapping[str, Pack]`; `Pack.rules: Mapping[str, Rule]`; `Rule(slug: str, title: str, path: Path, superseded_by: str | None)`; `packs.resolve(citation: str) -> Rule` raising `UnknownCitation` (follows `superseded_by` once).

- [ ] **Step 1: Port the tests**, replacing every `candle-legacy` expectation by a fixture `.claude/project.toml` whose `issue_reference` is `"candle-legacy#{n}"`; add `test_other_issue_reference_form` (`"#{n}"`), `test_pack_citation_resolves`, `test_superseded_citation_reports_new_one`, `test_unknown_pack_citation_is_a_fault`, `test_search_lists_wiki_pages_and_pack_rules`, `test_show_prints_a_rule`, `test_no_project_toml` (`check` exits 1 with "no [wiki] in .claude/project.toml").
- [ ] **Step 2: Run** `uv run pytest tests/wiki tests/test_packs.py -v`. Expected: FAIL.
- [ ] **Step 3: Port** `candle`'s `scripts/wiki/` at `275bce0`: `errors.py`'s `WikiError` derives from `Exception`; `grammar.py` and `check.py` rule 7 take the issue-reference form from the project; `archive.py`'s dated-file pattern stays (`docs/superpowers/<kind>/YYYY-MM-DD-*`), its `candle-legacy` docstring goes. `packs.py` reads the rules bundled in the wheel (`importlib.resources`, `claude_plugins_tools/packs/<pack>/<slug>.md`) and, in a source checkout, `plugins/rules-*/skills/*/rules/`. `pyproject.toml`: hatch `force-include` of each `plugins/rules-*/skills/rules-*/rules` into `claude_plugins_tools/packs/<pack>`. `search` matches every term, case-insensitively, against titles and bodies; it prints one line per hit: the citation (`wiki:<dir>/<slug>` or `<pack>:<slug>`), then the title.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Check the wheel:** `uv build` then `unzip -l dist/*.whl | grep packs/` lists the rule files.
- [ ] **Step 6: Check equivalence on `candle`:** in a scratch copy of `candle` at `275bce0` with the `.claude/project.toml` example of `docs/project-toml.md`, `cpt wiki check --root .` reports the same faults as `uv run python -m scripts.wiki check` (none).
- [ ] **Step 7: Commit** `feat(tools): cpt wiki, with pack citations and search`.

### Task 11: The rule packs from `candle`

**Files:**
- Create: `plugins/rules-{security,python,typescript,health-data,untrusted-parsing}/.claude-plugin/plugin.json`, `skills/rules-<pack>/SKILL.md`, `skills/rules-<pack>/rules/<slug>.md`; `docs/rule-classification.md`; Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: Task 7's list of pytest parts; `packs.load_packs` (Task 10) to test them.
- Produces: the rule slugs plan 2 rewrites citations to.

- [ ] **Step 1: Write `docs/rule-classification.md`**: one row per page of `candle`'s `docs/wiki/rules/` at `275bce0` (45): slug, target (`<pack>` or "stays in candle"), and, when the page carries a project application section, "split: principle → pack, application → candle". Apply the spec's two tests; the spec's table gives the examples.
- [ ] **Step 2: Write the failing test** `tests/test_packs.py::test_every_classified_rule_exists`: every row whose target is a pack has its file in that pack, with a `title` in its frontmatter; `test_no_project_link_in_packs`: no pack file contains `candle`, `../`, or `wiki:`.
- [ ] **Step 3: Run** it. Expected: FAIL.
- [ ] **Step 4: Write each rule file**: frontmatter `title`, `sources` (permalinks to `candle` at `275bce0`, or to `candle-legacy`'s `docs/security-rules.md` when the page cites it), then the rule and its reason, without the inherited numbering and without the project application. `rules-python` also receives Task 7's pytest parts and `CLAUDE.md` §4's ruff paragraph. Each pack's `SKILL.md`: a description naming the languages or data it covers, `paths` frontmatter where it applies (`rules-python`: `**/*.py`, `pyproject.toml`, `uv.lock`; `rules-typescript`: `**/*.ts`, `**/*.tsx`, `package.json`), and the list of its rules' titles with citations. `rules-security` also holds `skeleton.md` (the security sections) and `security-policy-template.md` (from `candle`'s `SECURITY.md`).
- [ ] **Step 5: Run** `uv run pytest -v` and `claude plugin validate` on each new plugin. Expected: PASS.
- [ ] **Step 6: Commit** `feat(rules): packs from candle's rule pages`.

### Task 12: `rules-rust` and `rules-swift` from `capture`

**Files:**
- Create: `plugins/rules-{rust,swift}/…` as in Task 11; Modify: `docs/rule-classification.md`, `.claude-plugin/marketplace.json`

- [ ] **Step 1: Classify** `capture/SECURITY.md`'s §1, §2 and §7 rules into `rules-rust`, `rules-swift`, or an existing `rules-security` principle they realise (add a row each to `docs/rule-classification.md`); project-specific rules (§3–§6, §8) stay in `capture`.
- [ ] **Step 2: Extend** `test_every_classified_rule_exists` by the new rows (it reads the classification file; no code change expected). Run it. Expected: FAIL.
- [ ] **Step 3: Write** the rule files and the two `SKILL.md` (`paths`: `**/*.rs`, `Cargo.toml`, `Cargo.lock`; `**/*.swift`, `Package.swift`).
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(rules): rust and swift packs from capture`.

### Task 13: An eval for `reading-the-wiki`

**Files:**
- Create: `plugins/core/evals/finds-a-pack-rule/prompt.md`, `graders/uses-search.md`, `graders/cites-rule.md`, `case.yaml`

- [ ] **Step 1: Write the case**: a fixture project with a `.claude/project.toml`, a two-page wiki, and `rules-python` enabled; the prompt asks "May I load this YAML file with `yaml.load`?". Graders: `tool_used` (a Bash call to `cpt wiki search` or the `rules-python` skill), `regex` on the answer for `rules-python:no-eval-exec-pickle-or-unsafe-yaml`.
- [ ] **Step 2: Run** `claude plugin eval plugins/core --trust-plugin --threshold 0.8 --no-publish`. Expected: WITH ≥ 0.8; the WITH/W/OUT gap is reported in the commit message. If WITH < 0.8, rework `reading-the-wiki`'s description and rerun (at most three rounds; then report to the owner).
- [ ] **Step 3: Commit** `test(core): eval for finding a pack rule`.

### Task 14: Publish

- [ ] **Step 1: Ask the owner to confirm** creating the public repository `aneuraz/claude-plugins` and pushing `main`. Do not proceed without it.
- [ ] **Step 2:** `gh repo create aneuraz/claude-plugins --public --source ~/git/claude-plugins --push`.
- [ ] **Step 3: Check** `claude plugin marketplace add aneuraz/claude-plugins` succeeds from a scratch directory, and `uv run --with "claude-plugins-tools @ git+https://github.com/aneuraz/claude-plugins@<sha>" cpt wiki search sql` lists `rules-security:parameterised-sql`.
- [ ] **Step 4:** Report the commit SHA plan 2 will pin.

---

## Left for plan 2 (migration)

Each project's `CLAUDE.md` line that stops a session without `core`'s base rules; retiring `humanizer` and turning off `anthropic-skills:unslop` in Claude Code; checking that user-level `enabledPlugins` cannot widen a project's declaration; `capture`'s `cargo test`/`swift test` counters in `cpt facts`; every repository's `.claude/project.toml`, citations and CI.

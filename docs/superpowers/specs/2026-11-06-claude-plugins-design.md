# claude-plugins: one source for the skills, agents and rules shared across projects

Date: 2026-11-06. Status: draft, awaiting the owner's approval.

## Why

The owner's Claude Code skills are copied by hand into each project. Nine repositories carry copies (`candle`, `candle-app`, `candle-legacy`, `candle-pseudo`, `candle-qa`, `capture`, `fhirforge`, `fouille`, `korps`), and the copies have drifted. Measured on 2026-11-06:

| Skill | Distinct versions |
|---|---|
| `updating-the-wiki` | 4 |
| `github-project-tracking`, `qa`, `reading-the-wiki` | 3 |
| `spec-to-facts`, `codebase-design` (`fhirforge`'s `DESIGN-IT-TWICE.md` differs) | 2 |
| `domain-modeling`, `unslop`, `writing-for-agents` | 1 |

The drift has three causes, and the design answers each:

1. **Repository facts written into a generic skill.** `updating-the-wiki` names its sibling repositories (`candle-legacy#N`, `aneuraz/candle#N`), the URL to read a foreign commit, and whether `scripts.wiki` exists.
2. **Language or project-type rules mixed into skills and `CLAUDE.md`.** `spec-to-facts` assumes pytest and `facts_check.py`; `CLAUDE.md` §4 carries ruff; `capture/SECURITY.md` and `fhirforge/SECURITY.md` state the same principles twice, once with Rust tooling, once with Python tooling.
3. **Improvements made in one copy and never carried over.** `spec-to-facts`' CI gate exists only in `candle`; `qa`'s `--keep` and its stack-error Monitor exist only in `candle-qa`; both copies check for a branch that changes the QA tooling, but `candle-qa`'s only warns where `candle`'s stops and asks.

The `CLAUDE.md` files show the same pattern: the five recent English ones share 15 to 18 of `candle`'s 22 paragraphs; the three older French ones (`capture`, `fhirforge`, `fouille`) restate the same sections in French, with project tracking and language rules inline.

## Goals

- **One source.** Every generic skill, agent and rule exists once, in this repository, and reaches every project through a Claude Code plugin marketplace.
- **Skills stay generic.** What depends on a language or a type of project leaves the skills and becomes a rule pack.
- **Rule packs follow updates.** Packs are delivered by the marketplace, not copied into each project's wiki.
- **Explicit declaration.** A project states which packs apply to it; nothing is guessed from its files.
- **`CLAUDE.md` keeps only what is the project's own.**

## Non-goals

- Replacing `github-project-tracking` with a Plane-based skill. That is the next project (`plane-project-tracking`, and a wider rework of how GitHub issues and Plane work items relate, given that the two can sync both ways). This design only leaves room for it in `core`.
- Rewriting the content of the skills beyond what the split requires.
- Distributing the plugins outside the owner's repositories.

## Anti-goals

- **A rule an agent cannot find.** Today a rule is a wiki page, found through `index.md` by `reading-the-wiki`. If moving rules into plugins makes an agent conclude that no rule covers a question, the design has failed even if every file is in place.
- **An always-on cost that grows unchecked.** Every character injected at session start is paid on every session of every project.
- **A second drift.** A project-side page that restates plugin content would drift exactly as the copies do today.

## Constraints (from the Claude Code documentation, checked 2026-11-06)

- A plugin can ship skills, agents, hooks, MCP servers, output styles and executables. It **cannot ship a `CLAUDE.md` or `.claude/rules/`**; a `CLAUDE.md` at a plugin's root is not loaded.
- The only documented way for a plugin to inject text into every session is a `SessionStart` hook emitting `additionalContext`. A field is capped at about 10,000 characters (to re-check during implementation); beyond it, Claude gets a file path and a preview.
- Skills load lazily: only their name and description sit in context; the body loads on invocation. A skill's `paths` frontmatter limits its automatic loading to matching files.
- Plugin skills are namespaced `/<plugin>:<skill>`; agents `<plugin>:<agent>`.
- `${CLAUDE_PLUGIN_ROOT}` changes with each version; `${CLAUDE_PLUGIN_DATA}` persists. Neither is in a Bash tool command's environment.
- A project declares a marketplace and its plugins in `.claude/settings.json` (`extraKnownMarketplaces`, `enabledPlugins`). A plugin with a relative-path source inside the marketplace repository loads without a per-contributor install step.
- Auto-update is off by default for a third-party marketplace; each user turns it on once. A private marketplace needs a git credential helper that answers without prompting.
- Without a `version` field, the commit SHA is the version: each push is an update.

## The design, as decided with the owner

### Repository and plugins

The repository `aneuraz/claude-plugins` (private) is the marketplace: `.claude-plugin/marketplace.json` at its root, one directory per plugin under `plugins/`, each referenced by a relative path.

```
claude-plugins/
├── .claude-plugin/marketplace.json
├── docs/superpowers/specs/          this document and its successors
└── plugins/
    ├── core/
    ├── rules-security/
    ├── rules-python/
    ├── rules-rust/
    ├── rules-typescript/
    ├── rules-swift/
    ├── rules-health-data/
    └── rules-untrusted-parsing/
```

### `core`

- **Always-on base.** A `SessionStart` hook emits `base.md`, a short file shipped in the plugin, on `startup`, `resume`, `clear` and `compact`. `base.md` holds the generic part of today's `CLAUDE.md`: think before coding, simplicity first, surgical changes, the completion-gate principle ("the CI is authoritative"), and a condensed `unslop` (the list of tells, without the examples).
- **Writing.** The `unslop` skill, complete with its examples, for reviewing a long text. `humanizer` (user level) is retired, and `anthropic-skills:unslop` (synced from claude.ai) is turned off in Claude Code: one source for that guidance there. The claude.ai copy is an account-level skill that also serves claude.ai outside Claude Code; whether to delete it there is the owner's call, outside this design.
- **Skills, moved as they are:** `writing-for-agents`, `codebase-design`, `domain-modeling`.
- **Skills, split:** `spec-to-facts` (the method; its pytest, report-plugin and `facts_check.py` parts go to `rules-python`), `reading-the-wiki` and `updating-the-wiki` (the procedure; see *Project-side facts* below).
- **QA.** A generic `qa` skill and a generic QA method: black-box testing of the current branch; oracles taken from the specs and fact-sets the diff touches; `scenarios.md` with one scenario per observable statement and a *Not observable* section; exploration of neighbouring paths including hostile input; each candidate replayed and marked `confirmed` or `intermittent`; a fixed report template; the agent confined by a guard. The project supplies a **QA contract**: a stack script exposing at least `up`, `down`, `status` and `guard`, plus any surface commands of its own (`candle`'s `cli` and `agent`; `candle-qa`'s `cli <identity>`, `transcript`, `hapi-diff`, `down --respect-keep --stop-hook`), and the list of its surfaces. The method merges the best of `candle`'s copy (stop and ask when the branch changes the QA tooling) and `candle-qa`'s (`--keep`, the stack-error Monitor). See *The `qa` agent* for what stays in the project.
- **Project tracking.** `github-project-tracking` until `plane-project-tracking` replaces it (non-goal above). Its repository facts (the Project's title: `candle` for the programme's repositories, the repository's name in `candle-qa`; the programme's repositories) move to the project-side facts, like the wiki skills'.
- **No relative link out of a skill.** A skill that links into a project's files today (`../../../docs/wiki/rules/project-tracking.md` in `github-project-tracking`, `qa`'s link to its how-to) names the project file by its path from the repository root instead, since the skill no longer sits in the repository.
- **Independent reviews around superpowers.** The owner uses the superpowers skills and asks, on top of them, for an independent review at three moments: after a spec is written (the end of `superpowers:brainstorming`), after a plan is written (`superpowers:writing-plans`), and after all of a plan's tasks are done (the end of `superpowers:subagent-driven-development` or `superpowers:executing-plans`, before `superpowers:finishing-a-development-branch`). An independent review is a fresh agent handed the artefact (the spec, the plan, the branch's diff), never the author's conclusions. superpowers is not forked and no skill wraps it: two skills competing for the same trigger lose to superpowers' own start-of-session hook. Instead:
  - `base.md` states the three review points; superpowers itself ranks user instructions above its skills.
  - A `PostToolUse` hook on the `Skill` tool re-states the review step when one of those skills loads, if the hook input carries the skill's name (to verify first; without it, `base.md` alone carries the rule).

### Rule packs

Each pack is a plugin holding one skill whose reference files are the rules, one rule per file, each with its reason, as the wiki pages carry them today. Where it helps, the skill's `paths` frontmatter scopes automatic loading (`rules-python`: `**/*.py`, `pyproject.toml`, `uv.lock`).

The split follows two tests:

- **Principle against toolchain.** A principle that holds in any language goes to `rules-security`; its realisation with a given toolchain goes to that language's pack.
- **Principle against this project's application.** Many rule pages also say how the rule applies to their project: `encrypt-at-rest-and-in-transit` has an "Applied to candle-agent" section citing R2-13 and R6-16; `data-classification` is mostly `candle`'s own table, linking into its `debts/`, `reference/`, `decisions/` and `hubs/`. The principle goes to the pack; the application stays in the project's wiki as its own page, which cites the pack rule. A pack file holds no link into any project.

Examples from `candle`'s 45 rule pages:

| Pack | Examples |
|---|---|
| `rules-security` | authorise at the data, constant-time secret comparison, no home-made cryptography, opaque error responses, parameterised SQL, submitted content is data, only configured outgoing endpoints, vet and trace every direct dependency, SBOM at each release, runtime defined by the repository, never write a version from memory |
| `rules-python` | pinned stable Python, `uv.lock` authoritative, `pip-audit` on every PR and daily, no `eval`/`exec`/`pickle`/unsafe YAML, `defusedxml`, Python rules (typing, naming, exceptions), ruff and `# noqa` discipline, `hatch-vcs` version, the pytest side of `spec-to-facts` |
| `rules-rust` | from `capture/SECURITY.md`: pinned stable toolchain, `Cargo.lock`, `cargo audit`/`cargo deny`, `#![forbid(unsafe_code)]` |
| `rules-swift` | from `capture/SECURITY.md`: checked return codes of system APIs, no forced casts |
| `rules-typescript` | TypeScript rules (Biome, pnpm) |
| `rules-health-data` | data classification, no identifier or content in logs, log every sensitive access, access logs unmodifiable by their producer, no real data in test datasets, purge checked by a test, the GDPR/CNIL breach procedure |
| `rules-untrusted-parsing` | bounded decompression, bounded image rendering, file type from magic bytes |

The security skeleton (threat model and data classification, toolchain and dependencies, dynamic code and untrusted parsing, untrusted input, no leakage, transport and cryptography, authentication and traceability, CI gates, resilience) and the `SECURITY.md` policy template (reporting a vulnerability, data breach) live in `rules-security`.

### Explicit declaration

A project's `.claude/settings.json` declares the marketplace and enables the plugins that apply to it. That list **is** the declaration. Example for `candle`: `core`, `rules-security`, `rules-python`, `rules-typescript`, `rules-health-data`, `rules-untrusted-parsing`. User-level `enabledPlugins` never enable a `rules-*` pack, so the project's list stays the whole declaration (to verify that user scope cannot widen it).

**Detecting a session without its rules.** If the marketplace fails to load, `core` is absent too, and no hook of it runs. The only check that survives that case is in the project: each project's `CLAUDE.md` carries one line telling the agent that, when `core`'s base rules are not in its context, it stops and tells the owner the plugins did not load. `core`'s `SessionStart` hook covers the partial case only: `core` loaded, a declared pack missing, found by comparing the project's `enabledPlugins` with `claude plugin list --json` (no documented variable lists the loaded plugins).

### What stays in each project

- **`CLAUDE.md`:** only what is the project's own (for `candle`: the version mechanism, the language rule and its French archives, the wiki's `doctrine-map`, the routing table to its own pages).
- **Its wiki:** its decisions, debts, defects, lessons, reference, how-tos and its own rules. Rule pages now held by a pack leave the wiki.
- **Project-side facts:** one file per repository, `.claude/project.toml`, states what the generic skills and the tooling package need to know of it: its sibling repositories, the form of an issue reference, where a foreign commit is read, whether it has a wiki, its tracking Project, its QA contract's commands. The skills read it first; the `wiki` engine reads its configuration there.
- **Its QA contract**, when it uses `qa`.

### Finding a rule

`reading-the-wiki` searches the project's wiki **and** the enabled packs before answering that no rule covers a question. One skill cannot read another plugin's files (their path is in the plugin cache, and `${CLAUDE_PLUGIN_ROOT}` is not in a Bash command's environment), so the search goes through the tooling package, which carries the packs (see *The tooling package*): `wiki search <terms>` lists the matching pages of the project's wiki and rules of its enabled packs, each with its citation. Each pack's skill also lists its rules' titles in its `SKILL.md`, so invoking a pack skill shows what it covers.

### Citing a rule that left the wiki

A rule held by a pack is cited `<pack>:<slug>` (for example `rules-security:parameterised-sql`), in markdown and in code alike, in place of `wiki:rules/<slug>` and of a relative link. The `wiki` engine's `check` resolves that form against the packs the package carries. The numbering inherited from `candle-legacy`'s `docs/security-rules.md` ("3.6 — …") is dropped.

Migrating a repository rewrites its live citations. In `candle`: 30 wiki pages, and 62 files outside the wiki, among them `ci.yml`, `release.yml`, the `Dockerfile`, `pyproject.toml`, `.gitignore` and the compose files; `tests/contracts/test_ci.py`, which pins CI step commands, changes with them. Dated specs and plans under `docs/superpowers/` are archives and are not rewritten. `candle-app` and `candle-pseudo` also cite `wiki:rules/…` and hold rule pages of their own.

### The `qa` agent

A plugin-shipped agent ignores the `hooks`, `mcpServers` and `permissionMode` of its frontmatter (documented). `candle`'s agent is confined by a frontmatter `PreToolUse` hook that fails closed (`|| exit 2`); `candle-qa`'s also relies on frontmatter `mcpServers` (Playwright, its "Application" surface) and a `Stop` hook that tears the stack down. A plugin-wide guard would run on every tool call of every session and fail open on any missed detection. So **the agent file stays in each project**: its frontmatter keeps the project's tools, hooks and MCP servers, and its body loads the method from `core`'s `qa` skill. No `qa` agent ships in a plugin.

The guard allows reads inside the worktree only (`candle/scripts/qa/guard.py`), while the agent's oracles include the guarantees of `SECURITY.md`, whose rules move to packs. The agent reads pack rules through the tooling package's `wiki search` and `wiki show <citation>`, which the guard allows as commands; it does not read the plugin cache.

The tooling-change check watches the project's QA files (`.claude/agents/qa.md`, its stack script); the method itself now comes from `core`, at the version the session loaded, and the report states that version.

### Repositories without a wiki

`candle-qa`, `capture`, `fhirforge`, `fouille` and `korps` are not given a wiki. Their project-side facts go in the same project-side facts file as the others'. `korps` has neither `CLAUDE.md` nor `SECURITY.md`; it only enables plugins.

`capture/SECURITY.md` and `fhirforge/SECURITY.md` are cited by section number across their repositories (`CLAUDE.md`, `README.md`, `Cargo.toml`, `.gitignore`, CI step names), with no checker to catch a dangling citation, and several of their sections are the project's own (e.g. `capture`'s §4.1 on its exclusion list). Their `SECURITY.md` does not shrink wholesale: a section is replaced by a pack citation only where it restates a pack rule, and each citation of it is rewritten in the same change. Project-specific sections stay. `candle-qa`'s `SECURITY.fr.md` carries a sha256 of `SECURITY.md` and follows any edit.

`capture`, `fhirforge` and `fouille` keep their French `suivi-github-project` skill until `plane-project-tracking` exists; `candle-qa` has the English `github-project-tracking` and takes `core`'s.

### `candle-legacy`

`candle-legacy` stays frozen and is not migrated, its own `facts_check.py` copy included: `candle`'s wiki pages cite commits of its history in their `sources`. Its `docs/security-rules.md` stays the cited source of the rules that move to packs; a pack rule's sources point there by permalink.

### Language

The plugins are written in English. Projects keep their own texts in their own language.

### The tooling package

A plugin does not reach CI, yet the skills and CI call the same scripts. This repository therefore also publishes one Python package, installed in each project by uv from git at a pinned commit, and called by CI and by the skills alike:

- **`facts`**: `facts_check` and `facts_report`, starting from `candle`'s, which holds no `candle`-specific reference. Four other live copies differ from it (`candle-app`, `candle-pseudo`, `candle-qa`, `capture`). The package absorbs what they do that `candle`'s does not before replacing them: `candle-pseudo`'s `--exclude-requires`, and `capture`'s counters for `cargo test` and `swift test` and its positional scope argument (`capture` has no Python project; it runs the package through `uvx`). A repository migrates to the package only once its CI's invocations pass unchanged in meaning. `facts_report`, loaded as a pytest plugin from `candle`'s `conftest.py`, moves with it.
- **`wiki`**: the engine of `candle`'s `scripts/wiki` (pages, model, markdown, anchors, index, check). Its four `candle`-specific points (`grammar.py` and `check.py` rule 7 forcing `candle-legacy#N` issue references, `errors.py` inheriting `candle.errors.CandleError`, `archive.py` following a `candle-legacy` design) become configuration read from `.claude/project.toml`; the engine also resolves `<pack>:<slug>` citations and serves `search` and `show`.

- **The packs travel with the package.** The package build includes the rule files of `plugins/rules-*/`, from the same commit, so `check` resolves `<pack>:<slug>` and `wiki search` finds pack rules in CI and in a confined agent alike. The plugins and the package come from one repository but are pinned separately: agents may see a newer pack than the project's pinned package. Accepted, with its bound: a pack rule is never renamed or removed without keeping its old slug resolvable (a `superseded_by` entry), so a pinned package and a newer plugin never disagree on whether a citation exists.

The package is a direct dependency of each Python project, and so takes its trace under `candle`'s rule on vetting every direct dependency.

`qa_stack` and its stack stay the project's own, as its QA contract. Whether `scripts/qa/guard.py`'s command confinement is generic enough to join the package is left to the builder.

### Where sessions run

Claude Code sessions run from the owner's terminal; none runs in GitHub Actions yet (claude-code-action would need read access to this repository, a workspace trusted ahead of a `-p` run, and a check of how it loads a project's plugins).

**CI does run in GitHub Actions**, on GitHub-hosted runners, in seven of the nine repositories (`candle`, `candle-app`, `candle-legacy`, `candle-pseudo`, `candle-qa`, `capture`, `fhirforge`), and it calls the scripts the package replaces. Once a project's `uv.lock` holds a git dependency on this repository, every job's `uv sync --locked` must be able to fetch it from the first migration on. See *Open question*.

## Open question for the owner

**How CI reaches this repository.** Either the repository is public (nothing to configure; its content is skills, rules and tooling, no secrets), or it stays private and each migrated repository's CI gets read access (a deploy key or a fine-grained token stored as a secret, and a git credential step before `uv sync`).

## Left to the builder

- The exact wording and length of `base.md` and of the condensed `unslop`, within the anti-goal on always-on cost.
- The classification of each existing rule page into a pack, by the test above; a page that fits no pack stays in its project.
- The format of a rule file inside a pack, and whether the wiki front matter (`sources` pinned to a commit) survives the move.
- Plugin evals (`claude plugin eval`) for the skills whose triggering matters; `reading-the-wiki` first, since `/skill-doctor` shows it invoked 11 times against 33 for `updating-the-wiki`.
- The order in which the nine repositories migrate, and how each is checked after migration.

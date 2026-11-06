# claude-plugins: one source for the skills, agents and rules shared across projects

Date: 2026-11-06. Status: draft, awaiting the owner's approval.

## Why

The owner's Claude Code skills are copied by hand into each project. Nine repositories carry copies (`candle`, `candle-app`, `candle-legacy`, `candle-pseudo`, `candle-qa`, `capture`, `fhirforge`, `fouille`, `korps`), and the copies have drifted. Measured on 2026-11-06:

| Skill | Distinct versions |
|---|---|
| `updating-the-wiki` | 4 |
| `github-project-tracking`, `qa`, `reading-the-wiki` | 3 |
| `spec-to-facts` | 2 |
| `codebase-design`, `domain-modeling`, `unslop`, `writing-for-agents` | 1 |

The drift has three causes, and the design answers each:

1. **Repository facts written into a generic skill.** `updating-the-wiki` names its sibling repositories (`candle-legacy#N`, `aneuraz/candle#N`), the URL to read a foreign commit, and whether `scripts.wiki` exists.
2. **Language or project-type rules mixed into skills and `CLAUDE.md`.** `spec-to-facts` assumes pytest and `facts_check.py`; `CLAUDE.md` §4 carries ruff; `capture/SECURITY.md` and `fhirforge/SECURITY.md` state the same principles twice, once with Rust tooling, once with Python tooling.
3. **Improvements made in one copy and never carried over.** `spec-to-facts`' CI gate exists only in `candle`; `qa`'s `--keep` and its stack-error Monitor exist only in `candle-qa`, while `candle`'s copy has a tooling-change check that `candle-qa`'s lacks.

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
- **Writing.** The `unslop` skill, complete with its examples, for reviewing a long text. `humanizer` (user level) and `anthropic-skills:unslop` (synced from claude.ai) are retired: one source for that guidance.
- **Skills, moved as they are:** `writing-for-agents`, `codebase-design`, `domain-modeling`.
- **Skills, split:** `spec-to-facts` (the method; its pytest, report-plugin and `facts_check.py` parts go to `rules-python`), `reading-the-wiki` and `updating-the-wiki` (the procedure; see *Project-side facts* below).
- **QA.** A generic `qa` skill and `qa` agent: black-box testing of the current branch; oracles taken from the specs and fact-sets the diff touches; `scenarios.md` with one scenario per observable statement and a *Not observable* section; exploration of neighbouring paths including hostile input; each candidate replayed and marked `confirmed` or `intermittent`; a fixed report template; the agent confined by a guard. The project supplies a **QA contract**: a stack script exposing `up`, `down`, `status`, `guard`, and a page describing its test surfaces. The method merges the best of `candle`'s copy (the tooling-change check) and `candle-qa`'s (`--keep`, the stack-error Monitor).
- **Project tracking.** `github-project-tracking` until `plane-project-tracking` replaces it (non-goal above).
- **Independent reviews around superpowers.** The owner uses the superpowers skills and asks, on top of them, for an independent review at three moments: after a spec is written (the end of `superpowers:brainstorming`), after a plan is written (`superpowers:writing-plans`), and after all of a plan's tasks are done (the end of `superpowers:subagent-driven-development` or `superpowers:executing-plans`, before `superpowers:finishing-a-development-branch`). An independent review is a fresh agent handed the artefact (the spec, the plan, the branch's diff), never the author's conclusions. superpowers is not forked and no skill wraps it: two skills competing for the same trigger lose to superpowers' own start-of-session hook. Instead:
  - `base.md` states the three review points; superpowers itself ranks user instructions above its skills.
  - A `PostToolUse` hook on the `Skill` tool re-states the review step when one of those skills loads, if the hook input carries the skill's name (to verify first; without it, `base.md` alone carries the rule).

### Rule packs

Each pack is a plugin holding one skill whose reference files are the rules, one rule per file, each with its reason, as the wiki pages carry them today. Where it helps, the skill's `paths` frontmatter scopes automatic loading (`rules-python`: `**/*.py`, `pyproject.toml`, `uv.lock`).

The split follows one test: **a principle that holds in any language goes to `rules-security`; its realisation with a given toolchain goes to that language's pack.** Examples from `candle`'s 45 rule pages:

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

A project's `.claude/settings.json` declares the marketplace and enables the plugins that apply to it. That list **is** the declaration. Example for `candle`: `core`, `rules-security`, `rules-python`, `rules-typescript`, `rules-health-data`, `rules-untrusted-parsing`.

### What stays in each project

- **`CLAUDE.md`:** only what is the project's own (for `candle`: the version mechanism, the language rule and its French archives, the wiki's `doctrine-map`, the routing table to its own pages).
- **Its wiki:** its decisions, debts, defects, lessons, reference, how-tos and its own rules. Rule pages now held by a pack leave the wiki.
- **Project-side facts for the wiki skills:** one wiki page per repository states its sibling repositories, the form of an issue reference, where a foreign commit is read, and which wiki tooling exists. `reading-the-wiki` and `updating-the-wiki` read it first.
- **Its QA contract**, when it uses `qa`.

### Finding a rule

`reading-the-wiki` searches the project's wiki **and** the rule skills of the enabled packs before answering that no rule covers a question.

### Citing a rule that left the wiki

A rule held by a pack is cited `<pack>:<slug>` (for example `rules-security:parameterised-sql`), in markdown and in code alike, in place of `wiki:rules/<slug>` and of a relative link. `scripts.wiki check` learns to resolve that form against the packs. The numbering inherited from `docs/security-rules.md` ("3.6 — …") is dropped. Migrating a repository rewrites its citations (in `candle`: 30 wiki pages and 62 code comments).

### The `qa` agent's guard

The documentation is understood to make a plugin-shipped agent ignore the `hooks` of its frontmatter (to verify first). If so, the guard moves to a `PreToolUse` hook in `core`'s `hooks.json` that acts only when the calling agent is `core:qa`. If the hook input cannot tell which agent is calling, the `qa` agent file stays in each project that uses it, and only the skill and the method move. An unconfined `qa` agent is not an option.

### Repositories without a wiki

`candle-qa`, `capture`, `fhirforge`, `fouille` and `korps` are not given a wiki. Their project-side facts go in their `CLAUDE.md`; their `SECURITY.md` shrinks to the policy template, the rules coming from the packs they enable. Their French `suivi-github-project` skill stays until `plane-project-tracking` exists.

### `candle-legacy`

`candle-legacy` stays frozen and is not migrated: `candle`'s wiki pages cite commits of its history in their `sources`.

### Language

The plugins are written in English. Projects keep their own texts in their own language.

### The tooling package

A plugin does not reach CI, yet the skills and CI call the same scripts. This repository therefore also publishes one Python package, installed in each project by uv from git at a pinned commit, and called by CI and by the skills alike:

- **`facts`**: `facts_check` and `facts_report`, taken from `candle`, which already holds no `candle`-specific reference. Five other copies exist (`candle-app`, `candle-legacy`, `candle-pseudo`, `candle-qa`, `capture`), all different from `candle`'s; they are replaced.
- **`wiki`**: the engine of `candle`'s `scripts/wiki` (pages, model, markdown, anchors, index, check). Its four `candle`-specific points (`grammar.py` and `check.py` rule 7 forcing `candle-legacy#N` issue references, `errors.py` inheriting `candle.errors.CandleError`, `archive.py` following a `candle-legacy` design) become configuration read from the repository. That configuration file is the project-side facts the wiki skills read first; the engine also resolves `<pack>:<slug>` citations.

`qa_stack` and its stack stay the project's own, as its QA contract. Whether `scripts/qa/guard.py`'s command confinement is generic enough to join the package is left to the builder.

### Where sessions run

Sessions run from the owner's terminal. GitHub Actions are not used yet; when they are, a runner needs read access to this private repository through git, the workspace trusted ahead of a `-p` run, and a check of how claude-code-action loads a project's plugins. Because a session where the marketplace failed to load loses `base.md` and every pack without a word, `core`'s `SessionStart` hook reports any pack the project enables that did not load.

## Left to the builder

- The exact wording and length of `base.md` and of the condensed `unslop`, within the anti-goal on always-on cost.
- The classification of each existing rule page into a pack, by the test above; a page that fits no pack stays in its project.
- The format of a rule file inside a pack, and whether the wiki front matter (`sources` pinned to a commit) survives the move.
- Plugin evals (`claude plugin eval`) for the skills whose triggering matters; `reading-the-wiki` first, since `/skill-doctor` shows it invoked 11 times against 33 for `updating-the-wiki`.
- The order in which the nine repositories migrate, and how each is checked after migration.

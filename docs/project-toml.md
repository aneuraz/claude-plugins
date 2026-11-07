# `.claude/project.toml`

The only project-side facts file. A project that uses the plugins' skills puts the facts those skills
need in `.claude/project.toml`, at its repository root. Every section and every key is optional: a
missing file, section or key means "not configured", and a reader says so and never guesses a default.
An unknown section or key is an error, named in the message together with the file's path.

Skills cite this schema by its keys (`[wiki] path`, `[qa] up`), not by this file's path.

## Keys

| Section | Key | Type | Meaning |
|---|---|---|---|
| `[repository]` | `name` | string | `owner/repo` of this repository |
| | `siblings` | list of strings | `owner/repo` of the repositories it cites |
| | `issue_repository` | string | the repository a wiki issue reference must name; rule 7 rewrites `name`'s issue and pull URLs, `<name's repo>#N` and bare `#N` into it |
| | `issue_reference` | string | the prose form of a reference to `issue_repository`, with `{n}` |
| | `foreign_commit_url` | string | URL format of a file at a commit of a sibling, with `{repo}`, `{commit}`, `{path}` |
| `[tooling]` | `command` | string | how to run `cpt` here |
| `[wiki]` | `path` | string | the wiki's directory |
| | `tooling` | `"cpt"` or `"none"` | `none`: the index is kept by hand |
| | `archive_until` | date | files of dated documents up to this date are archived, optional |
| | `archive_named` | list of strings | files archived by name, optional |
| | `index_sections` | list of tables `{title, dir, glob, kind}` | the source sections of the wiki index; `kind` is optional: `"files"` (the default) lists each file by its name, `"headings"` by its first `# ` heading |
| `[facts]` | `check_forms` | list of strings | the forms a pytest check of a fact may take: the check's tokens, its `file::function` selectors removed, must equal one form's, where a `*` token stands for any one token. Absent: `cpt facts` audits no check's form (its selectors still are) |
| | `[facts.check_forms]` | table of lists of strings | the alternative to a flat `check_forms`, with one optional list per runner: `pytest` (the flat list's meaning), `vitest` and `playwright` (the by-id forms), `vitest-files`, `cargo`, `swift`. Any other key is an error. See below |
| | `orphans` | `"design-text"` or `"facts-lines"` | how `--orphans` traces a fact; see below. Default `"design-text"` |
| | `owner` | boolean | facts carry an `owner` field and `--owner <name>` keeps the facts of that owner. Default `false` |
| | `[facts.schema]` | table | the closed schema of a fact; see below |
| | `release_reports` | list of strings | the names (file stems) of the reports written by release-profile cargo jobs; see cargo below |
| `[tracking]` | `project` | string | the tracking Project's title |
| | `rule_page` | string | the project's tracking rule page, from the repository root |
| `[qa]` | `up`, `down`, `status`, `guard` | string | command lines |
| | `up_keep`, `down_respect_keep` | string | the `up` and `down` command lines when the run is kept, optional; `--keep` is honoured only when both are set |
| | `variables` | list of strings | environment variables the run needs, checked by name, never printed |
| | `surfaces` | list of tables `{name, command, description}` | the test surfaces handed to the agent |
| | `work_dir` | string | the run's work directory, where the agent writes and the report lands; required when `[qa]` is used |
| | `errors_dir` | string | directory of stack-error files for the Monitor, optional |
| | `tooling_paths` | list of strings | paths whose change by the branch stops the run to ask |

## Example

The values of `aneuraz/candle`. `candle` has no value for `up_keep`, `down_respect_keep` or
`errors_dir` (its QA stack has no kept run and no error directory), so they are omitted. Its
`check_forms` are its two check forms (with and without `-m integration`), each run from the workspace
(`--all-packages`) or from one member (`--package *`).

```toml
[repository]
name = "aneuraz/candle"
siblings = ["aneuraz/candle-legacy", "aneuraz/candle-app"]
issue_repository = "aneuraz/candle-legacy"
issue_reference = "candle-legacy#{n}"
foreign_commit_url = "https://github.com/{repo}/blob/{commit}/{path}"

[tooling]
command = "uv run cpt"

[wiki]
path = "docs/wiki"
tooling = "cpt"
archive_until = 2026-10-12
archive_named = ["tests/contracts/test_wiki.py", "tests/helpers/wiki.py"]

[[wiki.index_sections]]
title = "Architecture decisions"
dir = "docs/adr"
glob = "*.md"
kind = "headings"

[[wiki.index_sections]]
title = "Specs"
dir = "docs/superpowers/specs"
glob = "*-design.md"

[[wiki.index_sections]]
title = "Fact-sets"
dir = "docs/superpowers/specs"
glob = "*-facts.md"

[[wiki.index_sections]]
title = "Plans"
dir = "docs/superpowers/plans"
glob = "*.md"

[[wiki.index_sections]]
title = "Research"
dir = "docs/research"
glob = "*.md"

[facts]
check_forms = [
  "uv run --all-packages --exact pytest -v",
  "uv run --all-packages --exact pytest -m integration -v",
  "uv run --package * --exact pytest -v",
  "uv run --package * --exact pytest -m integration -v",
]

[tracking]
project = "candle"
rule_page = "docs/wiki/rules/project-tracking.md"

[qa]
up = "uv run python -m scripts.qa_stack up"
down = "uv run python -m scripts.qa_stack down"
status = "uv run python -m scripts.qa_stack status"
guard = "uv run --frozen --no-sync python -m scripts.qa_stack guard"
work_dir = ".qa/current/work"
variables = ["CANDLE_QA_CONFIG"]
tooling_paths = [
  "scripts/qa",
  "scripts/qa_stack.py",
  ".claude/agents/qa.md",
  ".claude/skills/qa",
  "deploy/terminal",
  "deploy/compose/proxy-entrypoint.sh",
  "deploy/compose/deid-entrypoint.sh",
  "deploy/compose/deid.compose.toml",
  "deploy/seed.py",
  "deploy/compose/identities.py",
  "deploy/compose/init.py",
]

[[qa.surfaces]]
name = "cli"
command = "uv run python -m scripts.qa_stack cli <candle command>"
description = "candle as the agent identity"

[[qa.surfaces]]
name = "agent"
command = "uv run python -m scripts.qa_stack agent '<question>'"
description = "candle agent, one question per call"
```

## Per-runner check forms

`check_forms` is either the flat list above or the sub-table `[facts.check_forms]`, never both (TOML
allows one). In the sub-table, each key lists the command lines a check of that runner may take, and a
fact's check must equal one of them token for token, where `*` stands for any one token. The by-id
forms of `vitest` and `playwright` also use `<file>` (the test file, relative to the repository root)
and `<id>` (the id of the fact, which must be the fact's own):

```toml
[facts.check_forms]
vitest = ['pnpm exec vitest run <file> -t "<id>"']
playwright = ['pnpm exec playwright test <file> -g "<id>"']
```

A fact with such a check is green when, in the reports, at least one entry of `<file>` has an own title
starting with `"<id> "` and every such entry passed (the `-t`/`-g` pattern itself is not evaluated). The
audit, in every mode, requires the file to exist and hold a test whose title starts with the id.

### Whole-file vitest

```toml
[facts.check_forms]
vitest-files = ['npm --prefix app test -- <files>']
```

The form is the project's own command, as a developer types it, with `<files>` standing for one or
more test files or directories. A check is that command's tokens, the files, and optionally
`-t "<regex>"` (or `--testNamePattern`); anything else is a fault, and so is a check that names no
file (`npm --prefix app test -- -t "carries no excerpt"`). The files are relative to the directory the
command prefix names (`--prefix`, `-C`, `--dir` or `--cwd`; the repository root without one), and a
report entry's `file` is relative to the repository, so `src/App.test.ts` under `--prefix app` selects
the entries of `app/src/App.test.ts` (convert vitest's report with `--root app`). A directory selects
the entries beneath it. The audit, in every mode, requires each file or directory to exist and the
pattern to be a regular expression.

`-t` is a regular expression searched in the entry's full name: its ancestor titles and its title
joined by single spaces, the file's name not included (`Palette opens on key` for `it("opens on key")`
in `describe("Palette")`). That is vitest's own definition: `getTaskFullName` in `@vitest/runner` builds
the name and `interpretTaskModes` skips a test whose full name does not match the pattern. Python's
regular expressions stand in for JavaScript's; keep to the syntax they share. The fact is green when
the check selects at least one entry and every selected entry passed. The number of tests is not
counted.

### `&&`

A check may join parts with `&&` (outside quotes), for every runner. Each part is audited and judged
on its own: the fact is green when every part selects at least one entry and every selected entry
passed. Local mode runs the parts one after the other, without a shell, and stops at the first failure.

### cargo

```toml
[facts]
release_reports = ["rust-release"]

[facts.check_forms]
cargo = [
  "cargo test -p * --test *",
  "cargo test -p * --test * --release",
  "cargo test -p * --lib",
  "cargo test -p * --lib --release",
]
```

A cargo check is `cargo test -p <pkg> (--test <bin> | --lib) [--release] [-- <filter> ...]` and nothing
else: `--exact`, `--ignored`, `--nocapture`, `--features` and any other flag are refused. The declared
forms are matched on the check with its filters removed and its flags in the order shown (so
`--release --test x` fits `--test * --release`); without a `cargo` form only that grammar is audited.
The reports are nextest's (`cpt facts report nextest`): an entry belongs to `<pkg>::<bin>`, or to
`<pkg>` for `--lib`. With filters, each filter must select at least one entry (it is a substring of the
test path, as libtest without `--exact`) and every selected entry must have passed; without, every
entry of the binary is selected, and there must be one.

`release_reports` lists the **names of the reports** (the file's stem, which is the job name, without
`.json`) written by release-profile jobs. A `--release` check reads only those; any other cargo check
reads only the others. A `--release` check with no release report is `not run`. When any report is read, a name listed here with no report file fails the gate (`release report not found: <name>`), whatever the checks: a misspelt artifact or a cancelled release job is never silent.

The static audit, in every mode including `--orphans`: `<pkg>` is a workspace member (the manifest
directories come from `cargo metadata`, which runs once, only when a cargo check exists, offline);
`tests/<bin>.rs` (or `tests/<bin>/main.rs`) exists in it, or for `--lib` its `src/` holds `.rs` files;
and each filter's literal appears in that file (in `src/` for `--lib`). A filter containing `::` is
checked by its last non-empty segment.

### swift

```toml
[facts.check_forms]
swift = ["swift test --package-path agent --filter *"]
```

A swift check is audited for its form only (it must equal a declared `swift` form token for token;
without one it is a fault) and is never judged by `--reports`: there is no Swift report, so a fact made
only of swift parts prints `not gated (swift)` and counts neither green nor red. In a `&&` conjunction
the other parts are still judged. Locally, `--runner swift` runs it by exit code.

## Tracing facts to specs: `orphans`

`orphans = "design-text"` (the default) calls a fact orphaned when its id does not appear in its
sibling `*-design.md` (a range `X-001 à X-005` or `X-001 to X-005` stands for each id in it).

`orphans = "facts-lines"` traces by the `*Facts :*` lines of every spec in `docs/superpowers/specs/`
(the `*-facts.md` files excepted). A line is any line holding `*Facts :*` (so `**Facts :**` too); the
ids on it count wherever the prose puts them. An id may carry a letter suffix (`OCR-007a`), its prefix
may contain digits (`I18N-004`), and `X-001 à X-007` or `X-001 to X-007` is a range. A fact no line
cites is an orphan, and an id a line cites that no fact defines is **dangling**; both fail the gate.

## Owner

With `owner = true`, `cpt facts --owner <name>` judges only the facts whose `owner` field is `<name>`.
Without it, `--owner` is an error (exit 2), and so is an owner no fact carries (named in the message).

## Schema

```toml
[facts.schema]
allowed = ["id", "status", "level", "statement", "check", "source", "owner", "blocker", "timeout"]
required = ["id", "status", "level", "statement", "source", "owner"]
statuses = ["@draft", "@spec", "@implemented"]
```

Each list is optional and closes one aspect of a fact: `allowed` the fields (any other is a fault),
`required` the fields every fact has, `statuses` the values of `status`. Whatever the lists, an
`@implemented` fact without a `check` and a repeated id (across all fact-sets) are faults. A field the
schema allows is not necessarily read: `capture`'s `timeout` is allowed and ignored, since the gate
runs nothing. Without `[facts.schema]` the fact-sets are not audited. Schema faults, like dangling ids, concern the whole fact-set: `--only` and `--owner` do not narrow them.

## Options of `cpt facts`

| Option | Meaning |
|---|---|
| `--reports DIR` | the gate: judge each fact from the reports under DIR, run nothing |
| `--orphans` | traceability and the static audits only |
| `--implemented` | judge only `@implemented` facts; the others are listed as `- pending: <id> [<status>]`, except `@superseded` facts (they bind through their successors) |
| `--only ID` | judge only that fact; repeatable; an unknown id is an error (exit 2) naming it |
| `--owner NAME` | judge only the facts of that owner (`owner = true`) |
| `--exclude-requires a,b` | a fact whose `requires` names a listed resource prints `not run (requires: …)` and is not red, in reports and in local mode; given, each fact's `-m` markers must equal its `requires` |
| `--runner LIST` | local mode only: the runners to execute (`pytest`, `vitest`, `cargo`; `playwright` when named) |
| `--root DIR`, `--vitest-root DIR` | the project root; where legacy `pnpm -C agent exec` selectors resolve |

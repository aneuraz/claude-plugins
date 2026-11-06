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

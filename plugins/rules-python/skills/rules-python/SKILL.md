---
name: rules-python
description: 'Python rules: pinned stable Python, uv and uv.lock, pip-audit, ruff and noqa discipline, typing, naming and exception rules, no eval/exec/pickle/unsafe YAML, defusedxml, the hatch-vcs version, and the pytest side of spec-to-facts. Cited as rules-python:<slug>. Read a rule file when a skill or the base rules cite it, or before writing Python or changing its dependencies.'
paths:
- '**/*.py'
- pyproject.toml
- uv.lock
---

# Python rules

Rule files sit in `rules/`, one per file. Cite one as `rules-python:<slug>`.

## Rules

- `eval`, `exec`, `pickle`/`shelve` on external data, and non-safe `yaml.load` ARE FORBIDDEN — `rules-python:no-eval-exec-pickle-or-unsafe-yaml`
- All incoming XML MUST be parsed with `defusedxml` — `rules-python:parse-xml-with-defusedxml`
- Development MUST use a stable version of Python, pinned in `.python-version`, which is versioned — `rules-python:pinned-stable-python`
- `pip-audit` MUST run in CI on every PR and on a daily cron — `rules-python:pip-audit-on-every-pr-and-daily`
- Python rules — `rules-python:python-rules`
- A ruff warning gets fixed, not ignored — `rules-python:ruff-and-noqa-discipline`
- `uv.lock` MUST be versioned and authoritative — `rules-python:uv-lock-is-authoritative`
- The project version is never written by hand — `rules-python:version-never-written-by-hand`

## The pytest side of spec-to-facts

- pytest check selector — `rules-python:pytest-check-selector`
- facts report plugin — `rules-python:facts-report-plugin`
- CI facts gate — `rules-python:ci-facts-gate`
- Hypothesis property tests — `rules-python:hypothesis-property-tests`
- icontract runtime contracts — `rules-python:icontract-contracts`
- Pydantic model invariants — `rules-python:pydantic-model-invariants`

#!/usr/bin/env bash
# Builds the fixture project in the case's working directory (the eval runs this
# with the workspace as cwd). The repository's root is resolved from this
# script's own location, so no absolute path is written into the repository.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"

mkdir -p .claude docs/wiki/lessons
cat > .claude/project.toml <<TOML
[tooling]
command = ".venv/bin/cpt"

[wiki]
path = "docs/wiki"
tooling = "cpt"
TOML

cat > docs/wiki/index.md <<'MD'
# Wiki

## Lessons

- [Pin the CSV reader's delimiter](lessons/pin-the-csv-delimiter.md)
- [Log rotation keeps seven days](lessons/log-rotation-keeps-seven-days.md)
MD

cat > docs/wiki/lessons/pin-the-csv-delimiter.md <<'MD'
---
title: Pin the CSV reader's delimiter
sources:
- https://example.org/fixture/csv
---

# Pin the CSV reader's delimiter

The importer reads exports with `;` as the delimiter. Pass it explicitly.
MD

cat > docs/wiki/lessons/log-rotation-keeps-seven-days.md <<'MD'
---
title: Log rotation keeps seven days
sources:
- https://example.org/fixture/logs
---

# Log rotation keeps seven days

The service rotates its logs daily and keeps seven files.
MD

# The sandboxed agent can neither build the repository nor reach the operator's uv
# cache and Python installs, so cpt is installed into a project-local venv here.
uv venv --quiet --python 3.14 .venv
uv pip install --quiet --python .venv/bin/python "$REPO"

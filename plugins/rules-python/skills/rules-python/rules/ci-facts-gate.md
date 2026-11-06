---
title: CI facts gate
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# CI facts gate

GitHub Actions wiring for the facts gate: each test job gets the report option through the environment and an upload step; one job downloads every report and runs the gate with the project's `cpt` command (`facts --reports reports`). The report writer is `rules-python:facts-report-plugin`.

```yaml
  tests:
    steps:
      - run: pytest
        env:
          PYTEST_ADDOPTS: --facts-report=reports/tests.json
      - uses: actions/upload-artifact@<pinned digest>
        if: ${{ !cancelled() }}
        with:
          name: facts-report-tests
          path: reports/
          overwrite: true
          retention-days: 3
          if-no-files-found: error

  facts:
    needs: [tests]
    if: ${{ !cancelled() }}   # a red suite also names the facts it turns red
    steps:
      - uses: actions/download-artifact@<pinned digest>
        with:
          pattern: facts-report-*
          path: reports
      - run: <the project's cpt command> facts --reports reports
```

- Pin both actions to a commit digest.
- `download-artifact` puts each artifact in its own subdirectory; the gate reads the directory recursively.
- The gate reads every test job. A job that did not run leaves no report, and its facts read `not run`.
- Make the `facts` job a required status check, so a red or orphan fact blocks the merge.

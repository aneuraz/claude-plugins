---
title: pytest check selector
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/SKILL.md
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# pytest check selector

A fact's `check` names its test as `<file>::<function>`, or `<file>::<function>[<case>]` for one case of a parametrised test. This is pytest's own node id. The CI gate looks that name up in the test jobs' reports and runs no command.

```yaml
check: "pytest tests/contracts/test_auth.py::test_expired_jwt_returns_401 -v"
```

Give every check one fixed form: the runner, its environment flags, the selector, `-v`. The gate refuses any other token. A flag outside the form (`-k`, `-p`, a shell operator) would make the command differ from what the reports prove.

A bare selector (no `[<case>]`) stands for the test and each of its parametrised cases; the fact is green only when all of them passed.

## Level 1 test template

```python
def test_expired_jwt_returns_401(client, expired_token):
    r = client.post("/auth/refresh", headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401
    assert r.json()["code"] == "TOKEN_EXPIRED"
```

---
title: pytest check selector
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/SKILL.md
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# pytest check selector

A fact's `check` names its test as `<file>::<function>`, or `<file>::<function>[<case>]` for one case of a parametrised test. This is pytest's own node id. The CI gate looks that name up in the test jobs' reports and runs no command.

Give every check one of the project's fixed forms: the runner, its environment flags, the selector, `-v`. The forms are listed in `[facts] check_forms` of `.claude/project.toml`, each a check with its selectors removed (`*` stands for any one token), and the gate refuses a pytest check that takes none of them. A flag outside the form (`-k`, `-p`, a shell operator) would make the command differ from what the reports prove. Without `[facts] check_forms`, no form is audited: configure it.

```toml
[facts]
check_forms = ["uv run --exact pytest -v"]
```

```yaml
check: "uv run --exact pytest tests/contracts/test_auth.py::test_expired_jwt_returns_401 -v"
```

A bare selector (no `[<case>]`) stands for the test and each of its parametrised cases; the fact is green only when all of them passed.

## Level 1 test template

```python
def test_expired_jwt_returns_401(client, expired_token):
    r = client.post("/auth/refresh", headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401
    assert r.json()["code"] == "TOKEN_EXPIRED"
```

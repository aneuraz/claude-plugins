---
title: icontract runtime contracts
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# icontract runtime contracts

A level 3 fact stated as pre/post conditions on a function is a runtime Design by Contract, with icontract.

```python
import icontract

@icontract.require(lambda patient: patient.consent.is_active)
@icontract.ensure(lambda result: not contains_direct_identifiers(result))
def export_bundle(patient: Patient) -> Bundle: ...
```

The decorators enforce the contract on every call; the fact still needs a test that calls the function with a violating input and asserts the violation, so that `check` names a test.

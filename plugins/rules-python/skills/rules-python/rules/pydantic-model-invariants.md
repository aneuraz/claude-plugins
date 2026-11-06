---
title: Pydantic model invariants
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# Pydantic model invariants

A level 3 fact about a data schema (a field unique, non-null, bounded, or related to another field) is a validator on the model. Put the fact id in the failure message so a violation traces back to the fact.

```python
class ExportManifest(BaseModel):
    resources_in: int
    resources_out: int

    @model_validator(mode="after")
    def enrichment_never_drops(self):
        assert self.resources_out >= self.resources_in, "FACT DATA-003 violated"
        return self
```

The fact's `check` names a test that builds a violating instance and expects the validation error.

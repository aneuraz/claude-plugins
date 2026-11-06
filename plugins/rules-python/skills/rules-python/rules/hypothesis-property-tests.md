---
title: Hypothesis property tests
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# Hypothesis property tests

A level 2 fact (a predicate over a whole input domain) is a Hypothesis test.

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers(), unique=True).map(sorted), st.integers())
def test_binary_search_correct(xs, target):
    idx = binary_search(xs, target)
    assert (idx == -1 and target not in xs) or xs[idx] == target
```

For a non-deterministic pipeline, assert a structural invariant, never text equality:

```python
@given(clinical_note_strategy())
def test_pipeline_output_is_valid_fhir(note):
    bundle = pipeline.run(note)
    outcome = fhir_validator.validate(bundle, profile="http://hl7.org/fhir/R4")
    assert outcome.is_valid, outcome.issues
```

The fact's `check` names the test function like any other (`rules-python:pytest-check-selector`).

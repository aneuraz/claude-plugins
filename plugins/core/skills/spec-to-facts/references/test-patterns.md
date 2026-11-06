# What to write by fact level

The test itself is language-specific; the level decides its shape. Templates per language live in the rule packs, cited here.

## Level 1: Test (input/output example)

One precise input, one precise output, one test function. Name the fact id in the test name or its docstring so the trace runs both ways.

- Python / pytest: `rules-python:pytest-check-selector`
- TypeScript / Jest: `rules-typescript:jest-example-tests`

## Level 2: Property (property-based testing)

A predicate over a whole input domain, with a generator for the domain. For a non-deterministic pipeline (NLP, LLM) assert a structural invariant or a bound, never text equality.

- Python / Hypothesis: `rules-python:hypothesis-property-tests`
- TypeScript / fast-check: `rules-typescript:fast-check-property-tests`

## Level 3: Contract

- Runtime Design by Contract (Python / icontract): `rules-python:icontract-contracts`
- Data-model invariant (Python / Pydantic): `rules-python:pydantic-model-invariants`
- Consumer-driven cross-service contract (Pact), below. This one is cross-language: the consumer states what it needs from the provider, and the provider verifies it.

```python
pact.given("a patient with active consent") \
    .upon_receiving("an export request") \
    .with_request("GET", "/api/v1/export/123") \
    .will_respond_with(200, body=Like({"resourceType": "Bundle", "type": "collection"}))
```

## Conversion cheat sheet

| Prose formulation | Conversion |
|---|---|
| "returns X when Y" | test (example) |
| "for all / always / never" | property |
| "before the call… / after the call…" | pre/post contract |
| "field Z is unique / non-null / bounded" | data-model invariant |
| "service A guarantees B…" | Pact contract |
| "fast / intuitive / robust" | not testable → `@draft` + `blocker:` |

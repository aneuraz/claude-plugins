---
title: Python rules
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/python-rules.md
---

# Python rules

Based on PEP 8 and modern typing conventions. When in doubt, the source (PEP, official docs) wins over improvisation.

These rules only record what a competent Python writer would not already do by default. Rules that protect a security guarantee live in `rules-security`, which carries their justification.

## Internal API design

1. **No `get_` prefix for a plain access.** Use a property or the attribute itself. The prefix is reserved for what computes or fetches.

2. **Strict types everywhere.** Every public function is fully annotated, checked by the type checker in CI. No `Any` on a module boundary: if the type is unknown, the boundary is badly defined.

3. **NewType or dedicated classes for semantic distinctions**: `JobId`, `CorrelationId`, `UserId` rather than bare `str`. Two identifiers of different kinds must not be silently interchangeable.

4. **Arguments carry their meaning**: `parse(mode=ParseMode.STRICT)`, not `parse(True)`. A positional boolean is forbidden; enums (`StrEnum`) replace magic strings.

5. **Immutable models between pipeline steps** (`model_config = ConfigDict(frozen=True)` in Pydantic, `@dataclass(frozen=True)` otherwise): a step never mutates another step's input.

6. **Typed exceptions that carry meaning**: a project-specific hierarchy rooted in a single base exception (`<Project>Error` → `StepError`, `ConfigError`…). Never `raise Exception(...)`, never a silent `except Exception`. Every broad `except` is followed by a structured log and either a re-raise or a conversion to an opaque error.

7. **Dependencies between modules go one way**, the way of the pipeline or of the layers. A core module never imports an edge module. No circular imports and no imports inside functions, unless the import cost is documented. When the project has layers, they are a contract (`[tool.importlinter]` in `pyproject.toml`, run by `lint-imports` in CI); the project's own page lists them.

## What security requires of Python code

These three rules have their full justification in `rules-security`. They are repeated here because writing Python is when they get broken.

- **Validation at the edge, validated types inside**: `rules-security:validate-once-at-the-edge`.
- **`__repr__` never leaks sensitive data**: `rules-security:no-default-repr-for-sensitive-types`. Never a dataclass or a `BaseModel` with the default repr on a type that carries identifying data.
- **No raw exception on a path reachable from the network**: `rules-security:no-raw-exception-escapes-the-network`.

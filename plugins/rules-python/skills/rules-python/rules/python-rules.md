---
title: Python rules
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/python-rules.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/validate-once-at-the-edge.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/input-schemas-refuse-unknown-fields.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-raw-exception-escapes-the-network.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-default-repr-for-sensitive-types.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#4-no-leakage-of-sensitive-data
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/secrets-through-dedicated-types.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/constant-time-secret-comparison.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-home-made-cryptography.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/tls-on-every-transport.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/subprocess-without-a-shell.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/never-write-a-version-from-memory.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/resolve-a-library-then-read.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/deal-with-outdated-dependencies.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/sbom-at-each-release.md
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/runtime-defined-by-the-repository.md
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

Each rule below is a principle of `rules-security`, which carries its justification; the line is its Python realisation. It is repeated here because writing Python is when it gets broken.

- `validate-once-at-the-edge` (`rules-security:validate-once-at-the-edge`): the input models validate; the core handles `NewType`s and frozen models and does not validate again.
- `input-schemas-refuse-unknown-fields` (`rules-security:input-schemas-refuse-unknown-fields`): `model_config = ConfigDict(extra="forbid")` in Pydantic.
- `no-raw-exception-escapes-the-network` (`rules-security:no-raw-exception-escapes-the-network`): no `assert` for validation (removed under `-O`); indexed access on incoming data goes through `.get()` or an explicit check.
- `no-default-repr-for-sensitive-types` (`rules-security:no-default-repr-for-sensitive-types`): a common base whose `__repr__`/`__str__` redact the fields concerned; no `print()` and no f-string of a domain object in shipped code. Never a dataclass or a `BaseModel` with the default repr on a type that carries identifying data: a default repr combined with a `logger.error("%s", job)` in a rare error path exports the record into the logs.
- `secrets-through-dedicated-types` (`rules-security:secrets-through-dedicated-types`): `pydantic.SecretStr` for config; it neutralises accidental display.
- `constant-time-secret-comparison` (`rules-security:constant-time-secret-comparison`): `secrets.compare_digest`; randomness for security from the `secrets` module, never `random`.
- `no-home-made-cryptography` (`rules-security:no-home-made-cryptography`): `cryptography`, and `hashlib` for digests.
- `tls-on-every-transport` (`rules-security:tls-on-every-transport`): no `verify=False`, ever: a debugging `verify=False` that reaches production cancels the trust perimeter.
- `subprocess-without-a-shell` (`rules-security:subprocess-without-a-shell`): `subprocess.run([...], shell=False)` with a timeout: `shell=True` on a file name supplied by a third party is command injection.
- `never-write-a-version-from-memory` (`rules-security:never-write-a-version-from-memory`): `uv add <package>` (and `uv add "<package>[extra]"`) resolves the latest compatible version and updates the lock.
- `resolve-a-library-then-read` (`rules-security:resolve-a-library-then-read`): `uv pip show <package>` for the resolved version, then the documentation for that version.
- `deal-with-outdated-dependencies` (`rules-security:deal-with-outdated-dependencies`): `uv lock --upgrade --dry-run` or `uv tree --outdated`.
- `sbom-at-each-release` (`rules-security:sbom-at-each-release`): `cyclonedx-py` or equivalent, from `uv.lock`.
- `runtime-defined-by-the-repository` (`rules-security:runtime-defined-by-the-repository`): no `PYTHONPATH`, no modified `sys.path`; everything goes through `uv run` and entry points.

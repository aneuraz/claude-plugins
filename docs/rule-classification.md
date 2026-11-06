# Rule classification

Where each rule page of `candle`'s `docs/wiki/rules/` (at `275bce0`) goes, by the spec's two tests: a principle that holds in any language goes to `rules-security`, its realisation with one toolchain to that language's pack; the principle goes to a pack and the project's own application stays in the project's wiki. `split` is `yes` when the principle goes to the pack and the application stays as a page of the project's own, citing the pack rule.

| source | target | split | note |
|---|---|---|---|
| candle:access-logs-unmodifiable-by-producer | rules-health-data:access-logs-unmodifiable-by-producer | | |
| candle:authorise-at-the-data-not-the-route | rules-security:authorise-at-the-data-not-the-route | | |
| candle:bounded-decompression | rules-untrusted-parsing:bounded-decompression | | |
| candle:bounded-image-rendering | rules-untrusted-parsing:bounded-image-rendering | | `Image.MAX_IMAGE_PIXELS` (Pillow) kept as the example; the bound itself holds for any renderer. |
| candle:ci-gates | rules-security:ci-gates | yes | The principle (CI authoritative, the minimum gates, the mechanical no-leak test) goes to the pack. The project's job names, its facts-gate wiring (the method is `core`'s `spec-to-facts`, the pytest wiring `rules-python:ci-facts-gate`) and its debt on warning filters stay. |
| candle:constant-time-secret-comparison | rules-security:constant-time-secret-comparison | | Principle in any language; `secrets.compare_digest` kept as the Python example. |
| candle:data-classification | rules-health-data:data-classification | yes | The method, the generic rows and the three consequences go to the pack. The project's own rows (its caches, chat data, agent store, log streams, model call) and their links into its debts, references and decisions stay. The ANSSI pillar map goes to `rules-security`'s skeleton. |
| candle:deal-with-outdated-dependencies | rules-security:deal-with-outdated-dependencies | | Principle in any language; the `uv` commands kept as the Python example. |
| candle:documentation-chain | stays | | The project's own process: its three document paths, `facts_check.py`'s check forms and runners. The generic method is `core`'s `spec-to-facts`; the pytest selector is `rules-python:pytest-check-selector`. Its milestone-review and documentation-task sections are workflow, not a language or data rule, so no pack takes them. |
| candle:encrypt-at-rest-and-in-transit | rules-security:encrypt-at-rest-and-in-transit | yes | "Applied to candle-agent" (R2-13, R6-2b, R6-16, `SSLKEYLOGFILE`, the store's encrypted volume) stays as the project's page. |
| candle:every-request-authenticated | rules-security:every-request-authenticated | | "a decision page in the wiki" generalised to a recorded decision. |
| candle:explicit-service-bounds | rules-security:explicit-service-bounds | | |
| candle:file-type-from-magic-bytes | rules-untrusted-parsing:file-type-from-magic-bytes | | |
| candle:input-schemas-refuse-unknown-fields | rules-security:input-schemas-refuse-unknown-fields | | Principle in any language; Pydantic's `extra="forbid"` kept as the example. |
| candle:log-every-sensitive-access | rules-health-data:log-every-sensitive-access | | |
| candle:losing-a-backend-keeps-the-service-up | rules-security:losing-a-backend-keeps-the-service-up | | |
| candle:never-write-a-version-from-memory | rules-security:never-write-a-version-from-memory | | Principle in any language; `uv add` kept as the Python example (`pnpm add` in `rules-typescript:typescript-rules`). |
| candle:no-default-repr-for-sensitive-types | rules-security:no-default-repr-for-sensitive-types | | Principle in any language; `__repr__`/`__str__` kept as the Python example. |
| candle:no-eval-exec-pickle-or-unsafe-yaml | rules-python:no-eval-exec-pickle-or-unsafe-yaml | | |
| candle:no-home-made-cryptography | rules-security:no-home-made-cryptography | | The named libraries (`cryptography`, `hashlib`) kept as the Python example. |
| candle:no-identifier-or-content-in-logs | rules-health-data:no-identifier-or-content-in-logs | | |
| candle:no-raw-exception-escapes-the-network | rules-security:no-raw-exception-escapes-the-network | | |
| candle:no-real-data-in-test-datasets | rules-health-data:no-real-data-in-test-datasets | | |
| candle:only-configured-outgoing-endpoints | rules-security:only-configured-outgoing-endpoints | | |
| candle:opaque-error-responses | rules-security:opaque-error-responses | | |
| candle:parameterised-sql | rules-security:parameterised-sql | | |
| candle:parse-xml-with-defusedxml | rules-python:parse-xml-with-defusedxml | | |
| candle:pinned-stable-python | rules-python:pinned-stable-python | | |
| candle:pip-audit-on-every-pr-and-daily | rules-python:pip-audit-on-every-pr-and-daily | | The link to the project's defect page is dropped; its lesson (audit the lock, not an environment) stays in the rule as one sentence. |
| candle:project-tracking | stays | | The project's own tracking judgement (its shared Project, its repositories, its CI's draft behaviour). The mechanics are `core`'s `github-project-tracking`; nothing here is a language or data rule. |
| candle:purge-checked-by-a-test | rules-health-data:purge-checked-by-a-test | | |
| candle:python-rules | rules-python:python-rules | yes | Internal API design and the generic part of the import-direction rule go to the pack; the project's layer contract (`cli`, `proxy`, `engine`, the entry-point group, the namespace and the three look-alike names) and its language section stay. |
| candle:resolve-a-library-then-read | rules-security:resolve-a-library-then-read | | Principle in any language; `uv pip show` kept as the Python example. |
| candle:restart-safely | rules-security:restart-safely | | |
| candle:runtime-defined-by-the-repository | rules-security:runtime-defined-by-the-repository | | Principle in any language; `PYTHONPATH`/`sys.path`/`uv run` kept as the Python example. |
| candle:sbom-at-each-release | rules-security:sbom-at-each-release | | |
| candle:secrets-through-dedicated-types | rules-security:secrets-through-dedicated-types | | Principle in any language; `pydantic.SecretStr` kept as the Python example. |
| candle:submitted-content-is-data | rules-security:submitted-content-is-data | | |
| candle:subprocess-without-a-shell | rules-security:subprocess-without-a-shell | | Command injection holds in any language; `subprocess.run([...], shell=False)` kept as the Python example. |
| candle:tls-on-every-transport | rules-security:tls-on-every-transport | | |
| candle:typescript-rules | rules-typescript:typescript-rules | yes | Biome discipline, `pnpm add`, what Biome rejects and the plan code-block rule go to the pack; the `agent/` scope, the clinical agent's instructions and the CI jobs' facts runners stay. |
| candle:uv-lock-is-authoritative | rules-python:uv-lock-is-authoritative | | |
| candle:validate-once-at-the-edge | rules-security:validate-once-at-the-edge | | |
| candle:version-never-written-by-hand | rules-python:version-never-written-by-hand | yes | The principle and the `hatch-vcs` mechanism (`dynamic = ["version"]`, the tag as the only source) go to the pack; the project's `tooling/version_hook.py`, its sibling pinning, its static-dependencies lesson and the `uv build --wheel` note stay. |
| candle:vet-and-trace-every-direct-dependency | rules-security:vet-and-trace-every-direct-dependency | | |
| candle:CLAUDE.md#4-completion-gate | rules-python:ruff-and-noqa-discipline | | Not a wiki page: `CLAUDE.md` §4's ruff paragraph; the rest of §4 is `core`'s `base.md`. |

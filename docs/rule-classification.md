# Rule classification

Where each rule page of `candle`'s `docs/wiki/rules/` (at `275bce0`) goes, by the spec's two tests: a principle that holds in any language goes to `rules-security`, its realisation with one toolchain to that language's pack; the principle goes to a pack and the project's own application stays in the project's wiki. `split` is `yes` when the principle goes to the pack and the application stays as a page of the project's own, citing the pack rule.

| source | target | split | note |
|---|---|---|---|
| candle:access-logs-unmodifiable-by-producer | rules-health-data:access-logs-unmodifiable-by-producer | | |
| candle:authorise-at-the-data-not-the-route | rules-security:authorise-at-the-data-not-the-route | | |
| candle:bounded-decompression | rules-untrusted-parsing:bounded-decompression | | |
| candle:bounded-image-rendering | rules-untrusted-parsing:bounded-image-rendering | | `Image.MAX_IMAGE_PIXELS` (Pillow) kept as the example; the bound itself holds for any renderer. |
| candle:ci-gates | rules-security:ci-gates | yes | The principle (CI authoritative, the minimum gates, the mechanical no-leak test) goes to the pack. The project's job names, its facts-gate wiring (the method is `core`'s `spec-to-facts`, the pytest wiring `rules-python:ci-facts-gate`) and its debt on warning filters stay. |
| candle:constant-time-secret-comparison | rules-security:constant-time-secret-comparison | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:data-classification | rules-health-data:data-classification | yes | The method, the generic rows and the three consequences go to the pack. The project's own rows (its caches, chat data, agent store, log streams, model call) and their links into its debts, references and decisions stay. The ANSSI pillar map goes to `rules-security`'s skeleton. |
| candle:deal-with-outdated-dependencies | rules-security:deal-with-outdated-dependencies | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:documentation-chain | core:spec-to-facts | yes | The generic halves go to `core`'s `spec-to-facts` (Step 5): the milestone's consistency review before the PR leaves draft, the closing documentation task, and "what git does not track does not exist". The project's own process: its three document paths, `facts_check.py`'s check forms and runners. The generic method is `core`'s `spec-to-facts`; the pytest selector is `rules-python:pytest-check-selector`. Those sections are workflow, not a language or data rule, so `core` takes them, not a rules pack. |
| candle:encrypt-at-rest-and-in-transit | rules-security:encrypt-at-rest-and-in-transit | yes | "Applied to candle-agent" (R2-13, R6-2b, R6-16, `SSLKEYLOGFILE`, the store's encrypted volume) stays as the project's page. |
| candle:every-request-authenticated | rules-security:every-request-authenticated | | "a decision page in the wiki" generalised to a recorded decision. |
| candle:explicit-service-bounds | rules-security:explicit-service-bounds | | |
| candle:file-type-from-magic-bytes | rules-untrusted-parsing:file-type-from-magic-bytes | | |
| candle:input-schemas-refuse-unknown-fields | rules-security:input-schemas-refuse-unknown-fields | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:log-every-sensitive-access | rules-health-data:log-every-sensitive-access | | |
| candle:losing-a-backend-keeps-the-service-up | rules-security:losing-a-backend-keeps-the-service-up | | |
| candle:never-write-a-version-from-memory | rules-security:never-write-a-version-from-memory | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. The TypeScript one (`pnpm add`) is in `rules-typescript:typescript-rules`. |
| candle:no-default-repr-for-sensitive-types | rules-security:no-default-repr-for-sensitive-types | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:no-eval-exec-pickle-or-unsafe-yaml | rules-python:no-eval-exec-pickle-or-unsafe-yaml | | |
| candle:no-home-made-cryptography | rules-security:no-home-made-cryptography | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:no-identifier-or-content-in-logs | rules-health-data:no-identifier-or-content-in-logs | | |
| candle:no-raw-exception-escapes-the-network | rules-security:no-raw-exception-escapes-the-network | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:no-real-data-in-test-datasets | rules-health-data:no-real-data-in-test-datasets | | |
| candle:only-configured-outgoing-endpoints | rules-security:only-configured-outgoing-endpoints | | |
| candle:opaque-error-responses | rules-security:opaque-error-responses | | |
| candle:parameterised-sql | rules-security:parameterised-sql | | |
| candle:parse-xml-with-defusedxml | rules-python:parse-xml-with-defusedxml | | |
| candle:pinned-stable-python | rules-python:pinned-stable-python | | |
| candle:pip-audit-on-every-pr-and-daily | rules-python:pip-audit-on-every-pr-and-daily | | The link to the project's defect page is dropped; its lesson (audit the lock, not an environment) stays in the rule as one sentence. |
| candle:project-tracking | core:github-project-tracking | yes | The sections *What you discover along the way* and *Closing a decision* go to `core`'s `github-project-tracking`. The project's own tracking judgement (its shared Project, its repositories, its CI's draft behaviour). The mechanics are `core`'s `github-project-tracking`; nothing here is a language or data rule. |
| candle:purge-checked-by-a-test | rules-health-data:purge-checked-by-a-test | | |
| candle:python-rules | rules-python:python-rules | yes | Internal API design and the generic part of the import-direction rule go to the pack; the project's layer contract (`cli`, `proxy`, `engine`, the entry-point group, the namespace and the three look-alike names) and its language section stay. Its "What security requires of Python code" section holds the Python realisation of each language-neutral `rules-security` rule, one line each. |
| candle:resolve-a-library-then-read | rules-security:resolve-a-library-then-read | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:restart-safely | rules-security:restart-safely | | |
| candle:runtime-defined-by-the-repository | rules-security:runtime-defined-by-the-repository | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:sbom-at-each-release | rules-security:sbom-at-each-release | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:secrets-through-dedicated-types | rules-security:secrets-through-dedicated-types | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:submitted-content-is-data | rules-security:submitted-content-is-data | | |
| candle:subprocess-without-a-shell | rules-security:subprocess-without-a-shell | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:tls-on-every-transport | rules-security:tls-on-every-transport | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:typescript-rules | rules-typescript:typescript-rules | yes | Biome discipline, `pnpm add`, what Biome rejects and the plan code-block rule go to the pack; the `agent/` scope, the clinical agent's instructions and the CI jobs' facts runners stay. |
| candle:uv-lock-is-authoritative | rules-python:uv-lock-is-authoritative | | |
| candle:validate-once-at-the-edge | rules-security:validate-once-at-the-edge | | Language-neutral principle; its Python realisation is a line of `rules-python:python-rules`. |
| candle:version-never-written-by-hand | rules-python:version-never-written-by-hand | yes | The principle and the `hatch-vcs` mechanism (`dynamic = ["version"]`, the tag as the only source) go to the pack; the project's `tooling/version_hook.py`, its sibling pinning, its static-dependencies lesson and the `uv build --wheel` note stay. |
| candle:vet-and-trace-every-direct-dependency | rules-security:vet-and-trace-every-direct-dependency | | |
| candle:CLAUDE.md#4-completion-gate | rules-python:ruff-and-noqa-discipline | | Not a wiki page: `CLAUDE.md` §4's ruff paragraph; the rest of §4 is `core`'s `base.md`. |
| candle:SECURITY.md | rules-health-data:data-breach-notification | | Not a wiki page: `SECURITY.md`'s data-breach section, made a rule so `wiki search` finds it; the whole policy, this section included, is also `rules-security`'s `security-policy-template.md`. |
| capture:§1.1 | rules-rust:stable-toolchain-pinned-in-rust-toolchain-toml | | Realisation of `rules-security:runtime-defined-by-the-repository` and `rules-security:deal-with-outdated-dependencies`; no second generic rule. |
| capture:§1.2 | rules-security:lockfile-versioned-and-authoritative | | New language-neutral principle (the lockfile is committed and authoritative), written once; `rules-python:uv-lock-is-authoritative` was its Python realisation. |
| capture:§1.2 (Cargo) | rules-rust:cargo-lock-is-versioned | | Realisation of the security rule above (ANSSI `DENV-CARGO-LOCK`). |
| capture:§1.2 (SwiftPM) | rules-swift:package-resolved-is-versioned | | Realisation of the security rule above; the "no dependency" line is the general preference for system frameworks. |
| capture:§1.3 | rules-rust:dependency-trace-records-unsafe-and-prefers-std | yes | The trace's `unsafe` column is the Rust realisation of `rules-security:vet-and-trace-every-direct-dependency`; the agent's zero-dependency choice and its `docs/dependencies.md` stay. |
| capture:§1.4 | rules-rust:dependency-trace-records-unsafe-and-prefers-std | yes | The 18-month warning is already in `rules-security:vet-and-trace-every-direct-dependency`; the `std` before a crate lesson goes in the same Rust rule; the `fs2` case stays. |
| capture:§1.5 | rules-rust:cargo-audit-and-deny-on-every-pr | | Realisation of the dependency audit of `rules-security:ci-gates`. |
| capture:§1.6 | rules-rust:cargo-outdated-before-each-cycle | | Realisation of `rules-security:deal-with-outdated-dependencies`. |
| capture:§1.7 | rules-rust:no-build-overrides-from-the-environment | | Realisation of `rules-security:runtime-defined-by-the-repository`. |
| capture:§2.1 | rules-rust:forbid-unsafe-code-in-every-crate | | "No task of the plan needs it" stays. |
| capture:§2.2 | rules-rust:lifting-the-unsafe-ban-is-a-decision | | |
| capture:§2.3 | rules-swift:check-system-api-return-codes | yes | Split in two Swift rules; the Carbon hotkey, the review count and the spec invariant stay in the project. |
| capture:§2.3 (as!) | rules-swift:never-force-cast-a-system-value | | |
| capture:§7 | rules-rust:rust-ci-gates | yes | The `cargo` commands are the Rust realisation of `rules-security:ci-gates`; the no-leak test it asks for is already `rules-security:ci-gates`. The `facts_check.py` lines are the project's own (the method is `core`'s `spec-to-facts`). |
| capture:§7 (swift) | rules-swift:swift-test-in-ci | | The `--package-path agent` and the milestone stay. |
| capture:§0, §3, §4, §5, §6, §8 | stays | | The project's own threat model, spool, content-leak policy, storage, capture integrity and reopening conditions. |

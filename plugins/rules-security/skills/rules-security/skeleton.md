---
title: Security skeleton
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/hubs/security-rules.md
  - https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/hubs/threat-model-and-defence-in-depth.md
  - https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/data-classification.md
  - https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md
---

# Security skeleton

The sections a project's security rules are organised in, and the pack rules that fall in each. Structured after two ANSSI publications from the *Back to basics* collection (cyber.gouv.fr): *Defence-in-depth: a methodology* (v1.0) for the architecture of the measures, and *Sensitive data and processing* (v1.0) for data classification.

**Convention:** `MUST` = non-negotiable, blocks the merge. `SHOULD` = a deviation is possible, to be justified in review.

Each rule carries its **justification**: it says what the rule applies to, and so when it does not apply. If a rule does not bite on what the project does, say so and argue it. Do not bypass it silently. Sections *Untrusted input* to *Authentication, authorisation, traceability* assume a network surface; a project with no exposed service sets them aside explicitly rather than leaving them there as decoration.

**Scope to establish per project.** `rules-health-data:data-classification` asks for a classification of the project's real data. Until it is written, the rules that refer to it (*No leakage of sensitive data*, `rules-security:encrypt-at-rest-and-in-transit`) have no target: it is the first thing to produce.

## Threat model and data classification

The guiding principle (ANSSI): **any security measure can be bypassed**. Protection therefore rests on **multiple, robust and independent** layers: a single attack must not get past several safeguards at once.

The surfaces below are those of an exposed service that processes content supplied by third parties. Remove the rows outside the scope, add those the project introduces.

| Surface | Main threat | Independent layers | Section |
|---|---|---|---|
| HTTP endpoints | Untrusted input leading to a crash (DoS), abusive deserialisation | Edge limits · edge validation · global exception handler | Untrusted input |
| Submitted documents | Malicious file (booby-trapped PDF, decompression bomb, XML/image bomb) | Detection by magic bytes · hardened parsers · resource limits | Dynamic code and parsing of untrusted content, Untrusted input |
| Logs, traces, errors | Sensitive data leaking to an uncontrolled channel | Redacted reprs · field allow-list · opaque errors | No leakage of sensitive data |
| Third-party dependencies | Supply chain compromise | Versioned lock · CI audit · traced dependencies | Toolchain and dependencies |
| Storage and transport | Unauthorised access, interception | TLS · encryption at rest · TTL + purge | Transport, storage, cryptography |
| Model calls (LLM/VLM) | Data leaving the trust perimeter | De-id before an external call · explicitly configured endpoints | Transport, storage, cryptography |
| Application access to data | No enforceable traceability | Authentication · per-data authorisation · tamper-proof access log | Authentication, authorisation, traceability |

**Independence of measures** (ANSSI, implementation process): a rule MUST never be justified by "another layer already protects this". The TTL does not exempt you from encryption at rest; pseudonymisation before an external call does not exempt you from opaque errors.

This is the most useful clause of the skeleton, because it shuts down the reasoning one produces spontaneously to exempt oneself from a rule.

- `rules-health-data:data-classification`

The four ANSSI pillars are distributed as follows: **governance** = *Toolchain and dependencies* + the project's versioned documentation; **protection** = *Untrusted input*, *No leakage of sensitive data*, *Transport, storage, cryptography*; **defence** (detect and respond) = *Authentication, authorisation, traceability*, *CI gates* + observability; **resilience** = *Resilience*.

## Toolchain and dependencies

These rules are the source of truth for everything that touches dependencies. A project's instructions point to them rather than copying them.

- `rules-security:never-write-a-version-from-memory`
- `rules-security:vet-and-trace-every-direct-dependency`
- `rules-security:resolve-a-library-then-read`
- `rules-security:deal-with-outdated-dependencies`
- `rules-security:sbom-at-each-release`
- `rules-security:runtime-defined-by-the-repository`
- Python: `rules-python:pinned-stable-python`, `rules-python:uv-lock-is-authoritative`, `rules-python:pip-audit-on-every-pr-and-daily`, `rules-python:version-never-written-by-hand`

## Dynamic code and parsing of untrusted content

Applies as soon as the project parses a file or a stream supplied by a third party. After the network, this is the largest attack surface.

- `rules-security:subprocess-without-a-shell`
- `rules-untrusted-parsing:bounded-decompression`
- `rules-untrusted-parsing:bounded-image-rendering`
- Python: `rules-python:no-eval-exec-pickle-or-unsafe-yaml`, `rules-python:parse-xml-with-defusedxml`

## Untrusted input

- `rules-security:no-raw-exception-escapes-the-network`
- `rules-security:validate-once-at-the-edge`
- `rules-security:input-schemas-refuse-unknown-fields`
- `rules-security:explicit-service-bounds`
- `rules-untrusted-parsing:file-type-from-magic-bytes`
- `rules-security:parameterised-sql`
- `rules-security:submitted-content-is-data`

## No leakage of sensitive data

- `rules-security:no-default-repr-for-sensitive-types`
- `rules-health-data:no-identifier-or-content-in-logs`
- `rules-security:opaque-error-responses`
- `rules-security:secrets-through-dedicated-types`
- `rules-health-data:no-real-data-in-test-datasets`

## Transport, storage, cryptography

- `rules-security:tls-on-every-transport`
- `rules-security:no-home-made-cryptography`
- `rules-security:constant-time-secret-comparison`
- `rules-security:encrypt-at-rest-and-in-transit`
- `rules-security:only-configured-outgoing-endpoints`

## Authentication, authorisation, traceability

- `rules-security:every-request-authenticated`
- `rules-security:authorise-at-the-data-not-the-route`
- `rules-health-data:log-every-sensitive-access`
- `rules-health-data:access-logs-unmodifiable-by-producer`

## CI gates

- `rules-security:ci-gates`

## Resilience

- `rules-security:restart-safely`
- `rules-health-data:purge-checked-by-a-test`
- `rules-security:losing-a-backend-keeps-the-service-up`

---
name: rules-security
description: 'Security rules that hold in any language: authentication and authorisation at the data, secrets and cryptography, TLS and outgoing endpoints, untrusted input and submitted content, opaque errors and no leaking representation, subprocesses, dependencies and the supply chain, CI gates, resilience. Cited as rules-security:<slug>. Read a rule file when a skill or the base rules cite it, or before touching input parsing, the network, logs, secrets or storage.'
---

# Security rules

Rule files sit in `rules/`, one per file. Cite one as `rules-security:<slug>`. Each rule carries its justification: it says what the rule applies to, and so when it does not apply.

Two files beside `rules/` are not rules:

- `skeleton.md`: the security sections a project's rules are organised in, from the threat model to resilience, with the rules of every pack that fall in each.
- `security-policy-template.md`: the template of a project's `SECURITY.md` (reporting a vulnerability, data breach).

## Rules

- Authorisation MUST be checked on every access to a piece of data, at the level of the data, not of the route — `rules-security:authorise-at-the-data-not-the-route`
- CI gates — `rules-security:ci-gates`
- Secret comparisons MUST be constant-time — `rules-security:constant-time-secret-comparison`
- Outdated dependencies MUST be dealt with before each development cycle — `rules-security:deal-with-outdated-dependencies`
- Sensitive data MUST be encrypted at rest and in transit, including on internal links — `rules-security:encrypt-at-rest-and-in-transit`
- Every request MUST be authenticated — `rules-security:every-request-authenticated`
- The service MUST enforce explicit bounds — `rules-security:explicit-service-bounds`
- Input schemas MUST refuse unknown fields — `rules-security:input-schemas-refuse-unknown-fields`
- Losing a backend MUST NOT bring the service down — `rules-security:losing-a-backend-keeps-the-service-up`
- NEVER write a version from memory — `rules-security:never-write-a-version-from-memory`
- A type that carries sensitive data MUST NOT have a default representation — `rules-security:no-default-repr-for-sensitive-types`
- The project MUST NOT implement any cryptographic primitive — `rules-security:no-home-made-cryptography`
- A code path reachable from the network MUST NOT let a raw exception escape — `rules-security:no-raw-exception-escapes-the-network`
- Outgoing calls MUST target only explicitly configured endpoints — `rules-security:only-configured-outgoing-endpoints`
- Error responses returned to the caller MUST be opaque — `rules-security:opaque-error-responses`
- Every SQL query MUST be parameterised — `rules-security:parameterised-sql`
- Before using a library you do not know well, resolve it, then read — `rules-security:resolve-a-library-then-read`
- The service MUST restart safely — `rules-security:restart-safely`
- The runtime environment MUST be entirely defined by the repository — `rules-security:runtime-defined-by-the-repository`
- An SBOM MUST be produced at each release — `rules-security:sbom-at-each-release`
- Secrets MUST be handled through dedicated types — `rules-security:secrets-through-dedicated-types`
- Submitted content MUST be treated as data, never as instructions — `rules-security:submitted-content-is-data`
- Every subprocess MUST be invoked without a shell — `rules-security:subprocess-without-a-shell`
- TLS MUST be required on every transport — `rules-security:tls-on-every-transport`
- Validation MUST happen at the edge, once, and produce a validated type — `rules-security:validate-once-at-the-edge`
- Every direct dependency MUST be vetted and the vetting traced — `rules-security:vet-and-trace-every-direct-dependency`

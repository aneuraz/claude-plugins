---
title: Classification of the data processed
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/data-classification.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#01-classification-of-the-data-processed
---

# Classification of the data processed

Applies the ANSSI *Sensitive data and processing* method: an inventory of the project's data categories, their sensitivity level, and their authorised zone. **Every new component or flow MUST be placed in the project's table before merge**: this is the control of interconnections between levels that the guide requires.

Fill the template below with the project's real categories and real storage locations, as a page of the project's own. A row whose "Where it may live" column does not name an existing storage is a criterion nobody can verify.

| Category | Sensitivity | Where it may live |
|---|---|---|
| User content and its intermediate states | depends on the nature of the data | to establish; never: logs, errors, fixtures, git |
| Access metadata (log: who, what, when, from where) | Sensitive, reveals activity | separate audit stream, write-only, governed retention |
| Opaque technical identifiers (correlation_id, job_id) | Low **by construction**: plain UUIDs, no link to the content | application logs, error responses, audit stream (`rules-health-data:no-identifier-or-content-in-logs`, `rules-security:opaque-error-responses`) |
| Secrets (API keys, outgoing credentials) | Sensitive | environment or vault; never code, versioned config, logs |
| Technical data (logs, metrics, config without secrets) | Low **by construction**: the no-leakage rules are what guarantee that no user content gets in | freely exportable to observability |
| Development artefacts (fixtures, eval corpus) | Low by construction (`rules-health-data:no-real-data-in-test-datasets`: never real data) | git repository, CI |

Three consequences of the method:

- **Aggregation raises sensitivity.** A store that accumulates the content of many users is worth more, once compromised, than an isolated document. The short TTL and the purge (`rules-security:encrypt-at-rest-and-in-transit`, `rules-health-data:purge-checked-by-a-test`) are not a convenience: they are the anti-aggregation measures that keep the store at its assessed sensitivity level.
- **Priority follows exposure.** The most exposed surface protects the most sensitive category, so that is where review effort goes first (the dynamic-code and untrusted-input sections of `rules-security`'s skeleton).
- **A storage that hosts the sensitive data is classified as a whole.** If there is no watertight partition between "the normal storage" and "the one that holds the sensitive data", the whole inherits the highest level, backups included. This is a **deployment** requirement, not an application mechanism: the service does not control how its operator backs up its volumes.

Outside the scope of this rule: security of the hosting infrastructure, management of business authorisations.

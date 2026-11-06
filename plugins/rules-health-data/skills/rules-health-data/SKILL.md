---
name: rules-health-data
description: 'Rules for projects that process personal or health data: classification of the data processed, no identifier or content in logs, logging every sensitive access, access logs the producer cannot modify, no real data in test datasets, the purge checked by a test. Cited as rules-health-data:<slug>. Read a rule file when a skill or the base rules cite it, or before adding a data flow, a store, a log or a fixture.'
---

# Health-data rules

Rule files sit in `rules/`, one per file. Cite one as `rules-health-data:<slug>`.

The GDPR/CNIL breach procedure is part of `rules-security`'s `security-policy-template.md`.

- Access logs MUST NOT be modifiable by the service that produces them — `rules-health-data:access-logs-unmodifiable-by-producer`
- Classification of the data processed — `rules-health-data:data-classification`
- Every access to sensitive data MUST be logged — `rules-health-data:log-every-sensitive-access`
- Logs MUST NOT contain a direct identifier or user content — `rules-health-data:no-identifier-or-content-in-logs`
- Test datasets and the evaluation corpus MUST NOT contain real data — `rules-health-data:no-real-data-in-test-datasets`
- The purge (TTL) MUST be checked by a test — `rules-health-data:purge-checked-by-a-test`

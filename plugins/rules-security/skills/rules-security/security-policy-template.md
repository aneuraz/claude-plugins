---
title: SECURITY.md policy template
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/SECURITY.md
---

The template of a project's `SECURITY.md`. Copy it to the repository root and replace the placeholders in angle brackets. The breach section cites `rules-health-data:data-breach-notification`, which holds the deadlines; drop the section in a project that holds no personal data.

```markdown
# Security policy

## Reporting a vulnerability

Do not open a public issue. Report to **security@\<domain\>**. A PGP key is available on request.

Please include the affected version or commit, a description, steps to reproduce and the estimated impact.

**Commitments.** We acknowledge receipt within 3 business days, give an initial assessment within 10 business days, and tell you about the fix and its deployment date. Coordinated disclosure: we ask for a delay of 90 days or until the fix date, whichever comes first. We will take no action against researchers who follow this procedure.

**Forbidden.** Any test on the production environment, and any attempt to access, extract or modify real data. A test environment can be provided on request.

## In case of a data breach

A suspected breach involving personal data follows `rules-health-data:data-breach-notification`: it is reported at once to <the CISO and the DPO, and how to reach them>.

## Code security rules

The rules for development are in <where the project's security rules live>. They cover the supply chain, parsing untrusted content, network input, leak prevention, cryptography and traceability.
```

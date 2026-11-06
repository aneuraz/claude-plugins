---
title: Every subprocess MUST be invoked without a shell
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/subprocess-without-a-shell.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
---

# Every subprocess MUST be invoked without a shell

Pass an argument list, never a shell string (in Python, `subprocess.run([...], shell=False)`), with a timeout; the subprocess SHOULD be isolated (throwaway working directory, bounded resources).

*Justification:* `shell=True` on a file name supplied by a third party is command injection; a converter that loops without a timeout is a DoS.

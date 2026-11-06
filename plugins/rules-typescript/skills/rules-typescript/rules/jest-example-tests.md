---
title: Jest example tests
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# Jest example tests

A level 1 fact (one input, one output) is a Jest test; with supertest for an HTTP endpoint. Put the fact id in the test name so the trace runs both ways.

```ts
test("AUTH-001: expired JWT → 401 TOKEN_EXPIRED", async () => {
  const r = await request(app).post("/auth/refresh").set("Authorization", `Bearer ${expiredToken}`);
  expect(r.status).toBe(401);
  expect(r.body.code).toBe("TOKEN_EXPIRED");
});
```

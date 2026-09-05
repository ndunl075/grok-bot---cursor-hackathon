---
name: grade-watch
schedule: every 4 hours
skill: grade-model
---

# grade-watch

Every 4h. Recompute RiskScore per course.

**Sends only on a transition:**
- `at_risk` flipped false → true, or true → false
- `current_pct` moved by ≥ 2 points (a grade landed)

Not on state. A course that has been at risk for a week does not generate four
messages a day.

```
CSE 3901: Quiz 4 came back 68. You're at 84 now, floor 71.
```

State: `routine_state:grade-watch` holds the previous `{current_pct, at_risk}`
per course for comparison.

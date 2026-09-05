# Fixtures

Realistically-shaped Canvas API responses, trimmed to the fields the skills
actually read. Real Canvas objects carry 60+ fields; these carry the ~15 that
matter. Shape and types are faithful — IDs are strings (Canvas string-ids),
`score` is `null` when ungraded, `group_weight` is a float percentage.

**No live calls.** Every skill must produce `expected_output.json` from these
files alone. That is the test.

Scenario: a Tuesday in week 6. Five enrolled courses, one of them API-restricted.

| Course | Weights | Story |
|---|---|---|
| CSE 3901 | published | Project 2 due Thursday, 25% impact, unsubmitted. The headline. |
| MATH 2153 | **not published** | Midterm 2 Friday. Exercises the equal-weight caveat path. |
| PHYS 1250 | published | Wednesday lecture cancelled. Exercises the ⚠ bypass. |
| ENGL 1110 | published | Two sub-3% items. Must be suppressed, not listed. |
| HIST 2610 | — | Returns 403. Must degrade, not crash. |

Nothing here is real. No real student, course, or instructor.

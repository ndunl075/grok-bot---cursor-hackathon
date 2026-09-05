---
name: weekly-retro
schedule: Sunday 18:00
skill: weekly-retro
---

# weekly-retro

Sunday 18:00. Always sends.

Four lines, per `skills/weekly-retro/SKILL.md`:
1. Grade deltas this week, largest absolute move first.
2. Highest-impact item in the next 7 days.
3. At-risk course, or "nothing at risk."
4. One concrete action.

This is the only routine that carries state across weeks: it stores a snapshot
of every course's `{current_pct, floor_pct, ceiling_pct}` at the end of each
run and diffs against it on the next. Write the snapshot **after** composing —
writing it first makes every delta zero, which reads as a broken bot and is
hard to spot because zero is plausible.

Do not let it grow past four lines.

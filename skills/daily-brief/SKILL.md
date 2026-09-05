---
name: daily-brief
description: Composes the morning message. Merges risk scores, work due in 72h, and overnight announcements into at most six ranked lines. Use for the daily brief and the weekly retro.
---

# daily-brief

## Inputs

- `RiskScore[]` from grade-model (all non-ignored courses)
- assignments due within 72h
- announcements from the last 24h
- `UserPrefs.brief_style`

## Ranking

Sort every candidate item by `impact_pct`, then by urgency. Emit in that order.
This is the rule that separates this bot from a to-do list: a 2%-impact essay
due tomorrow ranks below a 15%-impact exam due Friday.

Exception: anything flagged `⚠` by announcement-digest (cancellation, due-date
change) goes first regardless of impact. Schedule changes are time-sensitive in
a way grades are not.

## Shape

**short** (default) — max 6 lines, no preamble, no sign-off.

```
CSE 3901 project due Thu — 25% of your grade, not started.
MATH 2153 exam Fri. Projected 84, floor 68.
⚠ PHYS 1250 lecture cancelled Wednesday.
```

**full** — same ranking, adds one clause of reasoning per line, still capped
at 8 lines.

## Hard rules

- **Never list everything.** If nine things qualify, emit the top three and
  end with "…and 6 smaller things." The student can ask.
- **Lead with the highest-impact item.** Not the earliest. Not the newest.
- **No greeting.** "Good morning!" costs a line and says nothing.
- If there is genuinely nothing — nothing due in 72h, no risk change, no
  announcements — send **one** line: "Nothing due before Monday. You're clear."
  A brief that says "you're clear" is trusted. A brief that manufactures
  content to justify itself is muted.

## Weekly retro (Sun 18:00)

Different shape, four lines:
1. What moved: grade deltas per course, largest first.
2. What's coming: highest-impact item in the next 7 days.
3. One at-risk course, or "nothing at risk."
4. One concrete action for the week.

Never more than four lines. The retro is a summary, and a summary that runs
long has failed at its only job.

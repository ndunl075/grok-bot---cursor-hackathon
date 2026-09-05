---
name: weekly-retro
description: The Sunday evening summary. Compares this week's grades against last week's stored snapshot, names what moved and why, and gives one action for the week ahead. Use for the weekly-retro routine.
---

# weekly-retro

The only routine that makes the bot feel like it has been paying attention
rather than just reacting. Four lines. Never five.

## It needs a snapshot, and nothing else writes one

Every other skill is stateless-ish. This one is not: a delta requires last
week's numbers. Store them yourself, at the end of every run:

```yaml
routine_state:weekly-retro:
  last_run: iso8601
  snapshot:
    "{course_id}": {current_pct, floor_pct, ceiling_pct}
```

**Write the snapshot after composing, not before.** Compose against the old
one, then overwrite. Getting this backwards produces a retro that reports every
delta as zero, which looks like the bot is broken and is hard to notice because
zero is a plausible number.

First run has no snapshot. Say so plainly — "first week, so no comparison yet" —
and write the snapshot. Do not print deltas of `current_pct - 0`.

## The four lines

**1. What moved.** Grade deltas, largest *absolute* move first. Signed, one
decimal. Only courses that moved by ≥ 0.5; a 0.1 drift is noise.

> CSE 3901 −5.4 (the midterm landed). MATH 2153 +2.9.

Say *why* when you can attribute it: exactly one assignment moved from ungraded
to graded in that course this week. When two or more did, don't guess — name
the count instead ("three things graded").

**2. What's coming.** The single highest-impact item due in the next 7 days.
Not a list. If nothing is due, say that; it is real information on a Sunday.

**3. Risk.** One at-risk course, or "nothing at risk." A course whose target
went *unreachable* this week outranks a course that has been at risk for a
month — that is news, the other is background.

**When two courses go unreachable in the same week**, lead with the one whose
grade moved most this week, not the one whose ceiling fell furthest. The
student can connect a moved grade to a cause they remember; a ceiling that
drifted down as ungraded work piled up has no such moment attached to it.
Mention the second in the same line, in four words, or not at all.

**4. One action.** Concrete, doable this week, tied to line 2 or 3. "Start
Project 2 before Wednesday" is an action. "Keep up the good work" is not, and
neither is "review your grades."

## Shape

```
Week in review.
CSE 3901 −5.4 (midterm landed), MATH 2153 +2.9.
Biggest thing this week: Project 2, Thursday, 25%.
An A in CSE 3901 closed this week — ceiling is 88.0. An 85 still holds.
Do: start Project 2 before Wednesday. It's the only thing that moves anything.
```

## Never

- Never grow past four lines plus the header. The retro's only job is to be
  read on a Sunday evening, and a long one is not.
- Never editorialize about effort. You can see grades, not work. "You've been
  slipping" is both unfounded and the fastest way to get muted.
- Never skip a week silently. If Canvas was unreachable, send three lines from
  the stored snapshot and say the data is stale.

---
name: deadline-guard
description: Fires deadline warnings at 48h and 24h, ranked by grade impact and deduped so the same assignment is never nudged twice in a window. Use for the deadline-48h and deadline-24h routines.
---

# deadline-guard

## Windows

**48h** — `unsubmitted AND impact_pct >= 3 AND due within 48h`

The architecture originally specified `unopened OR unsubmitted`. `opened` is
not obtainable from the student-scoped Canvas API (see canvas-core), so the
rule is impact-gated instead. The 3% floor is the point: below it, a nudge
costs more attention than the assignment is worth.

**24h** — `unsubmitted AND due within 24h`, no impact floor. At 24h,
everything is worth a mention.

## Dedupe

Read `routine_state:deadline-{window}.sent_ids` before composing. Skip any
assignment already there. **Append before sending**, not after — an
un-sent-but-recorded item is a missed nudge; a sent-but-unrecorded item is a
double nudge, and double nudges are how the bot gets muted.

Prune `sent_ids` to 30 days on every run.

An assignment appears in the 48h window and again in the 24h window. That is
correct and intended — they are separate `routine_state` keys. Two nudges for
one assignment across two days is the design. Two in one day is a bug.

## Quiet hours

If the window opens during quiet hours, hold and send at the boundary. Do not
drop. A 24h warning suppressed at 2am and delivered at 7am is still 19 hours
of warning.

## Message

```
{assignment} due {relative time} — {impact_pct}% of your grade.
```
> Project 2 due tomorrow 11:59pm — 25% of your grade.

At 24h only, append the offer, once per assignment, ever:
> Reply 'ext' and I'll draft an extension email.

Batch multiple hits from one run into one message, highest impact first, max
three lines. Never send two messages in the same run.

## What not to do

- Do not nudge on submitted work, even if the grade is bad. That's grade-watch.
- Do not nudge on `due_at == null`. Undated assignments are not deadlines.
- Do not nudge on an assignment in `UserPrefs.ignore_courses`.
- Do not re-nudge after a student submits. Check `submitted` at send time, not
  at query time — they may have submitted in the last 15 minutes.

# Path C — no outbound HTTP

If the bot cannot issue authenticated requests to arbitrary hosts, the token is
useless and grades are unreachable. Do not pretend otherwise. Degrade in this
order and tell the student exactly which tier they are on.

## Tier 1 — ICS calendar feed (no auth, no token)

Canvas publishes a per-user iCalendar feed at a long unguessable URL:
**Calendar → Calendar Feed** (bottom right) → copy link.

```
https://{host}/feeds/calendars/user_{opaque_token}.ics
```

It is a plain `GET` with no headers. If the bot can fetch *any* URL, this
works. It yields assignment names, due dates, and course association.

Gets you: deadline-guard, calendar-sync, the due-date half of daily-brief.
Loses you: points, weights, submission status, scores — so no grade-model,
no risk scoring, no "what this does to your grade." That is most of the
product, so say so plainly rather than shipping a worse bot quietly.

> The feed URL is a bearer credential in disguise. Anyone with it reads the
> student's schedule. Treat it exactly like the token: memory only, never in a
> template, never echoed back.

## Tier 2 — pasted grade snapshot

Ask the student to open **Grades** in a course and paste the table. Parse it
into `Assignment[]`. Refresh on request, not on a schedule.

Gets you: a real grade-model run, once, on demand.
Loses you: everything proactive, which is the entire premise.

## Tier 3 — advice only

No Canvas data. The bot becomes a study planner the student feeds by hand.
This is not the product. If you land here, say so in the first-run flow rather
than letting the student discover it a week later.

## What to tell the student

Name the tier in one line, once, at setup:

> Heads up: I can read your Canvas calendar but not your grades, so I'll catch
> every deadline but I can't tell you what they're worth. If that changes I'll
> upgrade myself.

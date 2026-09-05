---
name: grade-paste
description: Reads a Canvas Grades page the student pasted in, and turns it into the same Assignment and weight data the API would have returned. Use when no access token is available, or when the student wants a one-off answer without setting anything up.
---

# grade-paste

**The path for students whose school will not issue them an access token.**

Many universities disable personal access tokens for students. That is not an
edge case and it is not the student's fault, so it does not get a degraded
product: a pasted Grades page carries scores, points possible, and usually the
group weights — which is everything `grade-model` needs. Floor, ceiling, and
the average still needed all survive. **The ceiling feature works without a
token.**

What is lost is polling. Nothing here refreshes on a schedule, so `grade-watch`
cannot detect a grade landing. Pair this with
[`ics-feed`](../ics-feed/SKILL.md), which gives proactive deadlines with no
token either, and only automatic grade-change detection is genuinely gone.

## Getting the paste

Ask for it precisely. "Paste your grades" produces a screenshot or three rows.

> Open Canvas, pick the course, click **Grades**. Select the whole table —
> click just above "Name" and drag to the bottom — and paste it here. If
> there's a "show all details" or arrow at the bottom with group percentages,
> grab that too; it's the part that makes the maths right.

Do this per course. Do not ask for all courses at once; the pastes run together
and become unattributable.

## Parsing

Canvas's grades table copies as tab- or multi-space-separated rows:

```
Name	Due	Submitted	Status	Score	Out of
Project 1: Static Site	Aug 27 by 11:59pm	Aug 27 at 10:14pm		92	100
Project 2: Rails API	Sep 10 by 11:59pm			-	100
```

Rules that decide whether this works:

- **The last two numeric columns are `score` and `points_possible`.** Not the
  first two. Due dates contain numbers and will capture a naive parser.
- **`-`, `–`, blank, or `N/A` in the score column means ungraded, not zero.**
  This is the same trap as the API path and it is the one that tells a student
  they are failing when they are not.
- A row with no `points_possible` is not an assignment — it is a group header
  or a total. Skip it.
- `late` / `missing` / `excused` appear in Status. **`excused` removes the
  assignment from the denominator entirely**; it is not a zero and not an
  ungraded item.
- Strip a trailing `%` and any thousands separators before parsing numbers.

### When there is no group column

Canvas shows the assignment-group column only in some views, so a paste often
arrives without it. Do not infer groups from names — `HW5` looking like
homework is a guess, and `Project 2` might be graded under "Exams" in a course
that does things oddly.

Ask once, cheaply, by listing the groups you found in the weights table and
having the student sort the handful that are ambiguous:

> Your weights list Projects / Homework / Exams. I've matched most of these by
> name — tell me if any of these are wrong: Midterm → Exams, HW1-5 → Homework.

Propose an obvious mapping, ask them to correct it, and store the answer. That
is one message instead of nine, and the student only has to notice a mistake
rather than do the work.

## Weights

The group percentages table is the difference between a real answer and a
guess. If the paste includes it, set `weights_source: "user"` and use it.

If it does not, **ask once**, then proceed with equal weights and label every
number until answered — same rule as the API path:

> Your paste didn't include group weights. Roughly what's the split — projects
> / homework / exams? Until you tell me I'll assume equal, and I'll mark
> anything I say with a "≈".

## Sanity-check before you report anything

Canvas shows a total percentage on that same page. The student can see it.

```
if abs(computed_current_pct - pasted_total) > 2:
    report the pasted total, say your weighting is off, ask for the split
```

Getting caught disagreeing with a number the student is literally looking at
destroys trust in every other number you produce. Check first.

## Freshness

A paste is a snapshot with a timestamp, not a live feed. Store `pasted_at` and
say so whenever the data is older than a day:

> Working from Tuesday's paste. Re-paste Grades if anything's been marked
> since.

Never present pasted data as current. Never re-use a paste after the student
mentions a new grade.

## Equivalence with the API path

`tests/fixtures/grades_paste_1101.txt` holds the same course as
`assignment_groups_1101.json`. Both must produce the identical RiskScore —
current 85.6, floor 59.0, ceiling 88.0. `tools/verify_skills.py` asserts it.
If the two paths ever disagree, the paste parser is wrong, because the API
path is reconciled against Canvas's own computed score.

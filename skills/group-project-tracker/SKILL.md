---
name: group-project-tracker
description: Detects group assignments and tracks whether the group's shared submission has been made. Use alongside deadline-guard when an assignment has a group category.
---

# group-project-tracker

## Detecting a group assignment

`assignment.group_category_id` is non-null. That's the whole test.

```
GET /courses/{id}/assignments?include[]=submission   -> group_category_id
GET /group_categories/{gcid}/groups                  -> the groups
GET /groups/{gid}/users                              -> members
```

The student's own group is the one containing their user id.

## What Canvas actually tells you, and what it doesn't

For a group assignment with `grade_group_students_individually: false`, there
is **one submission for the whole group**. It is submitted or it is not. Canvas
does not expose who wrote what, who pushed to the repo, or who has been
carrying the project.

This is the single most important constraint on this skill. The tempting
feature — "Marcus hasn't done his part" — **cannot be built** from this API,
and faking it from submission timestamps or comment authorship would be
guessing about a real person the student has to sit next to on Thursday. Do not
do it. Name the *group's* state, never a member's.

When `grade_group_students_individually: true`, submissions are per student and
you may say how many of N have submitted — as a count, still without naming
anyone:

> 2 of 4 in your group have submitted. Yours is one of them.

That is the ceiling of what's honest here.

## What it adds over deadline-guard

deadline-guard already nudges on unsubmitted work. This adds three things:

1. **It says "group" out loud**, because the student's mental model of the
   deadline is different when someone else can submit for them.
2. **It nudges earlier.** Coordination takes days. Group assignments enter the
   warning window at **72h**, not 48h, and only for `impact_pct >= 5` — a group
   assignment small enough to fall under that isn't worth a separate message.
3. **It stops nudging the moment any group member submits**, not when the
   student does. Re-check the group submission at send time; a teammate may
   have submitted an hour ago and a nudge after that is actively wrong.

## Message

```
Project 2 is a group submission, due Thursday, 25%. Nobody in your group has
submitted yet.
```

One line. Add the member count only if you have individual submissions.

Dedupe in `routine_state:group-project-tracker.sent_ids`, keyed by
`{assignment_id}`, same rules as deadline-guard: append before sending, prune
at 30 days. It shares the window with deadline-guard, so when both would fire
for the same assignment, **this one wins and deadline-guard stays silent** —
otherwise the student gets two messages about one deadline.

## Privacy

Store teammates' Canvas ids and short names only, and only for the current
term's active groups. Never store or repeat their grades, their submission
times, or anything from their comments. Delete the group when the assignment is
graded. `bot/MEMORY_SCHEMA.md` forbids everything else and this is the skill
most likely to violate it by accident.

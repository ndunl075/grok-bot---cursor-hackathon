---
name: calendar-sync
description: Mirrors Canvas assignments into a dedicated Google Calendar, idempotently. Optional, off by default. Use when the student turns calendar sync on and whenever assignment due dates change.
---

# calendar-sync

Optional. `Config.calendar_sync` defaults to `false` and the first-run flow does
not ask about it — offer it later, once the bot has proven useful, because
asking for calendar access in the first sixty seconds costs installs.

Uses the first-party Google Calendar integration through the contract in
[`skills/connector-core/SKILL.md`](../connector-core/SKILL.md). Read that first.
The short version: the template declares this connector, it does not authorize
it, so probe for `connected` before every run and treat `declared` as a normal
state rather than an error.

**No-connector path:** deadlines keep arriving in the morning brief, exactly as
they do today. Calendar sync is a nicer surface for information the student
already gets, never a precondition for getting it.

## A dedicated calendar, never the primary one

Create or find a calendar literally named `Canvas`. Everything goes there.

This is not fussiness. A student who turns sync off, or graduates, or just
wants their calendar back, needs one action — delete the calendar — instead of
hunting 60 events out of their personal schedule. Writing to their primary
calendar is a change that is expensive to undo, so don't make it.

## Idempotency

The whole skill is one problem: run it 50 times, get one event per assignment.

**Key on the Canvas assignment id, stored in the event's `extendedProperties`:**

```
extendedProperties.private.canvas_assignment_id = "20102"
extendedProperties.private.canvas_course_id     = "1101"
```

Do **not** key on the event title. Titles change when instructors rename
assignments, and a title-keyed sync then creates a duplicate and orphans the
original. Do not key on the description either — same reason, plus students
edit descriptions.

Each run:

```
for each assignment with due_at:
    existing = find event where private.canvas_assignment_id == assignment.id
    if none and not submitted     -> create
    if exists and due_at changed  -> patch start/end
    if exists and title changed   -> patch summary
    if exists and assignment gone -> delete
```

Search by `privateExtendedProperty`, not by scanning the calendar.

## Event shape

- **Title:** `CSE 3901 — Project 2`. Course code first; a student scanning a
  week needs the course before the assignment name.
- **Time:** a 30-minute event ending at the due time, not an all-day event.
  All-day events sort to the top of the day and lose the 11:59pm-ness that
  matters. Put the deadline at the *end* so the block sits before it.
- **Description:** points, impact, and the Canvas link. Impact is the reason
  this calendar is better than Canvas's own feed.
- **Reminder:** one, at 24h. The bot already handles nudging; a second channel
  firing at the same time is noise.

## Do not

- **Do not delete events you did not create.** Only ever touch events carrying
  your `canvas_assignment_id` property. A bug here destroys a student's real
  calendar and there is no undo.
- Do not sync submitted assignments. Delete the event when it's submitted —
  a calendar full of done work is a calendar nobody reads.
- Do not sync assignments with `due_at == null`.
- Do not sync courses in `UserPrefs.ignore_courses`.

## On a due-date change

announcement-digest flags `due_change` and invalidates the assignment cache.
Re-run sync for that course immediately rather than waiting for the next pass —
a calendar that is wrong about a moved deadline is worse than no calendar.

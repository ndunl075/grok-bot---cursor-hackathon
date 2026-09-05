---
name: ics-feed
description: Reads the student's Canvas calendar feed, which needs no access token, and turns it into due dates. Use as the deadline source whenever a token is unavailable.
---

# ics-feed

**Proactive deadlines with no access token.** Canvas publishes a per-user
iCalendar feed at a long unguessable URL, fetched with a plain `GET` and no
headers. Where a school blocks student API tokens, this is usually still on,
because it is a user-facing calendar feature rather than an API surface.

Paired with [`grade-paste`](../grade-paste/SKILL.md), the no-token setup keeps
almost the whole product: this drives every routine, the paste drives the maths.

## Getting the URL

> Canvas → **Calendar** → **Calendar Feed** (bottom right of the sidebar) →
> copy the link.

```
https://{host}/feeds/calendars/user_{opaque}.ics
```

**Treat it exactly like the access token.** Anyone holding it can read the
student's whole schedule with no login. Store it in bot memory only, never echo
it back, never put it in a handoff, never let it into a template. It is in
`PUBLISH_CHECKLIST.md`'s grep list for this reason.

There is no revocation short of resetting it in Canvas, so a leak is worse than
a token leak in one respect: the student has to go and find the reset.

## Parsing

Standard iCalendar. One `VEVENT` per assignment:

```
BEGIN:VEVENT
DTSTART:20260911T035900Z
SUMMARY:Project 2: Rails API [CSE 3901]
UID:event-assignment-20102@osu.instructure.com
END:VEVENT
```

- **`SUMMARY` carries the course code in trailing square brackets.** Split it
  off: name before, course after. That bracket is the only course attribution
  in the feed.
- **`UID` contains the Canvas assignment id** — `event-assignment-{id}@{host}`.
  Extract it: it is what lets dedupe, `sent_ids`, and calendar-sync keep working
  identically to the API path.
- Unfold folded lines (a leading space continues the previous line) **before**
  parsing, or long assignment names silently truncate.
- Unescape `\,` `\;` `\n`. Canvas escapes commas in summaries and an assignment
  called "Essay 2\, final draft" reads wrong otherwise.
- `DTSTART` is UTC (`Z`). Convert to `Config.timezone` before comparing to
  anything, or every deadline lands on the wrong day for part of the year.
- Skip `VEVENT`s with no assignment `UID` — the feed also carries calendar
  events, office hours, and personal entries the student added.

## What it does not carry

Say this once at setup rather than letting it be discovered:

- No points, no weights, no scores, no submission status.
- So: no impact ranking, no floor, no ceiling — **from this source alone**.
- It cannot tell whether something is already submitted, so a nudge may be for
  work already done.

That last one matters. With no submission state, `deadline-guard` must soften
its wording — "due tomorrow" rather than "you haven't started it" — because
asserting an unsubmitted state you cannot see is the kind of wrong that makes a
student stop reading.

## Combining with a paste

When `grade-paste` data exists for a course, join on assignment name:

- Names match → attach `impact_pct` and submission state from the paste, and
  the full ranked brief comes back.
- No match → the item still appears, dated, unranked, marked plainly:
  "Quiz 3, Friday — I don't have points for this one."

Cache the feed 15 minutes, same as assignments. Never cache it longer: a
due-date change reaches the feed before it reaches the student.

## Failure

- `404` → the feed was reset. Ask for the new URL, and stop retrying the old
  one; retrying a dead feed every routine forever is how quotas get burned.
- HTML instead of `BEGIN:VCALENDAR` → wrong URL, probably the calendar page
  rather than the feed link. Ask again, and name the "Calendar Feed" button.

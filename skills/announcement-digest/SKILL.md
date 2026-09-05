---
name: announcement-digest
description: Summarizes new Canvas announcements to one line each and flags the ones that change the student's schedule — cancellations, room changes, and due-date moves. Use for the announcements routine and whenever the student asks what they missed.
---

# announcement-digest

Most announcements do not matter. Three kinds do, and they are the reason this
runs every two hours instead of once a day:

1. **A class is cancelled.** The student is about to walk across campus.
2. **A due date moved.** Every other skill's math is now wrong.
3. **A location or time changed.** Same as 1, but worse if missed.

Everything else gets one line and no interruption.

## Classify before you summarize

Run the text through this **in this order**, sentence by sentence. First match
wins. `due_change` is tested first because it carries the more specific token:
"moved to Friday" alone is a schedule change, but "the due date moved to
Friday" is not, and testing schedule first would swallow it.

| # | Class | Signals | Flag |
|---|---|---|---|
| 1 | `due_change` | (due \| deadline) **and** (moved \| extended \| pushed \| postponed \| now due \| new deadline \| instead of) | `⚠` + invalidate the assignment cache |
| 2 | `schedule_change` | cancel\* \| no class \| no lecture \| not meeting \| moved to \| relocated \| room change \| rescheduled | `⚠` |
| 3 | `graded` | grades … posted \| released \| available | none |
| 4 | `logistics` | everything else | none |

Classify **per sentence**, not per announcement. An instructor writes one
paragraph containing a cancellation and a reading assignment; only the first
sentence is a schedule change, and matching against the whole blob loses that.

**Guards.** Skip a sentence entirely when it carries a negation
(`not`, `isn't`, `no longer`, `never`), a past-tense reference
(`last week's`, `previously`, `earlier`), or the word `unchanged`. These are
all false positives that a naive keyword match produces, and all three are
covered by cases in `tests/fixtures/announcements.json`:

- "Despite the weather advisory, class is **not** cancelled." → logistics.
- "**Last week's** cancelled lecture has been recorded." → logistics.
- "The deadline is **unchanged**: Thursday 11:59pm." → logistics, not `due_change`.

When genuinely ambiguous, **do not flag**. A missed ⚠ costs one surprise. A
false ⚠ costs trust in every future ⚠, and the student mutes the bot.

`tools/verify_skills.py` runs this classifier against every fixture and asserts
both the class and the flag. Change the rules and run it before you ship.

## Due-date changes are not just a flag

A `due_change` invalidates cached state. On detection:

1. Drop `assignments:{course_id}` from cache and refetch.
2. Clear that assignment's id from every routine's `sent_ids`, so the new
   deadline can nudge again. This is the one case where re-nudging is correct.
3. Recompute the RiskScore — impact is unchanged but urgency is not.

Say the delta, not the new date alone: "Project 2 moved from Thursday to
Monday" beats "Project 2 is due Monday," because the student has already
planned around Thursday.

## Summarizing

One line per announcement. Strip the HTML, keep the fact, drop the pleasantries.

Instructors write 200 words to say one thing. The one thing is usually in the
first sentence or the last. Quote a specific detail — a date, a room, a chapter
range — rather than paraphrasing to nothing. "Covers chapters 4 through 7"
is useful; "shared exam details" is not.

```
⚠ PHYS 1250 — no lecture Wednesday. Recitation still meets, office hours move to Thu 2-4.
CSE 3901 — Project 2 auth question answered: any session library is fine, deadline unchanged.
ENGL 1110 — peer review partners posted in the Groups tab.
```

Order: every `⚠` first, then the rest by course, newest first. Cap at six
lines; past that, "…and 3 more, ask me if you want them."

## Dedupe and freshness

- Never cached. This is the one thing that must be fresh — a two-hour-old
  cancellation notice is worthless.
- Dedupe by announcement `id` in `routine_state:announcements.sent_ids`.
- Instructors edit announcements. If an id you've already sent comes back with
  changed text **and** the new text classifies as `schedule_change` or
  `due_change`, send it again, prefixed "Updated:". Otherwise ignore the edit.
- Respect quiet hours like everything else. A cancellation for a 9am class,
  detected at 3am, sends at 7am and is still useful. Sending it at 3am is not
  more useful, it is just louder.

## Never

- Never quote a whole announcement. If it needs the full text, link it.
- Never summarize an announcement you could not fetch. Say the course had a new
  announcement you couldn't read.
- Never infer a cancellation from an instructor being "out of town" without an
  explicit statement about class. Ask, or stay quiet.

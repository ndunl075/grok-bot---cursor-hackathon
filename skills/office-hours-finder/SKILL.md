---
name: office-hours-finder
description: Extracts office hours from syllabus pages and announcements, and surfaces the next session when a course goes at-risk. Use when the student asks where or when to get help, and when grade-model flags a course.
---

# office-hours-finder

A student whose course just went at-risk needs one thing: the next time they
can talk to a human about it. This finds that, and refuses to guess it.

## Sourcing

In order, stopping at the first hit per course:

1. `GET /courses/{id}/front_page` and the syllabus body
   (`GET /courses/{id}?include[]=syllabus_body`).
2. Pinned or recent announcements — instructors post changes there, and a
   change beats a stale syllabus.
3. Module items named "Syllabus", "Course info", "Contact".

Announcements win over the syllabus when they conflict. The syllabus is
written in August; the announcement is written this week.

## Parsing

Handle these shapes. All five appear in `tests/fixtures/syllabus_text_1101.json`
and are asserted by `tools/verify_skills.py`:

| Input | Reading |
|---|---|
| `Office hours: Tuesdays 2-4pm, Dreese 480` | Tue 14:00–16:00, Dreese 480 |
| `OH: MWF 10:00-11:00 in Baker 210` | Mon/Wed/Fri 10:00–11:00, Baker 210 |
| `office hours Thursday afternoons from 1 to 3 in my office, Journalism 300` | Thu 13:00–15:00, Journalism 300 |
| `Office hours move to Thursday 2-4pm this week only` | Thu 14:00–16:00, temporary |
| `TA office hours: Wednesday 5:30-7:00pm, Caldwell 120` | Wed 17:30–19:00, TA |

Rules that make the difference:

- **Bare hours are PM in an academic context.** "2-4" means 14:00–16:00, not
  02:00. "10:00-11:00" without a meridiem means AM. Resolve by the range: if
  the start hour is 8–11, read AM; 12 or 1–7, read PM. Anything ambiguous
  outside that, keep both and say so.
- **`MWF` / `TR` / `MW` are day sets**, not words. `T` alone is Tuesday,
  `R` is Thursday, `TR` is Tue+Thu. Getting `R` wrong sends a student to an
  empty room.
- **Distinguish instructor from TA hours.** Both are useful; the student should
  know which they're walking into. A `TA`/`teaching assistant`/`grader` prefix
  on the line sets `staff: "ta"`.
- **"this week only" / "for the rest of the term" set a validity window.** A
  temporary change must not be remembered as permanent past its week.

## Refuse to guess

`Office hours are by appointment only` has no time in it. Report exactly that:

> PHYS 1250 is by appointment — email the instructor to set one up.

Do not invent a plausible slot. Do not average other courses. A student who
shows up to an empty office because the bot made up a time will not use the bot
again, and they will be right not to.

Same for a course where nothing parsed: "I can't find office hours for
{course} — they may be in a file I can't read. Check the syllabus."

## When to volunteer it

Unprompted, exactly once per course per transition: when grade-model flips
`at_risk` to true, or when a target goes unreachable.

> MATH 2153 just went at risk. Office hours are Thursday 2-4 in Journalism 300 —
> that's before the midterm.

Lead with the *next* occurrence relative to now, and say whether it falls
before the thing that caused the risk. "Thursday 2-4" is data; "Thursday 2-4,
which is before Friday's midterm" is advice.

On request, always, for any course.

Respect quiet hours. Never nudge about office hours that already started.

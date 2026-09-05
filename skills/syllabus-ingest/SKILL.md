---
name: syllabus-ingest
description: Reads a syllabus image or PDF the student uploads, extracts dated assignments, and proposes only the ones Canvas doesn't already have. Never writes to Canvas. Use when the student sends a syllabus or asks why something isn't showing up.
---

# syllabus-ingest

Input: an image or PDF the student uploads. Output: a list of candidate
assignments for the student to confirm. **Never writes to Canvas.**

The real problem this solves: instructors put the whole term's schedule in a
syllabus PDF and then create the Canvas assignments two weeks at a time. The
student is flying blind about week 9 while Canvas looks complete.

## Extract

Per row: name, date, and weight or points if the table gives them.

- **Resolve the year.** A syllabus says "Oct 14", not "Oct 14 2026". Use the
  course's term. A date that lands before the term start belongs to the next
  calendar year — spring terms cross the boundary and getting this wrong files
  everything twelve months out.
- **Keep the grading-weights table if there is one.** It is often the only
  place course weights are published, and it resolves
  `Course.weights_source == unknown`, which unblocks grade-model. Offer it:
  "Your syllabus says Projects 50 / Homework 20 / Exams 30. Use that?"
- **Skip readings and lecture topics.** "Read ch. 4" is not an assignment.
  Keep only rows with a deliverable or an exam.

## Diff before proposing

This is the part that has to be right. Proposing something the student already
has in Canvas makes the whole feature look broken.

For each candidate, look for a Canvas assignment that matches on **either**:

- normalized name (lowercase, strip punctuation and `#`, collapse whitespace,
  treat `HW`/`Homework`/`Assignment` and `1`/`01`/`One` as equal), **or**
- due date within ±1 day *and* a name that shares a distinctive token

Match on either, not both — instructors rename between the syllabus and Canvas
constantly ("Project 2" becomes "Rails API Project"), and dates shift by a day
for weekends. Requiring both finds almost nothing.

Report three buckets:

```
Found 14 items in your syllabus.
  11 already in Canvas
   2 not in Canvas yet — Final Project (Dec 8, 20%), Presentation (Dec 3)
   1 I'm not sure about — "Unit 4 check-in", Oct 30
```

The uncertain bucket is not a failure, it is the honest output. A student can
resolve one ambiguity in three seconds; they cannot un-trust a bot that
silently guessed wrong.

## What happens to accepted candidates

They are **bot-side only**. Store as `Assignment` entries with
`source: "syllabus"` and `id: null`, and mark them clearly everywhere they
appear:

> Final Project — Dec 8, 20% (from your syllabus, not in Canvas yet)

- They participate in daily-brief and deadline-guard.
- They do **not** enter grade-model's `current_pct`, because they have no
  score and no verified point value.
- They may enter `impact_pct` estimates only if the syllabus published weights,
  and always with the caveat attached.
- When a matching real assignment shows up in Canvas later, replace the
  syllabus entry with it and say so once.
- If calendar-sync is on, they sync, keyed as `syllabus_{hash}` rather than a
  Canvas id.

## Never

- Never create anything in Canvas. There is no API call in this skill that
  isn't a `GET`.
- Never present an extracted date as certain when the source was a photo taken
  at an angle. If OCR confidence is poor or the row was ambiguous, put it in
  the uncertain bucket.
- Never keep the uploaded file. Extract, propose, discard. A syllabus PDF has
  the instructor's name, email, and office in it, and `bot/MEMORY_SCHEMA.md`
  does not permit storing that.

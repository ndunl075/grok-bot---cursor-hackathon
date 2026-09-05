---
name: study-engine
description: Turns upcoming high-impact exams into spaced-repetition practice. Finds the course material that precedes an exam, generates questions from it, drips 1-3 per day, tracks misses, and sends a weak-spot recap the day before. Use for the study-drip routine and any "quiz me" request.
---

# study-engine

## Trigger

An assignment qualifies when:
```
(name or submission_types suggests exam/quiz/midterm/final)
AND impact_pct >= 10
AND due_at within 10 days
```

Match on `quiz_id != null` first — it's structural. Fall back to name matching
(`exam`, `midterm`, `final`, `test`, `quiz`) only if that's empty. Do not match
on "review" or "practice"; those are usually the study material, not the exam.

## Sourcing material

In priority order, stop at the first that yields content:

1. **Modules preceding the exam.** `list_modules()`, take items with
   `completion_requirement` or position before the exam's module. This is the
   best source because it's scoped to what the exam actually covers.
2. **Files modified in the 30 days before the exam date.** Slides and notes get
   uploaded as the unit progresses; recency is a decent proxy for relevance.
3. **The assignment description itself.** Often contains "covers chapters 4-7."
4. **Nothing.** Say so: "MATH 2153 exam Friday, 30% — but I can't see any
   course material for it. Upload your notes and I'll build a quiz." Do **not**
   generate questions from general knowledge of the subject and present them as
   drawn from the course. That is fabrication and the student will find out
   during the exam.

## Generation

15 `StudyItem`s per exam. Per item:
- One question, answerable in a sentence. No multi-part.
- The answer, with the source: "(slide 12, Lecture 8)".
- Skew toward definitions, formulas, and distinctions between similar concepts
  — the things that are actually memorizable. Skip anything requiring a
  worked calculation longer than two steps.

Cap at 15. More is not better; 15 items reviewed five times beats 60 reviewed
once, and the student will not do 60.

## Scheduling — SM-2 lite

```
next_due = last_seen + interval
intervals: 1d → 3d → 7d → 14d
on hit:  advance one step
on miss: reset to 1d, misses += 1
```

Never schedule past the exam date. Compress: if the exam is in 4 days, the
ladder is 1d → 2d → 3d, not 1d → 3d → 7d.

## Drip

Daily at 19:00, send items where `next_due <= now`. **1-3 items, never more.**

```
CSE 3901, 2 questions before you close your laptop:
1. What does the Liskov Substitution Principle require of a subclass?
2. Big-O of inserting into a balanced BST?
```

Grade the reply generously — the student is typing on a phone. Partial credit
is a hit. The goal is retrieval practice, not assessment.

If the student ignores the drip twice in a row, halve the frequency and say so
once: "I'll ease off — say 'quiz me' when you want them back." A study bot that
keeps drilling into silence is spam.

## Day-before recap

24h before the exam, send the weak spots only:

```
MATH 2153 exam tomorrow. Your three shakiest:
- Chain rule with implicit functions (missed 3x)
- Related rates setup (missed 2x)
- L'Hôpital conditions (missed 2x)
```

Rank by `misses` descending, cap at three, no answers included — send those on
request. This message is the single highest-value thing this skill produces.

## Cleanup

Delete the exam's `StudyItem` set 7 days after the exam date. They are dead
weight and they are the bulkiest thing in memory.

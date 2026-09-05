---
name: drive-archive
description: Reads syllabi the student has in Google Drive and saves generated study guides back to a single Canvas Assistant folder. Use when the student mentions a syllabus in Drive, or wants a study guide they can keep.
---

# drive-archive

Two jobs, one connector. Follows
[connector-core](../connector-core/SKILL.md).

**No-connector path:** the student uploads a syllabus to the chat, and study
guides appear in the chat. Both already work. Drive means they don't have to
find the file, and the guide survives the conversation.

## Scope: one folder, and only ever that folder

Create or find a folder named **`Canvas Assistant`** in the student's Drive
root. Everything this skill writes goes there.

> **Never write outside it. Never delete anything you did not create. Never
> move, rename, or reorganize the student's existing files.**

Drive is where people keep their thesis. A bot with write access that
reorganizes helpfully is a catastrophe with no undo, and "I was tidying up" is
not a defence. The only file operations in this skill are: create in our
folder, overwrite a file in our folder that we created, and read a file the
student explicitly pointed at.

## Reading a syllabus

Only on an explicit ask — "my syllabus is in Drive", "grab the 3901 syllabus".
Never scan the student's Drive on a schedule looking for syllabi. A bot that
crawls someone's Drive unprompted is doing something they did not agree to,
even with the access to do it.

```
search: name contains "syllabus" and trashed = false
```

- **One clear match** → read it, hand the text to
  [syllabus-ingest](../syllabus-ingest/SKILL.md), confirm which file:
  "Reading *CSE 3901 Syllabus.pdf*, modified Aug 21."
- **Several matches** → list at most five with their dates and ask. Never pick
  the newest and proceed; a student with `syllabus-final-v3.pdf` and
  `syllabus (1).pdf` knows which is real and you do not.
- **None** → say so and offer the upload path. Do not widen the search to
  every PDF in their Drive.

Read the file, extract, and discard the text. `bot/MEMORY_SCHEMA.md` forbids
keeping the document — a syllabus carries the instructor's name, email, and
office.

## Saving a study guide

When study-engine has produced items for an exam, offer once per exam:

> Want this as a doc you can keep? I'll drop it in your Drive.

On yes, write `Canvas Assistant/{COURSE} — {Exam} study guide`.

**Idempotency by filename in our folder.** One guide per exam, updated in
place as the student misses questions and the weak spots change. A folder
holding `Midterm 2 study guide`, `Midterm 2 study guide (1)`, and
`Midterm 2 study guide (2)` is worse than no folder — the student cannot tell
which is current, and the newest is not obviously the best.

Search our folder by exact name before writing. Found → update. Not found →
create. Never append a counter.

Contents: the questions, the answers, and the source citation study-engine
already tracks (`slide 12, Lecture 8`). Weak spots first, ordered by misses.
A study guide that opens with what they keep getting wrong is worth opening
twice.

## What not to build

- **Do not sync Canvas files into Drive.** They are already in Canvas, the
  student can already download them, and copying them creates a second stale
  copy of someone else's copyrighted course material in the student's account.
- **Do not archive grades.** Drive is not a backup for something Canvas holds
  authoritatively, and a spreadsheet of grades in Drive is a liability with no
  matching benefit.
- **Do not share anything.** Never set permissions, never generate a link,
  never add a collaborator. Everything stays private to the student's account
  unless they share it themselves.

## Failure

Same rule as every connector: the value still lands.

> Couldn't reach Drive. Here's the study guide — copy it, I'll try again next
> time.

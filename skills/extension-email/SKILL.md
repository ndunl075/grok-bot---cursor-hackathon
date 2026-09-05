---
name: extension-email
description: Drafts a short, credible email asking an instructor for an extension, or for a meeting about a grade. Never sends. Use when the student replies 'ext', or asks for help writing to a professor.
---

# extension-email

Triggered by the student replying `ext` to a 24h deadline warning, or asking
directly. deadline-guard offers this once per assignment.

**This skill drafts. It never sends.** The student edits it and sends it from
their own address. An email to a professor over a student's name is their
reputation, and it is not yours to spend.

If the Gmail connector is available, [mail-draft](../mail-draft/SKILL.md) puts
the result in their drafts folder — still unsent, still theirs to review. If it
is not, the draft appears here and they copy it. Either way nobody sends
anything but the student.

## Get the facts right first

Pull from the assignment and the RiskScore, and do not write around a gap —
ask. One question, not a form:

- assignment name and the real due date
- how much time they're asking for (**ask; never invent a date**)
- whether they have a reason they want stated (**ask; never invent one**)

If the student won't give a reason, write it without one. "I'm asking for an
extension until Monday" is a complete request. A fabricated illness or family
emergency in an email a professor may check against attendance records is a
serious problem for the student, and generating one on their behalf is a
serious problem full stop.

## Shape

Five sentences, maximum. Subject line that names the course and the ask.

```
Subject: CSE 3901 — extension request, Project 2

Professor {name},

I'm writing to ask for an extension on Project 2, currently due Thursday
11:59pm. Could I have until Monday the 15th?

{one sentence of reason, if the student gave one}

I've got the {specific part} working and need the remaining time for
{specific part}. Happy to talk in office hours Thursday if that's easier.

{Student name}
```

Rules that make it land:

- **Name a specific new deadline.** "A few extra days" reads as unserious and
  makes more email. A date can be answered yes or no.
- **Show one concrete piece of progress.** It separates this from a student who
  hasn't started. Only include it if it's true — ask what they've actually
  done rather than asserting it.
- **Offer office hours.** If office-hours-finder has the time, name it. It
  signals the student will show up.
- No apologising twice. No "I know you're very busy." No paragraph about how
  much they value the course.

## The grade-conversation variant

When the trigger is a target going unreachable rather than a deadline, the ask
is different and the email must not sound like a complaint:

```
Subject: MATH 2153 — question about the rest of the term

Professor {name},

After Midterm 2 I've been working out where I stand and I'd like to make sure
I'm reading the weighting right. Could I stop by office hours Thursday?

I'm mainly trying to figure out what to prioritise for the remaining {n}% of
the grade.

{Student name}
```

Never ask for points back in a draft. Never state the bot's computed numbers as
fact to an instructor — the bot's weighting may be wrong, and being corrected on
arithmetic in the first email loses the conversation. Ask, don't assert.

## Always

End every draft with the same line, outside the email body:

> Read it before you send it, and change anything that isn't true.

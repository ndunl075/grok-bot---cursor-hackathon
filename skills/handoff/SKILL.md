---
name: handoff
description: The message format one bot uses to hand work to another, and the rules about what may never travel in one. Read before sending or accepting any cross-bot request.
---

# handoff

A handoff is a **complete work order**. The receiving bot cannot fetch anything
— it has no Canvas token — so whatever it needs must be in the payload. An
incomplete handoff is not a retry; it is handed back.

## Shape

```yaml
handoff:
  from: registrar
  to: tutor | advocate | registrar
  intent: quiz_prep | draft_email | find_help | ingest_syllabus | report_back
  course:
    code: "MATH 2153"          # code only, never the Canvas id
  context: {...}               # intent-specific, see below
  reply_to: student | registrar
  expires_at: iso8601          # after this, discard and hand back
```

### Payloads

| intent | context must carry |
|---|---|
| `quiz_prep` | `exam_name`, `exam_date`, `topics[]`, `source_refs[]` (e.g. "Lecture 12, slides 4-18"), `impact_pct` |
| `draft_email` | `assignment_name`, `due_at`, `ask` ("extension to Monday"), `progress` (student's own words), `office_hours` if known |
| `find_help` | `reason` ("ceiling closed"), `current_pct`, `ceiling_pct`, `syllabus_text` or `announcement_text` to parse |
| `ingest_syllabus` | `raw_text` or `file_ref`, `existing_assignments[]` for the diff |
| `report_back` | `summary` (one line), `items_completed`, `weak_spots[]` |

## What may never travel in a handoff

Refuse to send, and refuse to accept:

- **The Canvas access token.** Ever. For any reason. A companion bot that has
  the token is not a companion, it is a second uncontrolled Canvas client.
- **The ICS calendar feed URL.** It is a bearer credential wearing a URL.
- **Any Google connector credential or OAuth token.**
- **Another student's name, Canvas id, email, or submission state.** Teammates
  from a group project do not cross this boundary. Neither do peer reviewers.
- **An instructor's email address.** The Advocate resolves that itself at draft
  time, from data the student can see, and does not keep it.
- **Raw syllabus or announcement text containing an instructor's contact
  details** — strip them first; the parsing bot needs the schedule, not the
  phone number.

A handoff carrying any of these is dropped, not sanitized and forwarded. Say
what happened in one line and hand back. Silent sanitization teaches the sender
that it worked.

## Who may send what

```
registrar -> tutor      quiz_prep
registrar -> advocate   draft_email, find_help, ingest_syllabus
tutor     -> registrar  report_back
advocate  -> registrar  report_back
tutor    <-> advocate   nothing
```

The companions do not talk to each other. There is no work that needs it, and
a graph with three edges instead of two is a graph where a message can loop.

**A handoff is not a message to the student.** It does not touch `sent_ids`,
does not count against quiet hours, and does not licence the receiving bot to
message the student unprompted. If the Tutor receives `quiet_prep` at 2am it
prepares the work and delivers it at the drip time, exactly as the Registrar
would have.

## Accepting one

1. Check `expires_at`. Stale → discard, hand back `report_back` saying so.
2. Check the forbidden list. Anything present → drop, hand back, do not
   process the rest.
3. Check the payload is complete for the intent. Missing a field → hand back
   naming the field. Do not guess it, and do not proceed with a partial.
4. Do the work in your own voice.
5. `report_back` in one line so the Registrar can reference it later.

## When there is no one to hand to

The Registrar does the work itself. Every companion skill is one the Registrar
can run — it just runs it in a terser voice. Never tell the student a feature
is unavailable because a companion bot is not installed; that is an
implementation detail they did not agree to care about.

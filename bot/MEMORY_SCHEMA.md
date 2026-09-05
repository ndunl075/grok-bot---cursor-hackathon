# Memory Schema

What the bot may store, in what shape, and what must never be stored.
Canonical field names live in [ARCHITECTURE.md §2](../ARCHITECTURE.md). This
file governs *persistence*: lifetime, size, and template-export behavior.

## Never store

- Anything from another student (group project members' names beyond first
  name + Canvas ID, submission contents, grades).
- Assignment or file *contents* beyond what a StudyItem needs. Store the
  question and answer you generated, not the source PDF.
- Instructor email bodies, private messages, or discussion posts by others.

## Store, with lifetime

| Key | Shape | Lifetime | In template? |
|---|---|---|---|
| `canvas_access_token` | str | until revoked | **NO** |
| `config` | Config | permanent | NO (school-identifying) |
| `courses` | Course[] | refresh 24h | NO |
| `assignments:{course_id}` | Assignment[] | refresh 15m | NO |
| `risk:{course_id}` | RiskScore | recomputed each grade-watch | NO |
| `study_items` | StudyItem[] | until exam + 7d | NO |
| `prefs` | UserPrefs | permanent | defaults only |
| `routine_state:{name}` | `{last_run, sent_ids[]}` | rolling 30d | NO |
| `routine_state:weekly-retro` | `{last_run, snapshot}` | overwritten weekly | NO |
| `groups:{course_id}` | teammate `{id, short_name}` only | until the assignment is graded | **NO — other people's data** |
| `office_hours:{course_id}` | `{day, start, end, location, staff, until?}` | until the term ends | NO |
| `syllabus_candidates` | Assignment[] with `id: null`, `source: "syllabus"` | until matched or term ends | NO |

## Other people's data

`groups:{course_id}` is the only key that holds information about someone other
than the student, and it is the one most likely to leak. Rules:

- Store `id` and `short_name`. Nothing else. Not their grades, not their
  submission times, not their email, not anything from their comments.
- Delete the whole entry when the assignment is graded.
- It never enters a template. `PUBLISH_CHECKLIST.md` has a dedicated step.

calendar-sync stores nothing here: its idempotency key lives in the calendar
event's own `extendedProperties`, which is the right place for it — the mapping
survives a memory wipe and cannot drift out of sync with the calendar.

## Routine state

Each routine owns exactly one key: `routine_state:{name}`.

```yaml
routine_state:deadline-24h:
  last_run: 2026-09-05T15:00:00-04:00
  sent_ids: [assignment_id, ...]     # prune to last 30 days
```

`sent_ids` is the entire dedupe mechanism. A routine that sends without
appending to `sent_ids` will nag, and a bot that nags gets muted. Append
before you send, not after — a send that fails is better than a double-send.

**Delete-safe:** deleting any `routine_state` key must degrade to "sends the
next matching item again," never to a crash or a silent stop.

## Size discipline

Bot memory is not a database. Keep it under a few hundred entries.

- `assignments:{course_id}`: drop anything due more than 14 days ago and
  already graded.
- `study_items`: hard cap 15 per exam, delete the set 7 days after the exam.
- `sent_ids`: prune to 30 days on every routine run.
- `syllabus_candidates`: drop any candidate that has matched a real Canvas
  assignment; the Canvas record supersedes it.
- `routine_state:weekly-retro.snapshot`: one entry per course, overwritten
  weekly. It is a snapshot, not a history — do not accumulate weeks.

## Weight provenance

`Course.weights_source` is load-bearing and must be honest:

- `canvas` — read from `assignment_groups[].group_weight` and the course has
  `apply_assignment_group_weights: true`.
- `user` — the student told you.
- `unknown` — neither. Equal weights assumed, and **every grade number
  derived from it must carry a caveat** until it is resolved.

Never silently promote `unknown` to `canvas`.

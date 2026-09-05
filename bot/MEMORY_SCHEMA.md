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

## Weight provenance

`Course.weights_source` is load-bearing and must be honest:

- `canvas` — read from `assignment_groups[].group_weight` and the course has
  `apply_assignment_group_weights: true`.
- `user` — the student told you.
- `unknown` — neither. Equal weights assumed, and **every grade number
  derived from it must carry a caveat** until it is resolved.

Never silently promote `unknown` to `canvas`.

# Routines for the Registrar

7 routines.

## routines/morning-brief

---
name: morning-brief
schedule: daily at {Config.brief_time}
skill: daily-brief
---

# morning-brief

Runs daily at `Config.brief_time` (default 07:00, student timezone).

1. `canvas-core.list_courses()` — cache is fine, 24h.
2. For each non-ignored course: `list_groups()` (assignments included).
3. `grade-model` → RiskScore per course.
4. `list_announcements(since = last_run)`.
5. `daily-brief` → compose.
6. Send. Always sends — this is the routine the student agreed to receive.

**State:** `routine_state:morning-brief.last_run`.

If Canvas is unreachable, send the brief from cache and label it:
"(from yesterday's data — Canvas isn't responding)". Do not skip the send.
The morning brief is the habit; breaking the habit costs more than stale data.
------------------------------------------------------------------------
## routines/deadline-48h

---
name: deadline-48h
schedule: every 6 hours
skill: deadline-guard
---

# deadline-48h

Every 6h. Window: `unsubmitted AND impact_pct >= 3 AND due within 48h`.

Sends only on new matches. Dedupe against
`routine_state:deadline-48h.sent_ids`.

Respects quiet hours — hold, don't drop.
------------------------------------------------------------------------
## routines/deadline-24h

---
name: deadline-24h
schedule: every 3 hours
skill: deadline-guard
---

# deadline-24h

Every 3h. Window: `unsubmitted AND due within 24h`. No impact floor.

Separate `sent_ids` from deadline-48h — an assignment correctly appears in
both windows, once each.

Re-check `submitted` immediately before sending; the student may have
submitted since the last fetch.

Respects quiet hours — hold, don't drop.
------------------------------------------------------------------------
## routines/grade-watch

---
name: grade-watch
schedule: every 4 hours
skill: grade-model
---

# grade-watch

Every 4h. Recompute RiskScore per course.

**Sends only on a transition:**
- `at_risk` flipped false → true, or true → false
- `current_pct` moved by ≥ 2 points (a grade landed)

Not on state. A course that has been at risk for a week does not generate four
messages a day.

```
CSE 3901: Quiz 4 came back 68. You're at 84 now, floor 71.
```

State: `routine_state:grade-watch` holds the previous `{current_pct, at_risk}`
per course for comparison.
------------------------------------------------------------------------
## routines/announcements

---
name: announcements
schedule: every 2 hours
skill: announcement-digest
---

# announcements

Every 2h. `list_announcements(since = last_run)` across all active courses.

One line per announcement. Flag with `⚠` when the text indicates a
cancellation, a room change, or a due-date change — those are the ones worth
interrupting for, and they should bypass the impact ranking in daily-brief.

Sends only when there are new items. Dedupe by announcement id in `sent_ids`.

Never cached — announcements are the one thing that must be fresh.
------------------------------------------------------------------------
## routines/group-check

---
name: group-check
schedule: every 6 hours
skill: group-project-tracker
---

# group-check

Every 6h. Window: group assignments with `impact_pct >= 5` due within **72h**
whose group submission is still missing.

Wider than deadline-guard's 48h because coordinating three other people takes
days, not hours.

**Precedence:** when this fires for an assignment, deadline-guard stays silent
on that assignment for the same window. Two messages about one deadline is the
failure mode this whole design is built to avoid.

Re-check the group submission immediately before sending — a teammate may have
submitted since the last fetch, and a nudge after that is worse than none.

State: `routine_state:group-check`. Respects quiet hours.
------------------------------------------------------------------------
## routines/weekly-retro

---
name: weekly-retro
schedule: Sunday 18:00
skill: weekly-retro
---

# weekly-retro

Sunday 18:00. Always sends.

Four lines, per `skills/weekly-retro/SKILL.md`:
1. Grade deltas this week, largest absolute move first.
2. Highest-impact item in the next 7 days.
3. At-risk course, or "nothing at risk."
4. One concrete action.

This is the only routine that carries state across weeks: it stores a snapshot
of every course's `{current_pct, floor_pct, ceiling_pct}` at the end of each
run and diffs against it on the next. Write the snapshot **after** composing —
writing it first makes every delta zero, which reads as a broken bot and is
hard to spot because zero is plausible.

Do not let it grow past four lines.
------------------------------------------------------------------------

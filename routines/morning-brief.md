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

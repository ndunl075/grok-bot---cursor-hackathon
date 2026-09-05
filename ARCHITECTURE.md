# Canvas Student Assistant — Grok Bot Architecture

Contest: #GrokBotForStudents. Deadline Sun Sep 6, 11:59pm PST. Judged on engagement, bot quality, creativity.

Ship rule: a working base beats a broken feature pile. Every feature is additive to the base and must degrade to "bot says it can't" rather than breaking anything.

## 0. Non-negotiables (read before writing anything)

1. **Template-portable.** Grok Bot templates carry: instructions, selected memories, skills, routines, first-party integrations. They do NOT carry custom MCP servers, scripts, code, API keys, sessions. Anything that must survive template install lives in `bot/`, `skills/`, `routines/`. Anything under `tools/` is optional extra credit and must not be required.
2. **Zero cost.** No paid services. Canvas REST API + personal access token only. Optional Google Calendar via first-party integration.
3. **Generic Canvas.** No hardcoded school, course names, or IDs. Must work for any `*.instructure.com` or school-hosted Canvas. Setup = Canvas base URL + token.
4. **Proactive first.** The product is the routines. Chat-on-demand is secondary.
5. **Secrets.** Token stored only in bot memory. `PUBLISH_CHECKLIST.md` must be run before exporting the template. Never commit tokens. `.env` is gitignored.
6. **Verify the Grok Bot skill/routine file format against x.ai/bot/guides before writing the first skill.** If format differs from this doc, update this doc, not the other way around.

## 1. Repo layout

```
grokbot-canvas-assistant/
  ARCHITECTURE.md          # this file
  PUBLISH_CHECKLIST.md     # secret-strip + template export steps
  bot/
    INSTRUCTIONS.md        # bot identity, first-run setup flow, tone, rules
    MEMORY_SCHEMA.md       # what the bot is allowed to remember and in what shape
  skills/
    canvas-core/SKILL.md   # API access layer: all other skills call through this
    grade-model/SKILL.md   # weighted grade + risk scoring
    daily-brief/SKILL.md
    deadline-guard/SKILL.md
    announcement-digest/SKILL.md
    study-engine/SKILL.md  # exam-aware quiz generation + spaced repetition
    syllabus-ingest/SKILL.md
    calendar-sync/SKILL.md
    <feature>/SKILL.md     # one folder per parallel feature
  routines/
    morning-brief.md
    deadline-48h.md
    deadline-24h.md
    grade-watch.md
    announcements.md
    study-drip.md
    weekly-retro.md
  tools/                   # OPTIONAL, not in template. Local helper scripts only.
  docs/
    CANVAS_API.md          # endpoints cheat sheet (below, expanded)
    DEMO_SCRIPT.md         # video shot list
  tests/
    fixtures/              # sanitized JSON from Canvas API for offline agent testing
```

## 2. Data model (shared contract — every agent must conform)

All skills read/write these shapes via bot memory. Names are canonical; do not invent parallel structures.

```yaml
Config:
  canvas_base_url: str          # https://osu.instructure.com
  timezone: str                 # America/New_York
  brief_time: "07:00"
  quiet_hours: ["23:00","07:00"]
  calendar_sync: false

Course:
  id: int
  name: str
  code: str                     # CSE 3901
  term: str
  weights_source: "canvas" | "user" | "unknown"
  groups: [{id, name, weight_pct}]

Assignment:
  id: int
  course_id: int
  name: str
  due_at: iso8601 | null
  points_possible: float
  group_id: int
  submitted: bool
  score: float | null
  opened: bool                  # from submission.workflow_state or first-view heuristics
  impact_pct: float             # (points_possible / group_total_points) * weight_pct

RiskScore:                      # per course, recomputed by grade-model
  course_id: int
  current_pct: float
  projected_pct: float          # assumes avg on remaining
  floor_pct: float              # assumes zero on remaining
  at_risk: bool                 # projected < user_target or floor < 60
  drivers: [assignment_id]      # top 3 remaining by impact_pct

StudyItem:
  course_id: int
  source_file_id: int | null
  question: str
  answer: str
  last_seen: iso8601
  misses: int
  next_due: iso8601             # SM-2 lite: 1d, 3d, 7d, 14d; reset on miss

UserPrefs:
  target_grade_pct: {course_id: float}   # default 90
  ignore_courses: [course_id]
  brief_style: "short" | "full"
```

## 3. Skills (interface contracts)

### canvas-core

Single point of Canvas access. All other skills call it, never the API directly.

- `list_courses()` → Course[] (enrollment_state=active, include term)
- `list_assignments(course_id)` → Assignment[] (include submission)
- `list_groups(course_id)` → groups with weights
- `list_announcements(since)`
- `list_modules(course_id)`, `list_files(course_id | module_id)`, `download_file(file_id)`
- `get_enrollments()` → current computed scores
- Handles pagination (`Link` headers, per_page=100), 401 → reprompt token, 403/404 → mark course unavailable, never crash.
- Rate: ≤ 1 req/sec sustained. Cache course list 24h, assignments 15m.

### grade-model

- Input: Course + Assignment[]. Output: RiskScore.
- If `weights_source == unknown`: ask user once per course, store, proceed with equal weights and flag it.
- Must explain itself in one line: "Projected 87, floor 71. Project (25%) is the swing."

### daily-brief

- Composes morning message from RiskScore + due-in-72h + unopened + announcements(24h).
- Max 6 lines short mode. Lead with the highest impact item. Never list everything.

### deadline-guard

- 48h: unopened OR unsubmitted with impact_pct ≥ 3.
- 24h: any unsubmitted. Include "reply 'ext' to draft an extension email."
- Dedupe: never nudge same assignment twice in same window.

### announcement-digest

- New announcements since last run, summarized to one line each, cancelled-class and due-date-change detection flagged with ⚠.

### study-engine

- Trigger: exam/quiz assignment ≥ 10% impact within 10 days.
- Pull files from the module(s) that precede the exam date; fallback to assignment descriptions.
- Generate 15 StudyItems per exam. Drip 1–3/day by `next_due`. Track misses. Day before exam: send weak-spot recap.

### syllabus-ingest

- Input: image or PDF. Output: Assignment[] candidates (no Canvas write). Diff against Canvas; propose only missing items; add to calendar if sync on.

### calendar-sync (optional, first-party Google Calendar)

- Mirror assignments to a dedicated "Canvas" calendar. Idempotent by assignment id in event description.

## 4. Routines

| Routine | Schedule | Calls | Sends only if |
|---|---|---|---|
| morning-brief | daily @ brief_time | daily-brief | always |
| deadline-48h | every 6h | deadline-guard | new matches |
| deadline-24h | every 3h | deadline-guard | new matches |
| grade-watch | every 4h | grade-model | score changed or at_risk flipped |
| announcements | every 2h | announcement-digest | new items |
| study-drip | daily 19:00 | study-engine | items due |
| weekly-retro | Sun 18:00 | grade-model + daily-brief | always |

Rules: respect quiet_hours. Each routine is stateless except last_run + sent_ids in memory. Delete-safe.

## 5. Bot instructions (bot/INSTRUCTIONS.md must cover)

- Identity: concise, proactive, never nags twice about the same thing, speaks in grade impact not lists.
- First run: (1) ask Canvas URL, (2) ask token with exact click path `Account → Settings → + New Access Token`, (3) verify by listing courses, (4) ask brief time + target grade, (5) enable routines, (6) say "I'll text you first from now on."
- Failure mode: if API fails, say what failed and what to paste. Never fabricate grades or deadlines.
- Privacy line: token stays in this bot's memory; not included in shared template.

## 6. Build order and parallelization

### Phase 1 — base (main agent, sequential, must finish first)

1. Read Grok Bot skill/routine format docs. Update this file if needed.
2. `canvas-core` against live API with the owner's token. Write sanitized fixtures to `tests/fixtures/`.
3. `bot/INSTRUCTIONS.md` first-run flow. Test a fresh install end to end.
4. `grade-model` + `daily-brief` + `morning-brief` routine.

**Gate A:** fresh bot, paste token, get a correct morning brief. Nothing else starts until Gate A passes.

### Phase 2 — parallel feature agents (isolated worktrees, one skill folder each)

Each agent: own worktree, own `skills/<name>/`, own `routines/<name>.md`, may only read (not edit) `canvas-core`, `MEMORY_SCHEMA.md`, `ARCHITECTURE.md`. Tests run against `tests/fixtures/`, not live API. PR back to main with a 5-line demo transcript.

| Worktree | Model | Scope |
|---|---|---|
| ft/deadline-guard | Sonnet | deadline-guard + both routines |
| ft/announcements | Sonnet | announcement-digest + routine |
| ft/study-engine | Opus | study-engine + study-drip |
| ft/syllabus-ingest | Opus | syllabus-ingest |
| ft/calendar-sync | Sonnet | calendar-sync |
| ft/weekly-retro | Sonnet | weekly-retro |
| ft/extension-email | Sonnet | draft extension/office-hours emails from RiskScore context |
| ft/office-hours-finder | Sonnet | parse syllabus/announcements for office hours, suggest when at_risk |
| ft/group-project-tracker | Sonnet | detect group assignments, nudge on unsubmitted group members' pieces |
| ft/demo-script | Sonnet | docs/DEMO_SCRIPT.md + LinkedIn post draft |

Merge order: deadline-guard → announcements → study-engine → the rest. Anything not merged by Sun 12:00 is cut from the template and mentioned as "coming" in the post.

### Phase 3 — publish (main agent)

1. Run PUBLISH_CHECKLIST.md (strip token, memories, personal course data).
2. Fresh-account install test. Time it. Target < 60s.
3. Record video per DEMO_SCRIPT.md. Post by Sun 14:00.

## 7. Canvas API cheat sheet (docs/CANVAS_API.md expands this)

Base: `{canvas_base_url}/api/v1`, header `Authorization: Bearer {token}`, `?per_page=100`, follow `Link: rel="next"`.

- `GET /courses?enrollment_state=active&include[]=term&include[]=total_scores`
- `GET /courses/{id}/assignment_groups?include[]=assignments`  ← weights
- `GET /courses/{id}/assignments?include[]=submission&order_by=due_at`
- `GET /courses/{id}/enrollments?user_id=self`  ← current/final score
- `GET /announcements?context_codes[]=course_{id}&start_date=...`
- `GET /courses/{id}/modules?include[]=items`
- `GET /courses/{id}/files`, `GET /files/{id}` → `url` for download
- `GET /users/self/upcoming_events`
- `GET /users/self/todo`

## 8. Definition of done per feature

- Works from fixtures with zero live calls.
- Works on a fresh bot install with only URL + token.
- Fails loudly and gracefully on missing data.
- Sends nothing during quiet hours.
- One-paragraph description + one demo transcript for the post.

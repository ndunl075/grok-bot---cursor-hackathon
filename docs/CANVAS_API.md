# Canvas API — working reference

Endpoint list lives in [ARCHITECTURE.md §7](../ARCHITECTURE.md). This file is
the part that costs you a day if you learn it the hard way.

## Auth and headers

```
Authorization: Bearer {token}
Accept: application/json+canvas-string-ids
```

Token format is `{account_id}~{secret}`, e.g. `1234~aBcD...`. Canvas shows it
once at creation. A leaked token is full read/write as that user — treat it as
a password, and rotate anything that has touched a log.

`json+canvas-string-ids` is not optional. Some instances issue IDs above 2^53,
which silently lose precision as JSON numbers. Request string IDs and compare
IDs as strings everywhere.

## Pagination

Canvas returns a `Link` header:

```
Link: <https://x/api/v1/courses?page=2&per_page=100>; rel="next",
      <...>; rel="last"
```

Follow `rel="next"` until absent. **Do not synthesize `?page=N`** — several
endpoints (submissions, users) paginate by bookmark, and constructed page
numbers will skip records without erroring. `per_page` maxes at 100; asking for
more is silently clamped.

## Rate limiting

Leaky bucket per token. A burst of ~20 is fine; sustained 5/s is not. When you
exceed it you get **`403` with body `403 Forbidden (Rate Limit Exceeded)`** —
not `429`. Do not treat that 403 as an auth failure and clear the token.

Distinguish by body, always:
```
403 + "Rate Limit Exceeded"  -> back off 30s, retry once
403 + anything else          -> genuine permission denial, degrade
```

## The traps

**`due_at` is not the student's due date.** Use `submission.cached_due_date`
when present. Assignment-level `due_at` ignores per-student and per-section
overrides, so a student with an extension gets nagged on the wrong day.

**`score: null` ≠ `score: 0`.** Null means ungraded. Coercing it to zero is the
fastest way to tell a student they're failing when they aren't. Filter on
`workflow_state == "graded"`, don't test the score.

**`apply_assignment_group_weights` decides whether weights exist.** When it is
`false`, `group_weight` is still populated — usually with `0.0`, sometimes with
stale values from a previous term. Reading it anyway is how you produce a
confidently wrong grade. Gate on the boolean.

**Group weights need not sum to 100.** Canvas permits it. Normalize, and flag
it, because it usually means the instructor made a mistake worth asking about.

**There is no "student opened this assignment" signal.** `submission.read_state`
is whether they read *their grade*. `unread` on an ungraded submission means
nothing. Any feature specified on "unopened" needs redesigning — see
`skills/deadline-guard/SKILL.md`.

**`/courses/{id}/files` 404s constantly.** Instructors disable the Files tab.
It is a normal state, not an error. Fall back to `modules?include[]=items` and
filter `type == "File"`.

**Announcements need `context_codes[]`**, repeated per course
(`context_codes[]=course_1101&context_codes[]=course_1102`), and the list is
capped around 10 per request. Chunk it.

**`enrollments[].computed_current_score` is your test oracle.** It is Canvas's
own weighted math. If your `current_pct` disagrees by more than ~2 points, you
are wrong, not Canvas. `tools/grade_model_ref.py` asserts this against the
fixtures and currently reports drift 0.0 on both weighted and unweighted
courses.

## Endpoints that look useful and aren't

- `/users/self/todo` — only ungraded *submissions awaiting the teacher*, plus
  quizzes. It is not a student to-do list. Misleading name.
- `/users/self/upcoming_events` — 7-day horizon, calendar events only, drops
  assignments without a calendar entry. Fine as a cross-check, useless as a
  source of truth.
- `/courses/{id}/analytics/*` — teacher-scoped on most instances. Expect 403.

## Test without burning a token

```
GET /users/self          -> smoke test, cheapest possible call
GET /courses?enrollment_state=active
```

If `/users/self` returns 401, the token is dead.

**If it returns HTML, the base URL is wrong and no token will fix it.** Three
causes, in rough order of likelihood:

1. You are hitting the web app rather than the API — a missing `/api/v1`.
2. A school SSO redirect is serving a login page.
3. The instance is decommissioned. `canvas.instructure.com` — Instructure's
   old Free-for-Teacher host — now serves a static "Free for Teacher is
   discontinued" page, so it is useless as a test target and looks like a
   client failure when it is really a dead server.

Detect this by sniffing the first non-whitespace byte for `<` before parsing
JSON, which is what `canvas-core` and `tools/canvas_smoke.py` both do. Reporting
"invalid JSON" here sends the student hunting for a token problem they do not
have.

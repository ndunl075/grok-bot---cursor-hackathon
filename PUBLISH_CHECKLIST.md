# Publish Checklist

Run top to bottom before exporting the template. Do not skip the greps.

## 1. Strip secrets from the bot

- [ ] Open bot memory. Delete the `canvas_access_token` entry.
- [ ] Delete `canvas_base_url` if it names your school.
- [ ] Delete every `Course` memory (names, codes, IDs are personally identifying).
- [ ] Delete every `Assignment`, `RiskScore`, and `StudyItem` memory.
- [ ] Delete routine state: `last_run`, `sent_ids`, and
      `routine_state:weekly-retro.snapshot`.
- [ ] **Delete every `groups:{course_id}` entry.** These hold other students'
      names and Canvas ids. They are not yours to share, and a template is a
      public artifact. This is the one step on this list with someone else's
      privacy attached to it.
- [ ] Delete `office_hours:{course_id}` (instructor names and room numbers) and
      `syllabus_candidates`.
- [ ] Keep: `UserPrefs` defaults only if generic (target 90, brief_style short).

## 2. Strip secrets from the repo

```bash
grep -rInE '[0-9]{4}~[A-Za-z0-9]{20,}' . --exclude-dir=.git   # Canvas token shape
grep -rInE '\.instructure\.com' . --exclude-dir=.git --exclude=ARCHITECTURE.md
grep -rIn 'Bearer [A-Za-z0-9]' . --exclude-dir=.git
grep -rInE 'feeds/calendars/user_' . --exclude-dir=.git       # ICS feed is a credential too
git status --porcelain --ignored tests/fixtures/live/         # captures must stay uncommitted
```

All three must return nothing but doc placeholders. A Canvas token looks like
`1234~aBcD...` — the digits before the tilde are the account ID.

- [ ] `git log -p | grep -E '[0-9]{4}~[A-Za-z0-9]{20,}'` returns nothing.
      If it does not: the token is in history. Rotate it in Canvas
      (Account → Settings → delete the token) before doing anything else.

## 3. Select what the template carries

Templates carry instructions, selected memories, skills, routines, and
first-party integrations. They do not carry MCP servers, scripts, or keys.

- [ ] Instructions: include.
- [ ] Skills: include all of `skills/`.
- [ ] Routines: include all of `routines/`.
- [ ] Memories: include **none**. The first-run flow rebuilds them.
- [ ] Integrations: declare Google Calendar only if calendar-sync shipped. The
      declaration travels; the authorization does not. Whoever installs connects
      their own account, so say that in the description rather than letting sync
      silently no-op for them.

## 3b. If you are publishing companions

Each bot is a separate template. Export them separately and check each.

- [ ] **Registrar:** token stripped, per §1. It is the only one that ever had one.
- [ ] **Tutor / Advocate:** confirm no Canvas token is in memory at all. If one
      is, something violated the handoff rules and the token must be rotated,
      not just deleted.
- [ ] Companion memories hold no course names, no teammate names, no instructor
      addresses. They should hold study items and drafts only, and those go too.
- [ ] Each companion's description says it requires the Registrar. Installed
      alone they do nothing, and an installer should learn that before they
      install, not after.

## 4. Fresh-install test

- [ ] Install the template on a second account with no prior state.
- [ ] Time from install to first correct brief. Target < 60s. Record the number.
- [ ] Confirm the bot asks for URL and token and does not assume either.
- [ ] **Install the Registrar alone and confirm every feature still works** —
      quizzing, email drafting, syllabus reading. Companions are additive; if
      anything is missing without them, rule 3 in `bots/README.md` is broken.
- [ ] Confirm no course name from your account appears anywhere.

## 5. Rotate

- [ ] Delete the access token you developed with. Issue a fresh one for daily use.
      Assume any token that touched a terminal, a log, or a chat is burned.

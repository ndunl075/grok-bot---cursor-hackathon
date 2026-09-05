# Publish Checklist

Run top to bottom before exporting the template. Do not skip the greps.

## 1. Strip secrets from the bot

- [ ] Open bot memory. Delete the `canvas_access_token` entry.
- [ ] Delete `canvas_base_url` if it names your school.
- [ ] Delete every `Course` memory (names, codes, IDs are personally identifying).
- [ ] Delete every `Assignment`, `RiskScore`, and `StudyItem` memory.
- [ ] Delete routine state: `last_run`, `sent_ids`.
- [ ] Keep: `UserPrefs` defaults only if generic (target 90, brief_style short).

## 2. Strip secrets from the repo

```bash
grep -rInE '[0-9]{4}~[A-Za-z0-9]{20,}' . --exclude-dir=.git   # Canvas token shape
grep -rInE '\.instructure\.com' . --exclude-dir=.git --exclude=ARCHITECTURE.md
grep -rIn 'Bearer [A-Za-z0-9]' . --exclude-dir=.git
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
- [ ] Integrations: include Google Calendar only if calendar-sync shipped.

## 4. Fresh-install test

- [ ] Install the template on a second account with no prior state.
- [ ] Time from install to first correct brief. Target < 60s. Record the number.
- [ ] Confirm the bot asks for URL and token and does not assume either.
- [ ] Confirm no course name from your account appears anywhere.

## 5. Rotate

- [ ] Delete the access token you developed with. Issue a fresh one for daily use.
      Assume any token that touched a terminal, a log, or a chat is burned.

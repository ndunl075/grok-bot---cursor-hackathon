# Canvas Student Assistant — Grok Bot

A proactive Canvas bot that texts you first. It knows what's due, what it's
worth, and what it does to your grade, and it says something only when the
answer changes.

The thing it does that Canvas won't: it computes the best grade you can still
reach. Canvas shows you the grade you have. It never tells you that the midterm
two weeks ago already closed off the A.

**Demo:** open `docs/demo/index.html` in a browser.

## Start here

When you sit down, in this order:

1. **Answer the blocking question.** Open your Grok Bot and ask it to
   `GET https://canvas.instructure.com/api/v1/courses` with a junk bearer
   token. A `401` back from Canvas means skills can reach arbitrary hosts and
   `canvas-core` works as written. Anything else means read
   [`skills/canvas-core/NO_HTTP_FALLBACK.md`](skills/canvas-core/NO_HTTP_FALLBACK.md)
   and pick a tier. Nothing downstream is settled until this is.
2. **Verify the Canvas side.** `python3 tools/canvas_smoke.py https://yourschool.instructure.com`
   Token input is hidden and never stored. Add `--fixtures` to capture your own
   sanitized responses into the gitignored `tests/fixtures/live/`.
3. **Install the bot.** Paste `bot/INSTRUCTIONS.md` as the instructions, add
   every `skills/*/SKILL.md`, add every `routines/*.md`.
4. **Run [`PUBLISH_CHECKLIST.md`](PUBLISH_CHECKLIST.md) before exporting the
   template.** It has the greps that catch a committed token.
5. **Record per [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).**

## What's here

| | |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | The build contract. Data model, phases, what shipped and what was cut. |
| `bot/` | Identity, first-run flow, failure modes; and the memory persistence contract. |
| `skills/` | canvas-core, grade-model, daily-brief, deadline-guard, announcement-digest, study-engine. |
| `routines/` | All seven, with dedupe and quiet-hours semantics. |
| [`docs/CANVAS_API.md`](docs/CANVAS_API.md) | The Canvas gotchas that each cost a day. |
| `docs/demo/` | Animated walkthrough, built for screen capture. |
| `tests/fixtures/` | Canvas responses covering weighted and unweighted courses, a 403 course, a 404 endpoint, and eight announcements chosen to break a naive classifier. |
| `tools/` | Local only. Never ships in the template. |

## Verifying

Both run offline against fixtures, no token, no network:

```bash
python3 tools/grade_model_ref.py    # grade math, reconciled against Canvas's own score
python3 tools/verify_skills.py      # deadline windows, dedupe, quiet hours, classifier, exam sourcing
```

`grade_model_ref.py` currently reports **drift 0.0** against Canvas's
`computed_current_score` on both a weighted and an unweighted course.
`verify_skills.py` is **30/30**.

## What ships in the template

`bot/INSTRUCTIONS.md`, everything in `skills/`, everything in `routines/`.
Nothing in `tools/` or `tests/`.

Built for #GrokBotForStudents.

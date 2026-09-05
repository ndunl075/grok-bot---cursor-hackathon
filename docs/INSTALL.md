# Install

Everything you paste lives in [`dist/`](../dist/), generated from the repo by
`tools/build_template.py`. Read those files on GitHub and copy from them; you
do not need to clone anything.

## Before you start: one test that decides the shape of this

Open your Grok Bot and ask it, verbatim:

> Make a GET request to `https://canvas.instructure.com/api/v1/courses` with
> the header `Authorization: Bearer 1234~notarealtoken` and tell me the exact
> HTTP status code and response body you get back.

| What comes back | What it means | What to do |
|---|---|---|
| **401**, with a body about invalid access token | The bot can make authenticated requests to arbitrary hosts. Everything here works as written. | Continue below. |
| "I can't make web requests" / it describes rather than does | No outbound HTTP. `canvas-core` cannot work as designed. | Read [`skills/canvas-core/NO_HTTP_FALLBACK.md`](../skills/canvas-core/NO_HTTP_FALLBACK.md) and pick a tier before installing. |
| A prompt to connect an integration | Requests are connector-mediated. Method contracts hold; the transport differs, and the connector will not travel in a shared template. | Continue, and say so in the template description. |
| **200** with real course data | Something is very wrong — that token is fake. Stop and work out what answered. | Do not proceed. |

A 401 *from Canvas* is the success case. An error *from the bot* is the
failure case. They are easy to confuse when skimming.

## 1. The Registrar

This is the product. Installed alone it does everything.

1. **Instructions** — paste [`dist/registrar/INSTRUCTIONS.md`](../dist/registrar/INSTRUCTIONS.md).
2. **Skills** — [`dist/registrar/SKILLS.md`](../dist/registrar/SKILLS.md) holds
   16 blocks separated by horizontal rules. Paste each as a **separate skill**.
   Pasting the file as one skill will appear to work and will behave badly.
3. **Routines** — [`dist/registrar/ROUTINES.md`](../dist/registrar/ROUTINES.md),
   7 of them, same rule.
4. Start a chat. It asks for your Canvas URL, then your token. It verifies by
   listing your courses before it asks anything else.

If step 4 does not list your real courses, stop. Everything downstream is
built on that call succeeding.

## 2. Companions (optional, later)

Do not install these on day one. Live with the Registrar first and add a
companion when you notice you want it.

- **Tutor** — [`dist/tutor/`](../dist/tutor/). Add it if the study drip is the
  part you want more of. It quizzes in a longer, more patient voice than the
  Registrar can.
- **Advocate** — [`dist/advocate/`](../dist/advocate/). Add it the first time
  you actually need to email a professor.

Then put whichever you installed into one group chat with the Registrar so
handoffs do not need you to relay them.

**Neither companion asks for a Canvas token, and neither should ever be given
one.** They have no API access by design — see
[`bots/README.md`](../bots/README.md).

## 3. Connectors (optional)

All three are optional and every feature has a path without them.

| Connector | Bot | Gets you | Without it |
|---|---|---|---|
| Google Calendar | Registrar | Deadlines in a `Canvas` calendar | Deadlines in the morning brief |
| Gmail | Advocate | Extension emails as **drafts** | The draft in the chat |
| Google Drive | Tutor / Advocate | Study guides saved, syllabi read | Both in the chat |

Gmail is draft-creation only. Nothing in this bot can send mail.

## 4. Before you share it

Run [`PUBLISH_CHECKLIST.md`](../PUBLISH_CHECKLIST.md) in full. It catches a
committed token, other students' names in memory, and includes an adversarial
pass that confirms the bot ignores instructions planted in a Canvas
announcement.

## Rebuilding dist/

After changing any skill, routine, or instruction file:

```bash
python3 tools/build_template.py           # regenerate
python3 tools/verify_skills.py            # 130 checks, incl. dist/ freshness
```

The build refuses to run if anything token-shaped is in the output.

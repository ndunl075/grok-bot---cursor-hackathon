---
name: connector-core
description: The contract every connector-backed skill follows — how to declare a connector, probe whether it is actually authorized, and degrade when it is not. Read before using Google Calendar, Gmail, Drive, or any other first-party integration.
---

# connector-core

Every skill that touches something outside Canvas goes through this contract.
It exists because of one fact that breaks naive connector code:

> **A template carries a connector *declaration*, not an *authorization*.**

When someone installs this bot from a template, the template says "this bot
uses Google Calendar." It does not, and cannot, hand them your Google account.
They connect their own, or they don't connect anything. So every connector is
in one of three states at any moment, and a skill that assumes state 3 will
silently do nothing for most of its users.

## The three states

| State | Meaning | What the skill does |
|---|---|---|
| `absent` | Not declared by this bot at all | Feature does not exist. Never mention it. |
| `declared` | Declared, not authorized by this user | Feature is offered, inert. Say so **once**, when it would first have been useful. |
| `connected` | Declared and authorized | Full behaviour. |

Probe once per session, cache the result for the session, and re-probe on the
first failure rather than on a schedule. Store nothing about connector state in
long-term memory — it changes when the user revokes access, and a stale
"connected" produces a skill that reports success while doing nothing.

## The rule that matters most

**A missing connector must never block a Canvas feature.**

Calendar sync failing cannot stop the morning brief. Gmail being unconnected
cannot stop an extension email from being drafted — it changes where the draft
goes, not whether it exists. Every connector-backed skill has a no-connector
path that still delivers the value, and that path is the default, not the
fallback.

```
value = the thing the student wanted
connector = a nicer delivery mechanism for it
```

If you cannot state the no-connector path in one sentence, the skill is
designed wrong.

| Skill | With connector | Without |
|---|---|---|
| calendar-sync | Events in a `Canvas` calendar | Deadlines in the morning brief, as always |
| mail-draft | Draft sitting in Gmail | Draft in the chat, student copies it |
| drive-archive | Study guide saved to Drive | Study guide in the chat |

## Saying it once

When a connector is `declared` but not `connected`, tell the student at the
moment it would first have helped — not at setup, when they have no context
for the offer:

> I can put these on a Google Calendar if you connect one. Setup → Connectors.
> Either way I'll keep telling you here.

Then never again for that connector, unless they ask. A bot that reminds you
weekly about an integration you declined is an advertisement.

Store `connector_prompted: [name]` so the once is actually once. That is the
only connector state worth persisting, and it is about your own behaviour, not
about the connector.

## Failure

A connector call that fails mid-run is not an error the student needs to see,
unless it was the thing they just asked for.

- **Unprompted work** (a routine syncing the calendar): log it, keep going,
  do not message. Retry next run.
- **Requested work** ("put this on my calendar"): say what failed in one line
  and give them the value anyway. "Couldn't reach Google Calendar just now —
  here's the deadline: Thursday 11:59pm. I'll try again on the next pass."

`401`/revoked → drop to `declared`, tell them once, stop trying until they
reconnect. Retrying a revoked token every four hours forever is how a bot ends
up rate-limited and useless.

## Adding a connector

1. Declare it in the template description, so an installer knows before
   they install.
2. Write the no-connector path first. If it isn't good on its own, stop.
3. Probe, don't assume.
4. Add it to the table in `PUBLISH_CHECKLIST.md` §3.
5. Never let it hold data Canvas already holds. A connector is an output
   surface, not a second source of truth — two sources disagree, and then the
   bot has to guess which is right.

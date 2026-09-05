# The roster

Three bots. **One of them is the product; two are optional.** Install the
Registrar and you have a complete, working Canvas assistant. Add the others
only if you want them.

| Bot | Required | Holds the Canvas token | Speaks first |
|---|---|---|---|
| **Registrar** | yes | **yes, only it** | yes, only it |
| **Tutor** | no | no | no |
| **Advocate** | no | no | no |

## The four rules that make this work instead of making it worse

Multi-bot is usually a downgrade: N bots hitting the same API, N caches that
disagree, N sets of `sent_ids`, and a student getting nudged three times about
one deadline. These four rules are what stop that, and none of them is
optional.

**1. Exactly one bot talks to Canvas.** The Registrar holds the token and is
the only Canvas client. The Tutor and the Advocate never see it, never call the
API, and cannot — they receive everything they need in a
[handoff](../skills/handoff/SKILL.md) and cannot fetch more. One client means
one cache, one rate limit, and one version of the truth.

**2. Exactly one bot speaks first.** Every routine, every nudge, every morning
brief comes from the Registrar. It owns all `sent_ids`, so dedupe stays a
single-writer problem instead of a distributed one. The Tutor and the Advocate
speak only when engaged — by the student, or by a handoff the student can see.

**3. Companions are additive, never load-bearing.** With no Tutor installed,
the Registrar runs study-engine itself. With no Advocate, it drafts the email
itself. Nothing breaks, nothing is missing, the voice is just less specialised.
Setup stays a URL and a token.

**4. No credentials and no third parties in a handoff.** Never the token, never
the ICS feed URL, never a teammate's name, never an instructor's address. The
handoff protocol enforces this and `tools/verify_skills.py` asserts it.

## So why bother

One honest reason: **the Registrar's voice and the Tutor's voice are
incompatible, and forcing them into one bot makes both worse.**

The Registrar is terse and factual. Six lines, lead with impact, never explain
twice. That is correct for a 7am lock screen and wrong for someone stuck on the
chain rule at 11pm, who needs patience, a worked example, and a second attempt
at the explanation. One instruction set cannot hold "never use more than six
lines" and "keep going until they understand."

The Advocate is a third register again: careful, formal, writing to an adult
with authority over the student's grade. That is not the voice you want
composing a morning brief, and the brief's voice is not one you want emailing
a professor.

Splitting on **voice** is the case for this. Splitting on *workload* is not —
the work here is not parallel, and pretending otherwise is where multi-bot
setups go wrong.

## Install order

1. **Registrar.** Paste the Canvas URL and token. You now have the product.
2. Live with it for a few days. If the study drip is the part you want more
   of, add the **Tutor**.
3. Add the **Advocate** the first time you actually need to email a professor.

Then put whichever you installed in one group chat, so handoffs don't need you
to relay them.

## A known unknown

The handoff protocol is deliberately **transport-agnostic**. It works if bots
can message each other in a group chat, and it also works if the student pastes
a handoff from one chat into another, and it degrades to the Registrar doing
the work alone.

That is not over-engineering. It is because the group-chat mechanics have not
been verified against the platform docs from this environment, and a protocol
that assumes a transport it turns out not to have is a protocol that has to be
rewritten. Confirm the mechanics before relying on automatic handoff, and note
that nothing above breaks if it turns out the student has to relay.

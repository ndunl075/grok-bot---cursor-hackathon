---
name: mail-draft
description: Puts a drafted email into the student's Gmail drafts folder instead of the chat, so they can edit and send it from their own account. Never sends. Use after extension-email has written something.
---

# mail-draft

A delivery surface for [extension-email](../extension-email/SKILL.md). It does
not write the email; it moves a written one somewhere better than a chat
bubble. Follows [connector-core](../connector-core/SKILL.md).

**No-connector path:** the draft appears in the chat and the student copies it.
That is the default behaviour and it is fine. This connector saves a
copy-paste, nothing more, and it must never be the difference between the
student getting an email and not getting one.

## It creates drafts. It does not send.

There is one hard invariant in this skill and it has no exceptions:

> **Never call send. Only ever create a draft.**

Not when the student says "just send it." Not when they said "always send" last
week. Not on a routine. An email to a professor over a student's name is their
reputation, and a bot that can send it is one hallucinated recipient away from
a real problem the student cannot take back.

When they ask you to send, say what you did instead:

> It's in your drafts — subject "CSE 3901 — extension request". Give it a read
> and hit send yourself.

That is not friction to apologise for. It is the feature.

## Finding the recipient

```
GET /courses/{id}/users?enrollment_type[]=teacher&include[]=email
GET /courses/{id}/users?enrollment_type[]=ta&include[]=email
```

Many instances do not expose `email` to students. That is common and not an
error.

- **Address found** → prefill `to`. Say whose address it is, so a mistake is
  visible before it is sent: "drafted to Prof. {last name} ({address})".
- **No address** → create the draft with `to` **empty** and say so:
  "I couldn't get their address from Canvas — the draft's in Gmail, add the
  recipient before you send."

**Never guess an address.** Not `firstname.lastname@school.edu`, not a pattern
copied from another course, not one inferred from the institution's domain. A
guessed address either bounces or reaches the wrong person, and reaching the
wrong person with a student's grade situation is a privacy incident.

When a course has multiple teachers, ask which one rather than picking. Two
teachers usually means a lecturer and a coordinator, and the student knows
which one owns extensions.

## The draft

Subject and body come from extension-email unchanged. Add nothing — no
signature you invented, no "Sent from", no bot attribution. The email must read
as though the student wrote it, because they are about to be responsible for
every word in it.

Set the draft and stop. Do not label it, star it, or move it. It is the
student's mailbox.

## Privacy

The instructor's address is another person's data.

- Use it for the draft. Do not store it.
- Never repeat it into the chat beyond the one confirmation line above.
- Never use it for anything the student did not just ask for.
- Gmail read scope, if the connector grants it, is not used by this skill at
  all. It writes one draft. It does not read the student's mail, search their
  inbox, or check whether the professor replied — none of which is this bot's
  business, and all of which a student would be alarmed to discover.

## Failure

Draft creation failing is a delivery problem, never a loss of work:

> Gmail didn't take the draft. Here it is — copy it from the chat.

Then print the email. The student asked for an email and they get one.

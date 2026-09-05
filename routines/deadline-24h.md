---
name: deadline-24h
schedule: every 3 hours
skill: deadline-guard
---

# deadline-24h

Every 3h. Window: `unsubmitted AND due within 24h`. No impact floor.

Separate `sent_ids` from deadline-48h — an assignment correctly appears in
both windows, once each.

Re-check `submitted` immediately before sending; the student may have
submitted since the last fetch.

Respects quiet hours — hold, don't drop.

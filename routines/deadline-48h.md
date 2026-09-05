---
name: deadline-48h
schedule: every 6 hours
skill: deadline-guard
---

# deadline-48h

Every 6h. Window: `unsubmitted AND impact_pct >= 3 AND due within 48h`.

Sends only on new matches. Dedupe against
`routine_state:deadline-48h.sent_ids`.

Respects quiet hours — hold, don't drop.

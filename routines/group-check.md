---
name: group-check
schedule: every 6 hours
skill: group-project-tracker
---

# group-check

Every 6h. Window: group assignments with `impact_pct >= 5` due within **72h**
whose group submission is still missing.

Wider than deadline-guard's 48h because coordinating three other people takes
days, not hours.

**Precedence:** when this fires for an assignment, deadline-guard stays silent
on that assignment for the same window. Two messages about one deadline is the
failure mode this whole design is built to avoid.

Re-check the group submission immediately before sending — a teammate may have
submitted since the last fetch, and a nudge after that is worse than none.

State: `routine_state:group-check`. Respects quiet hours.

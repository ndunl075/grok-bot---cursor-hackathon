---
name: study-drip
schedule: daily at 19:00
skill: study-engine
---

# study-drip

Daily 19:00. Send `StudyItem`s where `next_due <= now`, capped at 3.

Sends nothing if no items are due. Sends nothing if there is no qualifying
exam in the next 10 days.

Two consecutive ignored drips → halve frequency and say so once.

The day-before-exam recap fires from this routine too, and takes precedence
over the regular drip.

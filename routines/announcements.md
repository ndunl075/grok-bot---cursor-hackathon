---
name: announcements
schedule: every 2 hours
skill: announcement-digest
---

# announcements

Every 2h. `list_announcements(since = last_run)` across all active courses.

One line per announcement. Flag with `⚠` when the text indicates a
cancellation, a room change, or a due-date change — those are the ones worth
interrupting for, and they should bypass the impact ranking in daily-brief.

Sends only when there are new items. Dedupe by announcement id in `sent_ids`.

Never cached — announcements are the one thing that must be fresh.

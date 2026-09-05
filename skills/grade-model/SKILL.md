---
name: grade-model
description: Computes weighted course grades and risk. Turns raw Canvas assignments into current, floor, and ceiling percentages, works out the average still needed to hit a target, detects when a target has become unreachable, and ranks remaining work by how much it actually moves the grade. Use whenever a grade, a projection, or "what should I do first" is needed.
---

# grade-model

Input: `Course` + `Assignment[]` from canvas-core. Output: one `RiskScore`.

This is the skill that makes the bot worth having. Everything else reports
Canvas back to the student. This tells them something Canvas won't.

## The three numbers

**`current_pct`** — the grade right now, graded work only.

```
for each group g with weight w_g:
    earned_g  = Σ score        over graded assignments in g
    possible_g = Σ points_possible over graded assignments in g
    if possible_g == 0: skip g and redistribute w_g proportionally
    current = Σ (earned_g / possible_g) * w_g  /  Σ w_g   (over non-skipped groups)
```

Skipping empty groups and renormalizing is what Canvas itself does. Forgetting
to renormalize is the single most common way to be wrong by 15 points.

**`floor_pct`** — assumes zero on everything remaining. This is the number that
changes behavior. "You have an 87" is comfortable. "Your floor is 61" is not.

```
floor = Σ (earned_g / group_total_g) * w_g       # over ALL groups, no renormalize
```

**`ceiling_pct`** — assumes 100% on everything remaining. The best grade still
mathematically available.

```
headroom = Σ ((group_total_g - graded_possible_g) / group_total_g) * w_g
ceiling  = floor + headroom
```

> **`projected_pct` was removed from the model.** As specified in
> ARCHITECTURE.md — "assumes average on remaining" — it is a tautology: extend
> each group's own graded rate over that group's remaining points and you get
> back exactly `current_pct`, every time. Verified in
> `tools/grade_model_ref.py`; it printed the same number for both on every
> fixture. A number that never differs from another number is not a
> projection, it is a second label for the same value. `ceiling` and `needed`
> replace it, and they are the two that change what a student does today.

## Ungraded ≠ zero

`score == null` means not yet graded. It does **not** mean zero and must never
enter `current_pct`. The only assignments that count as zero are ones past due
with `submitted == false` and `workflow_state == 'unsubmitted'` — and even then,
only after the late window, which you can't see. Prefer to leave them out of
`current` and let `floor` carry the warning.

## impact_pct

```
group_total = Σ points_possible for all assignments in the group
impact_pct  = (points_possible / group_total) * group_weight
```

This is the whole point. A 100-point homework in a 1000-point homework group
worth 20% is worth **2 points of final grade**. A 40-point quiz in an 80-point
quiz group worth 30% is worth **15**. Points possible is a lie; impact is not.

Rank remaining work by `impact_pct` descending. `drivers` is the top 3.

## needed — the number that ends arguments

```
needed = (target_grade_pct - floor_pct) / headroom_pct * 100
```

The average the student must earn on **all remaining work** to land their
target. This is the single most useful output of this skill.

- `needed <= 100` → actionable. "You need 84% on what's left to keep the A."
- `needed > 100` → **the target is gone.** Say so, plainly, once:

  > An A in CSE 3901 isn't reachable anymore — your ceiling is 89.8. A 90 on
  > Project 2 lands you at 89.3. Want me to aim at the A- instead?

  Canvas will never tell a student this. It is the reason to install the bot.
  Deliver it early enough to matter and never more than once per course, and
  always pair it with the next reachable target rather than leaving them
  with only bad news.

## at_risk

```
at_risk = (ceiling_pct < target_grade_pct) OR (floor_pct < 60)
```

Cross the flag, don't cross it twice — grade-watch only notifies on a
*transition*, not on the state.

## weights_source == unknown

Do not silently assume equal weights and report a confident number.

1. First encounter: ask once. "MATH 2153 doesn't publish its grade weights.
   Roughly what's the split — homework / exams / final?"
2. Store the answer, set `weights_source = user`.
3. Until answered, compute with equal weights **and label every number**:
   "≈84 (assuming equal weights — tell me the real split)".

## Self-check against Canvas

canvas-core exposes Canvas's own `current_score`. Compare.

- Within 2 points → you're right, say nothing.
- Off by more → your weights or your group handling is wrong. Report Canvas's
  number, not yours, and say: "My weighting is off for {course} — Canvas says
  {x}. Can you check the syllabus split?"

A bot that confidently reports a wrong grade is worse than no bot.

## Output format

One line. Always one line. The student is reading it on a lock screen.

> You're at 87, floor 61. Project 2 (25%) is the swing.

Structure: `You're at {current}, floor {floor}. {top driver} ({impact}%) is
the swing.`

When the target has become unreachable, that line replaces this one — it is
strictly more important than the floor.

If not at risk and nothing changed, produce nothing at all. Silence is a
feature.

#!/usr/bin/env python3
"""Fixture-driven checks for the skills' decision logic.

Local-only; does not ship in the template. Every skill claims in its
"definition of done" that it works from tests/fixtures with zero live calls.
This asserts that claim for the parts that are decidable: deadline-guard's
windows and dedupe, announcement-digest's classifier (including the
false-positive guards), and study-engine's module sourcing.

Usage: python3 tools/verify_skills.py
Exit 0 if every case passes.
"""
import json, pathlib, re, sys
from datetime import datetime, timedelta, timezone

FIX = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
ET = timezone(timedelta(hours=-4))            # fixtures are Fall 2026, EDT
load = lambda n: json.loads((FIX / n).read_text())
iso = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))

results = []
def check(group, name, got, want):
    results.append((group, name, got == want, got, want))


# ── deadline-guard ────────────────────────────────────────────────────────
def impacts():
    out = {}
    for g in load("assignment_groups_1101.json"):
        total = sum(float(a["points_possible"]) for a in g["assignments"])
        for a in g["assignments"]:
            out[a["id"]] = dict(
                name=a["name"], due=iso(a["due_at"]),
                submitted=a["submission"]["workflow_state"] in
                          ("submitted", "graded", "pending_review"),
                impact=float(a["points_possible"]) / total * float(g["group_weight"]))
    return out


def guard(now, window_h, floor, sent_ids=()):
    """The rule as written in skills/deadline-guard/SKILL.md."""
    hits = []
    for aid, a in impacts().items():
        if a["submitted"] or aid in sent_ids:
            continue
        hours = (a["due"] - now).total_seconds() / 3600
        if 0 < hours <= window_h and a["impact"] >= floor:
            hits.append(a["name"])
    return sorted(hits)


def in_quiet_hours(now, start="23:00", end="07:00"):
    h = now.astimezone(ET).time()
    s, e = [datetime.strptime(x, "%H:%M").time() for x in (start, end)]
    return h >= s or h < e                    # window wraps midnight


TUE = iso("2026-09-08T11:00:00Z")             # Tue 07:00 ET
WED = iso("2026-09-09T11:00:00Z")
THU = iso("2026-09-10T11:00:00Z")
LATE = iso("2026-09-10T07:00:00Z")            # Thu 03:00 ET

check("deadline-guard", "48h window is empty Tue morning (P2 is 65h out)",
      guard(TUE, 48, 3), [])
check("deadline-guard", "48h window catches Project 2 on Wed",
      guard(WED, 48, 3), ["Project 2: Rails API"])
check("deadline-guard", "24h window catches Project 2 on Thu",
      guard(THU, 24, 0), ["Project 2: Rails API"])
check("deadline-guard", "HW5 (4.0%) clears the 3% floor when it comes into range",
      guard(iso("2026-09-15T11:00:00Z"), 48, 3), ["HW5"])
check("deadline-guard", "a 2% floor would still exclude nothing here",
      guard(iso("2026-09-15T11:00:00Z"), 48, 5), [])
check("deadline-guard", "dedupe suppresses an already-sent assignment",
      guard(WED, 48, 3, sent_ids={"20102"}), [])
check("deadline-guard", "graded/submitted work never nudges",
      "Midterm" in " ".join(guard(THU, 24, 0)), False)
check("deadline-guard", "03:00 ET is inside quiet hours (hold, do not drop)",
      in_quiet_hours(LATE), True)
check("deadline-guard", "07:00 ET is outside quiet hours",
      in_quiet_hours(THU), False)


# ── announcement-digest ───────────────────────────────────────────────────
NEG   = re.compile(r"\b(?:not|isn'?t|is not|no longer|never)\b", re.I)
PAST  = re.compile(r"\b(?:last week'?s|previously|the previous|earlier)\b", re.I)
DUEW  = re.compile(r"\b(?:due|deadline)\b", re.I)
MOVED = re.compile(r"\b(?:moved|extended|pushed|postponed|now due|new deadline|instead of)\b", re.I)
SCHED = re.compile(r"\b(?:cancel\w*|no class|no lecture|not meeting|relocated|room change|rescheduled|moved to)\b", re.I)
GRADED= re.compile(r"\b(?:grades?)\b.{0,30}\b(?:posted|released|available)\b", re.I)
UNCH  = re.compile(r"\bunchanged\b", re.I)


def sentences(html):
    text = re.sub(r"<[^>]+>", " ", html)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def classify(html):
    """skills/announcement-digest/SKILL.md — due_change before schedule_change,
    because due_change carries the more specific token (due/deadline)."""
    for s in sentences(html):
        if UNCH.search(s) or PAST.search(s):
            continue                                   # guard: not a new change
        if DUEW.search(s) and MOVED.search(s) and not NEG.search(s):
            return "due_change"
    for s in sentences(html):
        if PAST.search(s):
            continue
        if SCHED.search(s) and not NEG.search(s):
            return "schedule_change"
    for s in sentences(html):
        if GRADED.search(s):
            return "graded"
    return "logistics"


FLAGGED = {"schedule_change", "due_change"}
for a in load("announcements.json"):
    got = classify(a["message"])
    exp = a["_expect"]
    label = a["title"][:44]
    check("announcement-digest", f'"{label}"', got, exp["class"])
    check("announcement-digest", f'"{label}" flag', got in FLAGGED, exp["flag"])


# ── study-engine ──────────────────────────────────────────────────────────
EXAMISH = re.compile(r"\b(?:exam|midterm|final|test|quiz)\b", re.I)


def exam_candidates(groups, now, horizon_days=10, min_impact=10.0):
    out = []
    n = len([g for g in groups])
    for g in groups:
        w = float(g["group_weight"]) or 100.0 / n     # course 1102 is unweighted
        total = sum(float(a["points_possible"]) for a in g["assignments"])
        for a in g["assignments"]:
            if a["submission"]["workflow_state"] != "unsubmitted":
                continue
            structural = a.get("quiz_id") is not None
            if not (structural or EXAMISH.search(a["name"])):
                continue
            impact = float(a["points_possible"]) / total * w
            days = (iso(a["due_at"]) - now).total_seconds() / 86400
            if impact >= min_impact and 0 < days <= horizon_days:
                out.append((a["name"], round(impact, 1)))
    return sorted(out)


def source_modules(modules, exam_module_position):
    return sorted(m["name"] for m in modules
                  if m["position"] < exam_module_position
                  and any(i["type"] == "File" for i in m["items"]))


m1102 = load("modules_1102.json")
check("study-engine", "MATH 2153 Midterm 2 qualifies (16.7% >= 10, 4 days out)",
      exam_candidates(load("assignment_groups_1102.json"), TUE),
      [("Midterm 2", 16.7)])
check("study-engine", "Quiz 3 is 16 days out, outside the 10-day horizon",
      any(n == "Quiz 3" for n, _ in
          exam_candidates(load("assignment_groups_1102.json"), TUE)), False)
check("study-engine", "CSE 3901 has no upcoming exam to study for",
      exam_candidates(load("assignment_groups_1101.json"), TUE), [])
check("study-engine", "sources only modules preceding the exam",
      source_modules(m1102, 5),
      ["Unit 3 — Partial Derivatives", "Unit 4 — Related Rates & Optimization"])
check("study-engine", "never sources the post-exam module",
      "Unit 5 — Multiple Integrals" in source_modules(m1102, 5), False)


# ── report ────────────────────────────────────────────────────────────────
width = max(len(n) for _, n, _, _, _ in results) + 2
group = None
fails = 0
for g, name, ok, got, want in results:
    if g != group:
        print(f"\n{g}")
        group = g
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}"
          + ("" if ok else f"got {got!r}, want {want!r}"))
    fails += not ok

total = len(results)
print(f"\n{total - fails}/{total} passed")
sys.exit(1 if fails else 0)

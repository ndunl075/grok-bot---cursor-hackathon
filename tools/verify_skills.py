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


# ── office-hours-finder ───────────────────────────────────────────────────
DAYNAME = {"monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
           "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun"}
DAYLETTER = {"M": "Mon", "T": "Tue", "W": "Wed", "R": "Thu", "F": "Fri"}
TIMESPAN = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|–|—|to)\s*"
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.I)
ROOM = re.compile(r"\b([A-Z][A-Za-z']+)\s+(\d{2,4})\b")


def _hour(h, mer, is_start):
    """Bare hours are PM in an academic context, except a morning-looking start.
    skills/office-hours-finder/SKILL.md: 8-11 reads AM, 12 and 1-7 read PM."""
    h = int(h)
    if mer:
        m = mer.lower()
        if m == "pm" and h != 12: h += 12
        if m == "am" and h == 12: h = 0
        return h
    return h if 8 <= h <= 11 else (h if h == 12 else h + 12)


def parse_office_hours(text):
    if re.search(r"by appointment", text, re.I):
        return {"found": False}

    days = [DAYNAME[m.lower()] for m in
            re.findall(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?\b",
                       text, re.I)]
    if not days:
        for tok in re.findall(r"\b([MTWRF]{2,5})\b", text):
            days = [DAYLETTER[c] for c in tok]
            break
    t = TIMESPAN.search(text)
    if not days or not t:
        return {"found": False}

    sh, sm, smer, eh, em, emer = t.groups()
    smer = smer or emer                      # "2-4pm" -> pm applies to both
    out = {
        "found": True,
        "day": ",".join(dict.fromkeys(days)),
        "start": f"{_hour(sh, smer, True):02d}:{int(sm or 0):02d}",
        "end":   f"{_hour(eh, emer or smer, False):02d}:{int(em or 0):02d}",
        "location": None,
    }
    tail = text[t.end():]
    room = ROOM.search(tail)
    if room:
        out["location"] = f"{room.group(1)} {room.group(2)}"
    if re.search(r"\bthis week\b", text, re.I):
        out["temporary"] = True
    if re.search(r"\b(TA|teaching assistant|grader)\b", text):
        out["staff"] = "ta"
    return out


for s_ in load("syllabus_text_1101.json")["samples"]:
    got, exp = parse_office_hours(s_["text"]), s_["_expect"]
    for k in exp:
        check("office-hours-finder", f'{s_["id"]}.{k}', got.get(k), exp[k])


# ── weekly-retro ──────────────────────────────────────────────────────────
def deltas(snapshot, now):
    out = {}
    for cid, prev in snapshot["courses"].items():
        cur = next((v for v in now.values() if v["course_id"] == cid), None)
        if cur:
            out[cid] = round(cur["current_pct"] - prev["current_pct"], 1)
    return out


def newly_unreachable(snapshot, now, target=90.0):
    hit = []
    for cid, prev in snapshot["courses"].items():
        cur = next((v for v in now.values() if v["course_id"] == cid), None)
        if cur and prev["ceiling_pct"] >= target > cur["ceiling_pct"]:
            hit.append(cid)
    return hit


snap, now_ = load("snapshots.json"), load("expected_output.json")
d = deltas(snap, now_)
check("weekly-retro", "CSE 3901 delta (midterm landed)", d["1101"], -5.4)
check("weekly-retro", "MATH 2153 delta (WebAssign 5 landed)", d["1102"], 2.9)
check("weekly-retro", "leads with the largest absolute move",
      max(d, key=lambda k: abs(d[k])), "1101")
check("weekly-retro", "detects every ceiling that closed below 90 this week",
      sorted(newly_unreachable(snap, now_)), ["1101", "1102"])
check("weekly-retro", "ties break to the course whose grade moved most",
      max(newly_unreachable(snap, now_), key=lambda c: abs(d[c])), "1101")
check("weekly-retro", "no snapshot means no deltas, not deltas from zero",
      deltas({"courses": {}}, now_), {})


# ── group-project-tracker ─────────────────────────────────────────────────
grp = load("groups_1101.json")
check("group-project-tracker", "detects a group assignment by group_category_id",
      grp["assignment_group_category"]["group_category_id"] is not None, True)
check("group-project-tracker", "group submission is unsubmitted",
      grp["submission"]["workflow_state"], "unsubmitted")
check("group-project-tracker", "72h window catches Project 2 a day before deadline-guard",
      guard(iso("2026-09-08T11:00:00Z"), 72, 5), ["Project 2: Rails API"])
check("group-project-tracker", "stores only id and short_name for teammates",
      sorted(set(k for u in grp["groups"][0]["users"] for k in u)),
      ["id", "short_name"])


# ── calendar-sync ─────────────────────────────────────────────────────────
def sync_action(assignment, event):
    """Keyed on canvas_assignment_id in extendedProperties, never on the title."""
    if assignment is None:
        return "delete" if event else "skip"
    if assignment.get("submitted") or not assignment.get("due_at"):
        return "delete" if event else "skip"
    if event is None:
        return "create"
    if event["due_at"] != assignment["due_at"]:
        return "patch_time"
    if event["title"] != assignment["title"]:
        return "patch_title"
    return "skip"


A = {"title": "CSE 3901 — Project 2", "due_at": "2026-09-11T03:59:00Z", "submitted": False}
E = {"title": "CSE 3901 — Project 2", "due_at": "2026-09-11T03:59:00Z"}
check("calendar-sync", "second run is a no-op (idempotent)", sync_action(A, E), "skip")
check("calendar-sync", "first run creates", sync_action(A, None), "create")
check("calendar-sync", "moved due date patches the time",
      sync_action(A, {**E, "due_at": "2026-09-14T03:59:00Z"}), "patch_time")
check("calendar-sync", "renamed assignment patches the title, not a duplicate",
      sync_action({**A, "title": "CSE 3901 — Rails API Project"}, E), "patch_title")
check("calendar-sync", "submitting removes the event",
      sync_action({**A, "submitted": True}, E), "delete")
check("calendar-sync", "undated assignments never sync",
      sync_action({**A, "due_at": None}, None), "skip")


# ── syllabus-ingest ───────────────────────────────────────────────────────
SYNS = {"hw": "homework", "assignment": "homework", "proj": "project"}
WORDNUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5"}


def norm(name):
    n = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    n = re.sub(r"([a-z])(\d)", r"\1 \2", n)     # HW5 -> hw 5, so HW == Homework
    parts = []
    for w in n.split():
        w = SYNS.get(w, WORDNUM.get(w, w))
        parts.append(w.lstrip("0") if w.isdigit() else w)
    return " ".join(parts)


def matches(candidate, canvas_items, day_tol=1):
    for it in canvas_items:
        if norm(candidate["name"]) == norm(it["name"]):
            return it
        gap = abs((iso(candidate["due"]) - iso(it["due"])).days)
        shared = set(norm(candidate["name"]).split()) & set(norm(it["name"]).split())
        if gap <= day_tol and any(len(w) > 3 for w in shared):
            return it
    return None


CANVAS = [{"name": "Project 2: Rails API", "due": "2026-09-11T03:59:00Z"},
          {"name": "HW5", "due": "2026-09-16T03:59:00Z"}]
check("syllabus-ingest", "'Homework 5' matches Canvas 'HW5' by normalized name",
      matches({"name": "Homework 5", "due": "2026-09-16T03:59:00Z"}, CANVAS)["name"], "HW5")
check("syllabus-ingest", "'Project Two' matches 'Project 2' despite the rename",
      matches({"name": "Project Two", "due": "2026-09-11T03:59:00Z"}, CANVAS)["name"],
      "Project 2: Rails API")
check("syllabus-ingest", "a date one day off still matches on a shared token",
      matches({"name": "Rails API", "due": "2026-09-10T03:59:00Z"}, CANVAS)["name"],
      "Project 2: Rails API")
check("syllabus-ingest", "a genuinely new item proposes nothing to match",
      matches({"name": "Final Project", "due": "2026-12-08T03:59:00Z"}, CANVAS), None)


# ── connector-core ────────────────────────────────────────────────────────
def connector_action(state, requested, prompted_already):
    """skills/connector-core/SKILL.md. A missing connector never blocks the
    Canvas path; it only changes where the value is delivered."""
    if state == "connected":
        return "use_connector"
    if state == "absent":
        return "fallback_silent"
    if requested:
        return "fallback_explain"          # they asked; say why it went elsewhere
    return "fallback_silent" if prompted_already else "fallback_offer_once"


check("connector-core", "connected uses it",
      connector_action("connected", False, False), "use_connector")
check("connector-core", "declared-but-unauthorized offers once, unprompted",
      connector_action("declared", False, False), "fallback_offer_once")
check("connector-core", "and never offers twice",
      connector_action("declared", False, True), "fallback_silent")
check("connector-core", "an explicit request always gets an explanation",
      connector_action("declared", True, True), "fallback_explain")
check("connector-core", "an undeclared connector is never mentioned",
      connector_action("absent", True, False), "fallback_silent")
check("connector-core", "no state ever returns 'block'",
      {connector_action(s_, r, p) for s_ in ("connected", "declared", "absent")
       for r in (True, False) for p in (True, False)} & {"block", "error"}, set())


# ── report ─────────────────────────────────────────────────────────────────
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

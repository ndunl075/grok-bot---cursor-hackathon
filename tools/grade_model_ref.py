#!/usr/bin/env python3
"""Reference implementation of skills/grade-model, run against tests/fixtures.

Local-only. Does NOT ship in the template — it exists so the skill's arithmetic
is verifiable instead of asserted, and so tests/fixtures/expected_output.json is
generated rather than hand-written.

Usage: python3 tools/grade_model_ref.py [--write]
"""
import json, sys, pathlib

FIX = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
GRADED = {"graded"}
SUBMITTED = {"submitted", "graded", "pending_review"}


def load(name):
    return json.loads((FIX / name).read_text())


def score_groups(groups, weights_source):
    """Returns (current, projected, floor, per_assignment_impact)."""
    n = len(groups)
    prepared = []
    for g in groups:
        w = float(g["group_weight"]) if weights_source == "canvas" else 100.0 / n
        assigns = g["assignments"]
        total = sum(float(a["points_possible"]) for a in assigns)
        earned = sum(float(a["submission"]["score"]) for a in assigns
                     if a["submission"]["workflow_state"] in GRADED
                     and a["submission"]["score"] is not None)
        graded_possible = sum(float(a["points_possible"]) for a in assigns
                              if a["submission"]["workflow_state"] in GRADED
                              and a["submission"]["score"] is not None)
        prepared.append(dict(g=g, w=w, total=total, earned=earned, gp=graded_possible))

    # Drop groups with nothing graded yet and renormalize. Canvas does this too;
    # skipping it is the classic way to be wrong by 15 points.
    live = [p for p in prepared if p["gp"] > 0]
    wsum = sum(p["w"] for p in live) or 1.0

    current = sum((p["earned"] / p["gp"]) * p["w"] for p in live) / wsum * 100
    # floor: zero on everything not yet graded, across ALL groups (no renormalize)
    floor = sum((p["earned"] / p["total"]) * p["w"] for p in prepared if p["total"] > 0)
    # headroom: grade points still winnable, i.e. the ungraded share of each group
    headroom = sum(((p["total"] - p["gp"]) / p["total"]) * p["w"]
                   for p in prepared if p["total"] > 0)
    ceiling = floor + headroom

    impacts = {}
    for p in prepared:
        for a in p["g"]["assignments"]:
            impacts[a["id"]] = dict(
                name=a["name"], course_id=a["course_id"],
                impact_pct=round(float(a["points_possible"]) / p["total"] * p["w"], 1),
                due_at=a.get("due_at"),
                submitted=a["submission"]["workflow_state"] in SUBMITTED,
            )
    return (round(current, 1), round(floor, 1), round(ceiling, 1),
            round(headroom, 1), impacts)


def main():
    courses = {c["course_code"]: c for c in load("courses.json")}
    out = {}
    for code, cid in (("CSE 3901", "1101"), ("MATH 2153", "1102")):
        c = courses[code]
        ws = "canvas" if c.get("apply_assignment_group_weights") else "unknown"
        groups = load(f"assignment_groups_{cid}.json")
        cur, flr, ceil_, head, impacts = score_groups(groups, ws)
        remaining = sorted(
            (v for v in impacts.values() if not v["submitted"]),
            key=lambda v: -v["impact_pct"])
        target = 90.0
        reachable = ceil_ >= target
        needed = round((target - flr) / head * 100, 1) if head > 0 else None
        out[code] = dict(
            course_id=cid, weights_source=ws,
            current_pct=cur, floor_pct=flr, ceiling_pct=ceil_, headroom_pct=head,
            canvas_reported=c["enrollments"][0]["computed_current_score"],
            drift=round(abs(cur - c["enrollments"][0]["computed_current_score"]), 1),
            target_pct=target, target_reachable=reachable,
            needed_avg_on_remaining=needed,
            at_risk=(not reachable) or (flr < 60),
            drivers=[dict(name=r["name"], impact_pct=r["impact_pct"], due_at=r["due_at"])
                     for r in remaining[:3]],
        )
        print(f"{code:10} [{ws:7}] current {cur:5}  floor {flr:5}  ceiling {ceil_:5}"
              f"   canvas says {out[code]['canvas_reported']:5}  drift {out[code]['drift']}")
        print(f"           target {target}: {'reachable' if reachable else 'UNREACHABLE'}"
              f"  (need {needed}% avg on remaining {head}% of grade)")
        for d in out[code]["drivers"]:
            print(f"           remaining: {d['name']:24} {d['impact_pct']:5}%  due {d['due_at']}")

    if "--write" in sys.argv:
        (FIX / "expected_output.json").write_text(json.dumps(out, indent=2) + "\n")
        print("\nwrote tests/fixtures/expected_output.json")


if __name__ == "__main__":
    main()

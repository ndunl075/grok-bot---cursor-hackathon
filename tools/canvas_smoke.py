#!/usr/bin/env python3
"""Verify a Canvas token and capture fixtures. Stdlib only, run locally.

WHAT THIS ANSWERS
  Whether your Canvas host, token, and the endpoints canvas-core depends on
  actually work, and what they return for your account.

WHAT THIS DOES NOT ANSWER
  Whether a Grok Bot *skill* can make these calls. That is a property of the
  bot runtime, not of Canvas, and this script cannot test it. See
  skills/canvas-core/SKILL.md ("Access path") — you still have to try it in
  the bot.

SAFETY
  The token is read with getpass, so it is never in argv, never in your shell
  history, and never echoed. It is never written to disk and never printed,
  not even partially. Captured fixtures go to tests/fixtures/live/, which is
  gitignored.

USAGE
  python3 tools/canvas_smoke.py https://yourschool.instructure.com
  python3 tools/canvas_smoke.py https://yourschool.instructure.com --fixtures
  python3 tools/canvas_smoke.py --ics 'https://.../feeds/calendars/user_x.ics'
"""
import argparse, getpass, json, pathlib, re, sys, urllib.error, urllib.request
from urllib.parse import urljoin

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT / "tests" / "fixtures" / "live"
TIMEOUT = 20

GREEN, RED, DIM, YEL, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[33m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = DIM = YEL = OFF = ""


class Canvas:
    def __init__(self, base, token):
        self.base = base.rstrip("/")
        self._token = token
        self.calls = 0

    def _req(self, url):
        r = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self._token,
            "Accept": "application/json+canvas-string-ids",
            "User-Agent": "canvas-student-assistant/smoke",
        })
        return urllib.request.urlopen(r, timeout=TIMEOUT)

    def get(self, path, paginate=True):
        """Returns (status, data, note). Never raises on an HTTP error."""
        url = urljoin(self.base + "/api/v1/", path.lstrip("/"))
        url += ("&" if "?" in url else "?") + "per_page=100"
        out, pages = [], 0
        while url and pages < 10:
            try:
                self.calls += 1
                resp = self._req(url)
            except urllib.error.HTTPError as e:
                body = e.read(400).decode("utf-8", "replace")
                if e.code == 403 and "Rate Limit" in body:
                    return 403, None, "rate limited (back off, this is not an auth failure)"
                return e.code, None, body.strip()[:160]
            except Exception as e:                      # DNS, TLS, timeout
                return 0, None, f"{type(e).__name__}: {e}"

            raw = resp.read()
            if raw.lstrip()[:1] in (b"<",):
                return resp.status, None, ("HTML, not JSON — the base URL is probably "
                                           "the web app or an SSO redirect")
            data = json.loads(raw)
            out = data if not out else (out + data if isinstance(data, list) else out)
            pages += 1
            url = self._next(resp.headers.get("Link", "")) if paginate else None
        return 200, out, f"{pages} page(s)"

    @staticmethod
    def _next(link):
        for part in link.split(","):
            m = re.search(r'<([^>]+)>;\s*rel="next"', part)
            if m:
                return m.group(1)
        return None


def line(ok, label, detail=""):
    tag = f"{GREEN}ok  {OFF}" if ok is True else (
          f"{RED}FAIL{OFF}" if ok is False else f"{YEL}warn{OFF}")
    print(f"  {tag}  {label:<42}{DIM}{detail}{OFF}")


def sanitize(obj, ids, seq):
    """Strip identity, keep shape and numbers. IDs are remapped consistently."""
    DROP = {"name", "course_code", "short_name", "sortable_name", "title",
            "display_name", "filename", "user_name", "sis_course_id",
            "sis_user_id", "login_id", "email", "avatar_url", "html_url", "url",
            "uuid", "integration_id", "message", "description", "body"}
    if isinstance(obj, list):
        return [sanitize(v, ids, seq) for v in obj]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        if k in DROP:
            if isinstance(v, str):
                out[k] = f"<{k} redacted>"
            continue
        if k == "id" or k.endswith("_id"):
            if isinstance(v, (str, int)) and str(v) not in ids:
                seq[0] += 1
                ids[str(v)] = str(10000 + seq[0])
            out[k] = ids.get(str(v), v)
        else:
            out[k] = sanitize(v, ids, seq)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_url", nargs="?", help="https://yourschool.instructure.com")
    ap.add_argument("--fixtures", action="store_true",
                    help="write sanitized responses to tests/fixtures/live/ (gitignored)")
    ap.add_argument("--ics", metavar="URL",
                    help="test the no-auth calendar feed fallback instead (Path C tier 1)")
    args = ap.parse_args()

    if args.ics:
        print("\nICS calendar feed (no token required)")
        try:
            with urllib.request.urlopen(args.ics, timeout=TIMEOUT) as r:
                text = r.read().decode("utf-8", "replace")
            events = text.count("BEGIN:VEVENT")
            line(events > 0, "feed reachable", f"{events} events")
            print(f"\n  {DIM}This URL is a credential. Anyone holding it reads the"
                  f" schedule.{OFF}\n  {DIM}Keep it in bot memory only, never in a"
                  f" template.{OFF}\n")
        except Exception as e:
            line(False, "feed unreachable", f"{type(e).__name__}: {e}")
            return 1
        return 0

    if not args.base_url:
        ap.error("base_url is required (or use --ics)")

    base = args.base_url.strip().rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    base = re.sub(r"/(courses|api)(/.*)?$", "", base)      # tolerate a pasted deep link

    print(f"\n{DIM}Token input is hidden and is never stored, printed, or"
          f" written to disk.{OFF}")
    token = getpass.getpass("Canvas access token: ").strip()
    if not token:
        print("no token entered"); return 1

    c = Canvas(base, token)
    print(f"\nCanvas at {base}")

    status, me, note = c.get("users/self", paginate=False)
    if status == 401:
        line(False, "GET /users/self", "401 — token rejected. Regenerate it in "
                                       "Account -> Settings.")
        return 1
    if status != 200:
        line(False, "GET /users/self", f"{status} {note}")
        if status == 0:
            print(f"\n  {DIM}Nothing answered at that address. Check the host is"
                  f" exactly what you\n  see in the browser when logged into Canvas,"
                  f" and that you are not\n  behind a VPN or proxy that blocks"
                  f" it.{OFF}")
        elif status == 404:
            print(f"\n  {DIM}Reached the host but not the API. Some schools serve"
                  f" Canvas from a\n  subpath or a different hostname than the login"
                  f" page.{OFF}")
        return 1
    line(True, "GET /users/self", "token accepted")

    status, courses, note = c.get(
        "courses?enrollment_state=active&include[]=term&include[]=total_scores")
    ok = status == 200 and isinstance(courses, list)
    line(ok, "GET /courses", f"{len(courses)} active" if ok else f"{status} {note}")
    if not ok:
        return 1

    courses = [c_ for c_ in courses if not c_.get("access_restricted_by_date")]
    weighted = [c_ for c_ in courses if c_.get("apply_assignment_group_weights")]
    line(True, "courses publishing group weights",
         f"{len(weighted)} of {len(courses)} — the rest need the weights asked for")

    captured, reachable = {}, 0
    for course in courses[:6]:
        cid = course["id"]
        st, groups, nt = c.get(f"courses/{cid}/assignment_groups?include[]=assignments")
        if st == 200:
            reachable += 1
            captured[f"assignment_groups_{cid}"] = groups
        else:
            line(None, f"course {cid} assignment_groups",
                 f"{st} — mark unavailable, keep going")
    line(reachable > 0, "GET /courses/{id}/assignment_groups",
         f"{reachable} of {min(len(courses), 6)} readable")

    st, enr, nt = c.get("users/self/enrollments?state[]=active")
    line(st == 200, "GET /users/self/enrollments",
         "Canvas's own computed scores — the oracle for grade-model"
         if st == 200 else f"{st} {nt}")

    codes = "".join(f"context_codes[]=course_{c_['id']}&" for c_ in courses[:10])
    st, anns, nt = c.get(f"announcements?{codes}active_only=true")
    line(st == 200, "GET /announcements",
         f"{len(anns)} recent" if st == 200 else f"{st} {nt}")

    st, mods, nt = c.get(f"courses/{courses[0]['id']}/modules?include[]=items")
    line(st == 200, "GET /modules", "study-engine can source material"
         if st == 200 else f"{st} {nt} — study-engine falls back to descriptions")

    st, files, nt = c.get(f"courses/{courses[0]['id']}/files")
    line(st == 200, "GET /files",
         "available" if st == 200 else f"{st} — normal, Files tab is often off")

    print(f"\n  {c.calls} requests made.")

    if args.fixtures:
        LIVE.mkdir(parents=True, exist_ok=True)
        ids, seq = {}, [0]
        captured["courses"] = courses
        if st == 200:
            captured["modules"] = mods
        for name, payload in captured.items():
            (LIVE / f"{name}.json").write_text(
                json.dumps(sanitize(payload, ids, seq), indent=2) + "\n")
        print(f"\n  wrote {len(captured)} files to {LIVE.relative_to(ROOT)}/ "
              f"{DIM}(gitignored){OFF}")
        print(f"  {YEL}Names and free text are redacted; scores and point values are"
              f" not.{OFF}\n  {DIM}Review before promoting anything into"
              f" tests/fixtures/.{OFF}")

    print(f"\n{GREEN}Canvas side is good.{OFF} The open question is whether a Grok"
          f" Bot skill\ncan make these same calls — test that in the bot, not here.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

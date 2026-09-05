# Demo script

Contest judges on engagement, bot quality, and creativity. Engagement is won
in the first four seconds, so the video opens on the payoff and explains
afterward.

**The one idea:** Canvas shows a student the grade they have. It never shows
them the grade they can still get. When those two numbers stop agreeing with
the grade they *want*, that is the moment worth knowing about, and it usually
passes silently.

## The hook

> An A in this class stopped being possible two weeks ago. Canvas never
> mentioned it.

Everything else in the video is support for that sentence. If a cut does not
serve it, drop the cut.

## Assets

- `docs/demo/index.html` — animated walkthrough, plays on load, `R` replays.
  Ends on the three-bot architecture figure, which is shot 7.
  Record at 1280×1000 or wider. Built for screen capture: no browser-chrome
  dependency, readable at 720p, both themes, reduced-motion respected.
  The sequence runs 9.6s and the scrubber tracks it, so you can cut to any
  beat. Amber is the grade still winnable; the single red element on the page
  is the target marker landing outside it.
- A real phone showing the actual bot thread. **Do not fake this.** One
  genuine screen recording of the bot texting is worth more than the whole
  animation, and a judge can tell the difference.

## Shot list — 55 seconds

| # | Time | Shot | Audio |
|---|---|---|---|
| 1 | 0:00–0:04 | Cold open on the instrument. Amber wipes right, then the red target marker drops *past* its edge and flashes. No title card. | "An A in this class stopped being possible two weeks ago." |
| 2 | 0:04–0:08 | Same frame, the `2.0 out of reach` bracket draws. | "Canvas never mentioned it." |
| 3 | 0:08–0:16 | Cut to phone. Real bot thread, messages arriving. | "This is a Grok Bot that reads your Canvas and texts you first." |
| 4 | 0:16–0:26 | Screen: the impact strip. HW5 and the midterm side by side, both 100 points, 4% vs 30%. | "It ranks your work by what it actually does to your grade. These are both worth a hundred points. One of them matters seven times as much." |
| 5 | 0:26–0:34 | Phone: the ceiling message, then the reply, then the new target. | "So when a target goes out of reach, it says so, and it gives you the next one that isn't." |
| 6 | 0:34–0:41 | Screen recording of setup: paste Canvas URL, paste token, courses list appears. Keep the real timer visible. | "Setup is a URL and a token. Under a minute." |
| 7 | 0:41–0:50 | Scroll to the architecture figure. Hold on the red boundary line. | "There are three bots. Only one holds the key, and only one texts you — so you never get nudged three times about the same thing." |
| 8 | 0:50–0:55 | Static end frame: bot name, template link. | "It's a template. Install it and it starts tomorrow morning." |

## Rules for the recording

- **Blur or replace every real course name and grade.** Use a second account
  seeded from `tests/fixtures/` if there is time; blur if there is not.
- Never show the token, even blurred, even for a frame. Cut before the paste
  and resume after.
- Do not narrate the architecture. Nobody is judging the routine schedule.
- No background music with lyrics. No stock-footage students.
- Capture at 60fps if possible. The animation uses spring easing and it reads
  as cheap at 30.

## Post draft

For LinkedIn. Sentences capitalized, no dashes.

> I built a Canvas bot for the Grok Bot contest this weekend.
>
> Here is the thing it does that Canvas won't. It tells you the best grade you
> can still get.
>
> Your Canvas dashboard shows a current grade. That number is backward looking.
> It cannot tell you that the midterm you took two weeks ago already closed off
> the A, because it never computes the ceiling. So students keep grinding
> toward a target that stopped being reachable, and they find out in December.
>
> The bot computes three numbers every four hours. Your floor if you turn in
> nothing else. Your ceiling if you ace everything left. And the average you
> need on remaining work to hit the grade you actually want. When that average
> crosses 100 percent, it tells you, once, and offers the next target that
> still works.
>
> It also ranks your assignments by real impact instead of points. A hundred
> point homework and a hundred point midterm look identical in Canvas. In my
> test course one of them moves the final grade by 4 percent and the other by
> 30.
>
> There are actually three bots. A Registrar that watches Canvas, a Tutor that
> quizzes you before exams, and an Advocate that drafts the email when you need
> an extension. Only the Registrar holds your access token and only the
> Registrar messages you first, which is what stops three bots nudging you
> three times about one deadline. Install the Registrar alone and everything
> still works.
>
> Setup is your Canvas URL and an access token. It texts you first every
> morning.
>
> Template link in the comments. #GrokBotForStudents

Check before posting: no course names, no real grades, no token in any frame
of the attached video.

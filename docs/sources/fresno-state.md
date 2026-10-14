# Fresno State: data sources and collection rules

Checked 2026-10-14 by fetching each page from GitHub's network as
`BeyondTheSyllabusBot/0.1 (+https://github.com/Shabanaomar/BeyondtheSyllabus)`, one request per
second, and one request per 120 seconds for the catalog. Every finding below comes from those
fetches.

## Summary

| Source | robots.txt | What happened | Recommendation |
| --- | --- | --- | --- |
| Catalog, `catalog.fresnostate.edu` | Allows program and course pages; disallows `/portfolio.php`, `/portfolio_nopop.php`, `/ajax/`, `/search_advanced.php`; **crawl-delay 120 s** | Home page and catalog list loaded. The "Degrees and Programs" page returned **HTTP 202 with `x-amzn-waf-action: challenge`**: an Amazon WAF bot challenge | **Don't automate.** The site is filtering bots; we don't bypass challenges. Enter the 3 programs by hand for the prototype and ask the university for permission or an export (see below) |
| Engineering college, `engineering.fresnostate.edu` | None (404), so no restrictions | Degrees, clubs and Industry Expo pages loaded | **Collect with limits:** weekly, 1 request/second |
| Student affairs, `studentaffairs.fresnostate.edu` | None (404) | Clubs page loaded | **Collect with limits:** weekly |
| Academic calendar, `academics.fresnostate.edu/about/calendars/current.html` | None (404) | Loaded; dates are in the page | **Collect with limits:** weekly |
| Campus events, `calendar.fresnostate.edu` | None (404) | Not needed for version 1 | Skip for now |
| Clubs directory, `engage.fresnostate.edu` | Disallows `/api/` and `/engage/` | The organizations page is an empty shell; club data loads from `/api/`, which is disallowed | **Don't collect.** Link students to Engage instead; use the engineering clubs page for picks |
| Class schedule | — | The registrar's "Plan your schedule" link redirects to the registrar home page; no public class search was found. It appears to be in the student portal (login) | **Not available.** We never log in to university systems |
| Main site, `www.fresnostate.edu` | Allows everything we need | Loaded | Collect with limits if needed |

## Terms of use

The site has no terms-of-use page that addresses automated collection. The two relevant pages:

- [Copyright](https://www.fresnostate.edu/copyright.html): points to the university's Acceptable
  Use Policy, which asks users to obey the law and respect copyright and intellectual property.
- [Disclaimer](https://www.fresnostate.edu/disclaimer.html): site data is informational, not
  guaranteed error-free, and not a promise or contract.

What that means for us: degree requirements and course facts aren't copyrightable expression, so
we store the facts (course codes, units, rules) and always link back to the source page. We don't
republish page text. Because the site says its data may contain errors, every plan keeps the
"confirm with your advisor" note.

## Decisions needed

1. **Catalog (requirements, courses, prerequisites).** Recommended: for the 10-user prototype,
   enter the three programs (Civil, Mechanical, Electrical; 2026-27 catalog) by hand from the
   catalog pages, each rule linked to its page and reviewed by you. In parallel, email the
   catalog office or the registrar to ask whether automated weekly collection is acceptable, or
   whether they can provide an export. Acalog, the catalog software, has an API the university
   can enable.
2. **Class times.** Recommended: the long-term plan works at the course level, using each course's
   typical term. For next term's schedule, the student adds the sections they're considering
   from their portal (course, days, times), and the engine checks them against work hours and
   prerequisites.

## Raw evidence

The raw responses (headers and bodies) are on the scratch branch `probe/fetch` under
`.probe/out/`. That branch is a temporary tool and won't be merged.

# UC Berkeley: data sources and collection rules

Checked 2026-10-14 by fetching each page from GitHub's network as
`BeyondTheSyllabusBot/0.1 (+https://github.com/Shabanaomar/BeyondtheSyllabus)`, one request per
second, and one per 11 seconds where a site asks for a 10-second crawl delay. Every finding below
comes from those fetches.

## Summary

| Source | robots.txt | What happened | Recommendation |
| --- | --- | --- | --- |
| Undergraduate catalog, `undergraduate.catalog.berkeley.edu` | **Allow: /** (everything) | Home, programs and College of Engineering pages loaded; program names are in the page | **Collect with limits:** weekly, 1 request/second |
| Engineering college, `engineering.berkeley.edu` | Everything allowed; **crawl-delay 10 s** | Major programs and degree worksheets pages loaded. Worksheets (PDF) are listed per admission year; the newest listed for Civil, Mechanical and EECS is **2023** | **Collect with limits:** weekly, 1 request per 10 seconds. Use the catalog for newer admission years |
| Class schedule, `classes.berkeley.edu` | **Disallows `/search/`**, which is where class and section listings live | Home page loaded | **Don't collect** section listings. Ask for access to Berkeley's official class data (see below) |
| Registrar calendars, `registrar.berkeley.edu/calendars/` | Disallows only `/wp-json/` | Loaded. The registrar publishes **official public Google Calendars**: Academic Calendar (`berkeley.edu_lrpagcvovu47raj72dmpatjou4@group.calendar.google.com`) and Student Enrollment Calendar (`c_lublpqqigfijlbc1l4rudcpi5s@group.calendar.google.com`) | **Collect** from the public calendar feeds: they're published for subscribing |
| Clubs, `callink.berkeley.edu` | Disallows `/api/` and `/engage/` | The organizations page is an empty shell; club data loads from `/api/`, which is disallowed | **Don't collect.** Link students to CalLink; build engineering club picks from department and college pages |
| Career Center, `career.berkeley.edu` | Disallows only `/wp-json/` | Fair list page (checked earlier) is public; details are in Handshake (login) | **Collect with limits:** weekly fair names and dates; link to Handshake |
| EECS Career Fair, `hkn.eecs.berkeley.edu` | Allows everything we need | — | **Collect with limits:** weekly |
| Student affairs, `studentaffairs.berkeley.edu` | Disallows only `/wp-json/` | — | Collect with limits if needed |
| Main site, `www.berkeley.edu` | Everything allowed; crawl-delay 10 s | Loaded | Not needed for version 1 |

## Terms of use

No terms-of-use page addressing automated collection was found on these sites. The main site's
[privacy policy](https://www.berkeley.edu/privacy-policy/) covers what Berkeley collects from its
visitors, not reuse of public pages. As with Fresno State, we store facts (course codes, units,
rules, dates), link every item to its source page, and don't republish page text.

## Decisions needed

1. **Class times.** Recommended: the long-term plan works at the course level. For next term, the
   student adds the sections they're considering (course, days, times), and the engine checks
   them against work hours and prerequisites. In parallel, ask Berkeley for access to its class
   data through the university's API program (requires approval).
2. **Admission years after 2023.** Worksheets stop at 2023 on the engineering site, so for students
   admitted in 2024 or later, requirements come from the undergraduate catalog. I'll confirm each
   rule against the catalog page and send unclear ones to your review queue.

## Raw evidence

The raw responses (headers and bodies) are on the scratch branch `probe/fetch` under
`.probe/out/`. That branch is a temporary tool and won't be merged.

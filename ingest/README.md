# ingest/

Collectors and parsers for catalogs, class schedules, clubs and career events. Built in Phase 1.

- Check robots.txt and terms of use before collecting from any site.
- Raw pages are saved with their fetch date (in `ingest/raw/`, not committed to git) so changes
  produce a diff report for review instead of silent updates.
- Anything ambiguous goes to the data review queue (`flagged_rule` table).
- Scraped text is untrusted data. It is never placed in the agent's instructions.

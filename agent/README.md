# agent/

The Claude tool-use counselor. Built in Phase 2, step 12.

- `prompt.md` is the system prompt. `{school_name}` and `{college_name}` are filled in from our
  own data, never from scraped text or student uploads.
- The agent only calls engine tools; it never decides requirements or prerequisites itself.

/**
 * Builds an iCalendar (.ics) file that Google, Apple and Outlook calendars can import.
 * Follows RFC 5545: CRLF line endings, escaped text, lines folded at 75 octets.
 */

export interface WeeklyMeeting {
  kind: "weekly";
  uid: string;
  title: string;
  days: ("MO" | "TU" | "WE" | "TH" | "FR" | "SA" | "SU")[];
  start: string; // "09:30" local time
  end: string; // "10:45"
  firstDate: string; // first day of instruction, "2027-01-20"
  lastDate: string; // last day of instruction, "2027-05-12"
  location?: string;
  description?: string;
  /** Dates with no class (holidays, breaks), as "YYYY-MM-DD". */
  skipDates?: string[];
}

export interface TimedEvent {
  kind: "timed";
  uid: string;
  title: string;
  date: string; // "2026-09-23"
  start: string; // "10:00"
  end: string; // "14:00"
  location?: string;
  description?: string;
  url?: string;
}

export interface AllDayEvent {
  kind: "all-day";
  uid: string;
  title: string;
  date: string; // first day
  endDate?: string; // last day, inclusive
  description?: string;
}

export type CalendarItem = WeeklyMeeting | TimedEvent | AllDayEvent;

const TZ = "America/Los_Angeles";
const DAY_INDEX: Record<WeeklyMeeting["days"][number], number> = {
  SU: 0,
  MO: 1,
  TU: 2,
  WE: 3,
  TH: 4,
  FR: 5,
  SA: 6,
};

export function escapeText(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

/** Fold a content line to 75 octets per RFC 5545 §3.1, never splitting a UTF-8 character. */
export function fold(line: string): string {
  const encoder = new TextEncoder();
  const parts: string[] = [];
  let current = "";
  let size = 0;
  for (const char of line) {
    const charSize = encoder.encode(char).length;
    const limit = parts.length === 0 ? 75 : 74; // continuation lines start with a space
    if (size + charSize > limit) {
      parts.push(current);
      current = "";
      size = 0;
    }
    current += char;
    size += charSize;
  }
  parts.push(current);
  return parts.join("\r\n ");
}

const compactDate = (date: string) => date.replaceAll("-", "");
const compactTime = (time: string) => `${time.replace(":", "").padStart(4, "0")}00`;

export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** The first date on or after `from` that falls on one of `days`. */
export function firstMeetingDate(from: string, days: WeeklyMeeting["days"]): string {
  const wanted = new Set(days.map((d) => DAY_INDEX[d]));
  for (let i = 0; i < 7; i += 1) {
    const date = addDays(from, i);
    if (wanted.has(new Date(`${date}T00:00:00Z`).getUTCDay())) return date;
  }
  return from;
}

function lines(item: CalendarItem, stamp: string): string[] {
  const out = ["BEGIN:VEVENT", `UID:${item.uid}@beyondthesyllabus`, `DTSTAMP:${stamp}`];
  out.push(`SUMMARY:${escapeText(item.title)}`);
  if (item.kind === "weekly") {
    const first = firstMeetingDate(item.firstDate, item.days);
    out.push(`DTSTART;TZID=${TZ}:${compactDate(first)}T${compactTime(item.start)}`);
    out.push(`DTEND;TZID=${TZ}:${compactDate(first)}T${compactTime(item.end)}`);
    // UNTIL must be UTC: 07:59:59Z the next day is just before midnight Pacific on lastDate.
    const until = `${compactDate(addDays(item.lastDate, 1))}T075959Z`;
    out.push(`RRULE:FREQ=WEEKLY;BYDAY=${item.days.join(",")};UNTIL=${until}`);
    const meetingDays = new Set(item.days.map((d) => DAY_INDEX[d]));
    const skipped = [...(item.skipDates ?? [])]
      .sort()
      .filter((d) => meetingDays.has(new Date(`${d}T00:00:00Z`).getUTCDay()));
    if (skipped.length) {
      const times = skipped.map((d) => `${compactDate(d)}T${compactTime(item.start)}`);
      out.push(`EXDATE;TZID=${TZ}:${times.join(",")}`);
    }
  } else if (item.kind === "timed") {
    out.push(`DTSTART;TZID=${TZ}:${compactDate(item.date)}T${compactTime(item.start)}`);
    out.push(`DTEND;TZID=${TZ}:${compactDate(item.date)}T${compactTime(item.end)}`);
    if (item.url) out.push(`URL:${item.url}`);
  } else {
    out.push(`DTSTART;VALUE=DATE:${compactDate(item.date)}`);
    out.push(`DTEND;VALUE=DATE:${compactDate(addDays(item.endDate ?? item.date, 1))}`);
  }
  if ("location" in item && item.location) out.push(`LOCATION:${escapeText(item.location)}`);
  if (item.description) out.push(`DESCRIPTION:${escapeText(item.description)}`);
  out.push("END:VEVENT");
  return out;
}

const TIMEZONE_BLOCK = [
  "BEGIN:VTIMEZONE",
  `TZID:${TZ}`,
  "BEGIN:DAYLIGHT",
  "TZOFFSETFROM:-0800",
  "TZOFFSETTO:-0700",
  "TZNAME:PDT",
  "DTSTART:19700308T020000",
  "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
  "END:DAYLIGHT",
  "BEGIN:STANDARD",
  "TZOFFSETFROM:-0700",
  "TZOFFSETTO:-0800",
  "TZNAME:PST",
  "DTSTART:19701101T020000",
  "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
  "END:STANDARD",
  "END:VTIMEZONE",
];

export function buildCalendar(name: string, items: CalendarItem[], now = new Date()): string {
  const stamp = now
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");
  const all = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Beyond the Syllabus//Plan export//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${escapeText(name)}`,
    `X-WR-TIMEZONE:${TZ}`,
    ...TIMEZONE_BLOCK,
    ...items.flatMap((item) => lines(item, stamp)),
    "END:VCALENDAR",
  ];
  return `${all.map(fold).join("\r\n")}\r\n`;
}

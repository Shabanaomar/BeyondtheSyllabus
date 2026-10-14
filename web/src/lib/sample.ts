/**
 * A made-up student for the public demo. Courses, reasons and times are illustrations, not
 * Fresno State requirements. The term dates and the club names are real (collected from the
 * university's own pages; see docs/sources/fresno-state.md).
 */

import type { Dashboard } from "./dashboard-types";
import { addDays, type CalendarItem } from "./ics";

export const SAMPLE_NOTICE =
  "Maya is a made-up student. Her courses and times are examples, not Fresno State requirements. The term dates and club names are real.";

// Fresno State, Spring 2027 (academics.fresnostate.edu/about/calendars/current.html).
const SPRING_2027 = {
  firstInstruction: "2027-01-20",
  lastInstruction: "2027-05-12",
  holidays: ["2027-02-15", "2027-03-31"],
  springBreak: { from: "2027-03-22", to: "2027-03-26" },
  finals: { from: "2027-05-17", to: "2027-05-20" },
};

function range(from: string, to: string): string[] {
  const out: string[] = [];
  for (let d = from; d <= to; d = addDays(d, 1)) out.push(d);
  return out;
}

const noClassDays = [
  ...SPRING_2027.holidays,
  ...range(SPRING_2027.springBreak.from, SPRING_2027.springBreak.to),
];

export const sampleDashboard: Dashboard = {
  firstName: "Maya",
  program: "Mechanical Engineering at Fresno State",
  term: "Spring 2027",
  progress: {
    unitsDone: 62,
    unitsTotal: 120,
    graduationTerm: "Spring 2028",
    onTrack: true,
    summary: "3 core courses left",
  },
  week: [
    {
      day: "Mon",
      entries: [
        { start: "9:00", end: "9:50", label: "MATH 77", kind: "class" },
        { start: "1:00", end: "5:00", label: "Work", kind: "work" },
      ],
    },
    { day: "Tue", entries: [{ start: "9:30", end: "10:45", label: "ME 112", kind: "class" }] },
    {
      day: "Wed",
      entries: [
        { start: "9:00", end: "9:50", label: "MATH 77", kind: "class" },
        { start: "1:00", end: "5:00", label: "Work", kind: "work" },
      ],
    },
    { day: "Thu", entries: [{ start: "9:30", end: "10:45", label: "ME 112", kind: "class" }] },
    { day: "Fri", entries: [{ start: "10:00", end: "12:45", label: "ME 159 lab", kind: "lab" }] },
  ],
  weekNote: "Every class fits around your Monday and Wednesday shifts.",
  nextTerm: [
    {
      code: "ME 112",
      title: "Thermodynamics",
      units: 3,
      reason: "Required for your major, and you need it before ME 120",
    },
    {
      code: "MATH 77",
      title: "Differential Equations",
      units: 4,
      reason: "Required for your major",
    },
    {
      code: "ME 159",
      title: "Renewable Energy Systems",
      units: 3,
      reason: "A technical elective that matches your interest in energy",
    },
  ],
  clubs: [
    {
      name: "American Society of Mechanical Engineers",
      kind: "professional",
      reason: "fits your major and your energy goal",
      url: "https://engineering.fresnostate.edu/student-services/clubs-orgs.html",
    },
    {
      name: "Society of Women Engineers",
      kind: "both",
      reason: "mentoring and community across all engineering majors",
      url: "https://engineering.fresnostate.edu/student-services/clubs-orgs.html",
    },
  ],
  events: [
    {
      title: "Spring engineering career fair (example)",
      date: "2027-02-24",
      time: "10 a.m. to 2 p.m.",
      tip: "Bring printed resumes",
    },
  ],
};

export const sampleCalendar: CalendarItem[] = [
  {
    kind: "weekly",
    uid: "sample-math77",
    title: "MATH 77 · Differential Equations (example)",
    days: ["MO", "WE"],
    start: "09:00",
    end: "09:50",
    firstDate: SPRING_2027.firstInstruction,
    lastDate: SPRING_2027.lastInstruction,
    skipDates: noClassDays,
  },
  {
    kind: "weekly",
    uid: "sample-me112",
    title: "ME 112 · Thermodynamics (example)",
    days: ["TU", "TH"],
    start: "09:30",
    end: "10:45",
    firstDate: SPRING_2027.firstInstruction,
    lastDate: SPRING_2027.lastInstruction,
    skipDates: noClassDays,
  },
  {
    kind: "weekly",
    uid: "sample-me159",
    title: "ME 159 lab · Renewable Energy Systems (example)",
    days: ["FR"],
    start: "10:00",
    end: "12:45",
    firstDate: SPRING_2027.firstInstruction,
    lastDate: SPRING_2027.lastInstruction,
    skipDates: noClassDays,
  },
  {
    kind: "timed",
    uid: "sample-fair",
    title: "Spring engineering career fair (example)",
    date: "2027-02-24",
    start: "10:00",
    end: "14:00",
    description: "Bring printed resumes.",
  },
  {
    kind: "all-day",
    uid: "fs-2027sp-instruction-start",
    title: "First day of spring instruction",
    date: SPRING_2027.firstInstruction,
  },
  {
    kind: "all-day",
    uid: "fs-2027sp-break",
    title: "Spring break (no classes)",
    date: SPRING_2027.springBreak.from,
    endDate: SPRING_2027.springBreak.to,
  },
  {
    kind: "all-day",
    uid: "fs-2027sp-finals",
    title: "Final exams",
    date: SPRING_2027.finals.from,
    endDate: SPRING_2027.finals.to,
  },
];

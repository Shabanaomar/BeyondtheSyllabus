/** What the dashboard shows. Filled from the planning engine for real students. */

export type Weekday = "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun";

export interface WeekEntry {
  start: string; // "9:00"
  end?: string; // "10:15"
  label: string; // "MATH 77" or "Work"
  kind: "class" | "lab" | "work" | "commute" | "other";
}

export interface WeekDay {
  day: Weekday;
  entries: WeekEntry[];
}

export interface CourseRecommendation {
  code: string;
  title: string;
  units: number;
  reason: string;
  notes?: string[];
}

export interface ClubRecommendation {
  name: string;
  kind: "professional" | "social" | "both";
  reason: string;
  url?: string;
}

export interface CareerEvent {
  title: string;
  date: string; // ISO date, e.g. "2026-09-23"
  time?: string; // "10 a.m. to 2 p.m."
  place?: string;
  tip?: string;
  url?: string;
}

export interface Progress {
  unitsDone: number;
  unitsTotal: number;
  graduationTerm: string; // "Spring 2028"
  onTrack: boolean;
  summary: string; // "3 core courses left"
}

export interface Dashboard {
  firstName: string;
  program: string; // "Mechanical Engineering at Fresno State"
  term: string; // "Spring 2027"
  progress: Progress;
  week: WeekDay[];
  weekNote: string;
  nextTerm: CourseRecommendation[];
  clubs: ClubRecommendation[];
  events: CareerEvent[];
}

import type {
  CareerEvent,
  ClubRecommendation,
  CourseRecommendation,
  Dashboard,
  WeekDay,
  WeekEntry,
} from "@/lib/dashboard-types";

import { ButtonLink, Card, Notice, Pill, ProgressRing, type Tone } from "./ui";

const entryTone: Record<WeekEntry["kind"], Tone> = {
  class: "accent",
  lab: "warm",
  work: "lilac",
  commute: "lilac",
  other: "lilac",
};

const kindLabel: Record<ClubRecommendation["kind"], string> = {
  professional: "Professional",
  social: "Social",
  both: "Social and professional",
};

function time(entry: WeekEntry) {
  return entry.end ? `${entry.start}–${entry.end}` : entry.start;
}

export function ProgressCard({ progress }: { progress: Dashboard["progress"] }) {
  const pct = (progress.unitsDone / progress.unitsTotal) * 100;
  return (
    <Card>
      <div className="flex items-center gap-4">
        <ProgressRing
          value={pct}
          label={`${progress.unitsDone} of ${progress.unitsTotal} units done`}
        />
        <div className="flex min-w-0 flex-col gap-1">
          <p className="font-bold">
            {progress.onTrack
              ? `On track to graduate in ${progress.graduationTerm}`
              : `Graduation is at risk for ${progress.graduationTerm}`}
          </p>
          <p className="text-muted text-sm">
            {progress.unitsDone} of {progress.unitsTotal} units done · {progress.summary}
          </p>
        </div>
      </div>
    </Card>
  );
}

export function WeekCard({ week, term, note }: { week: WeekDay[]; term: string; note: string }) {
  return (
    <Card title={`Your week in ${term}`} labelledBy="week-heading">
      <ul className="flex flex-col gap-2">
        {week.map((day) => (
          <li key={day.day} className="flex items-start gap-2.5">
            <span className="w-[38px] shrink-0 pt-1 text-[13px] font-bold">{day.day}</span>
            <ul
              className="flex min-w-0 flex-1 flex-wrap gap-1.5"
              aria-label={`${day.day} schedule`}
            >
              {day.entries.length === 0 ? (
                <li className="text-muted pt-1 text-[13px]">Free</li>
              ) : (
                day.entries.map((entry) => (
                  <li key={`${entry.start}-${entry.label}`}>
                    <Pill tone={entryTone[entry.kind]}>
                      {time(entry)} {entry.label}
                    </Pill>
                  </li>
                ))
              )}
            </ul>
          </li>
        ))}
      </ul>
      <p className="text-muted text-[13px]">{note}</p>
    </Card>
  );
}

export function NextTermCard({ courses }: { courses: CourseRecommendation[] }) {
  const units = courses.reduce((sum, c) => sum + c.units, 0);
  return (
    <Card title="Take these next term" aside={`${units} units`} labelledBy="next-term-heading">
      <ul className="flex flex-col gap-3">
        {courses.map((course) => (
          <li
            key={course.code}
            className="bg-surface-soft flex flex-col gap-0.5 rounded-[var(--radius-inner)] p-3"
          >
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="font-sans font-bold">
                {course.code} · {course.title}
              </h3>
              <span className="text-muted shrink-0 text-[13px]">{course.units} units</span>
            </div>
            <p className="text-muted text-[13px]">{course.reason}</p>
            {course.notes?.map((note) => (
              <p key={note} className="text-on-warm-soft text-[13px]">
                {note}
              </p>
            ))}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function ClubsCard({ clubs }: { clubs: ClubRecommendation[] }) {
  return (
    <Card title="Clubs you might like" labelledBy="clubs-heading">
      <ul className="flex flex-col gap-3">
        {clubs.map((club) => (
          <li key={club.name} className="flex flex-col gap-0.5">
            <h3 className="font-sans font-bold">
              {club.url ? (
                <a href={club.url} className="text-ink underline-offset-2 hover:underline">
                  {club.name}
                </a>
              ) : (
                club.name
              )}
            </h3>
            <p className="text-muted text-[13px]">
              {kindLabel[club.kind]} · {club.reason}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  );
}

const monthFormat = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: "UTC" });

export function EventsCard({ events }: { events: CareerEvent[] }) {
  return (
    <Card title="Coming up for your career" labelledBy="events-heading">
      {events.length === 0 ? (
        <p className="text-muted text-sm">
          No career events are listed for your major yet. We check the career center every week.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {events.map((event) => {
            const date = new Date(`${event.date}T00:00:00Z`);
            return (
              <li key={`${event.date}-${event.title}`} className="flex items-center gap-3">
                <div
                  aria-hidden="true"
                  className="bg-warm-soft text-on-warm-soft flex size-[52px] shrink-0 flex-col items-center justify-center rounded-[14px]"
                >
                  <span className="text-[11px] font-bold uppercase">
                    {monthFormat.format(date)}
                  </span>
                  <span className="font-display text-xl leading-none font-bold">
                    {date.getUTCDate()}
                  </span>
                </div>
                <div className="flex min-w-0 flex-col gap-0.5">
                  <h3 className="font-sans font-bold">{event.title}</h3>
                  <p className="text-muted text-[13px]">
                    <time dateTime={event.date}>
                      {date.toLocaleDateString("en-US", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                        timeZone: "UTC",
                      })}
                    </time>
                    {[event.time, event.place, event.tip]
                      .filter(Boolean)
                      .map((part) => ` · ${part}`)
                      .join("")}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

export function DashboardView({
  dashboard,
  calendarHref,
  planHref,
}: {
  dashboard: Dashboard;
  calendarHref: string;
  planHref: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-[30px] leading-tight font-bold">
          Hi {dashboard.firstName}, here&apos;s your{" "}
          {(dashboard.term.split(" ")[0] ?? "").toLowerCase()}
        </h1>
        <p className="text-muted">{dashboard.program}</p>
      </div>
      <ProgressCard progress={dashboard.progress} />
      <WeekCard week={dashboard.week} term={dashboard.term} note={dashboard.weekNote} />
      <NextTermCard courses={dashboard.nextTerm} />
      <p className="-mt-1 px-1">
        <a href={planHref} className="text-accent font-bold underline-offset-2 hover:underline">
          See your full plan to graduation
        </a>
      </p>
      <ClubsCard clubs={dashboard.clubs} />
      <EventsCard events={dashboard.events} />
      <ButtonLink href={calendarHref}>Add everything to my calendar</ButtonLink>
      <Notice>Check your plan with your academic advisor before you register.</Notice>
    </div>
  );
}

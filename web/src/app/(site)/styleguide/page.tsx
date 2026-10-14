import type { Metadata } from "next";
import { notFound } from "next/navigation";

import {
  ClubsCard,
  EventsCard,
  NextTermCard,
  ProgressCard,
  WeekCard,
} from "@/components/dashboard";
import { Button, ButtonLink, Card, Notice, Pill, ProgressRing } from "@/components/ui";
import { sampleDashboard } from "@/lib/sample";

export const metadata: Metadata = { title: "Style guide", robots: { index: false } };

const swatches = [
  ["bg", "Page background"],
  ["surface", "Cards"],
  ["surface-soft", "Inner panels"],
  ["ink", "Text"],
  ["muted", "Secondary text"],
  ["line", "Dividers"],
  ["accent", "Primary actions, progress"],
  ["accent-soft", "Classes"],
  ["warm-soft", "Labs, events, notices"],
  ["lilac-soft", "Work and fixed time"],
  ["critical-soft", "Problems"],
] as const;

export default function StyleGuide() {
  // Development only: the style guide is never served in production.
  if (process.env.NODE_ENV === "production" && process.env.SHOW_STYLEGUIDE !== "1") notFound();
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold">Style guide</h1>

      <Card title="Colors" labelledBy="colors-heading">
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {swatches.map(([token, use]) => (
            <li key={token} className="flex items-center gap-2">
              <span
                className="ring-line size-9 shrink-0 rounded-[10px] ring-1"
                style={{ background: `var(--${token})` }}
              />
              <span className="flex min-w-0 flex-col">
                <code className="text-sm">--{token}</code>
                <span className="text-muted text-xs">{use}</span>
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Type" labelledBy="type-heading">
        <p className="font-display text-[40px] leading-tight font-bold">Display 40 / Bricolage</p>
        <p className="font-display text-[30px] leading-tight font-bold">Page title 30</p>
        <p className="font-display text-lg font-bold">Card title 18</p>
        <p>Body 16 / Atkinson Hyperlegible, chosen for readability.</p>
        <p className="text-muted text-[13px]">Detail 13 / muted</p>
      </Card>

      <Card title="Controls" labelledBy="controls-heading">
        <div className="flex flex-wrap gap-3">
          <Button>Primary button</Button>
          <Button kind="secondary">Secondary button</Button>
          <Button disabled>Disabled</Button>
          <ButtonLink href="/demo" kind="secondary">
            Link styled as a button
          </ButtonLink>
        </div>
        <div className="flex flex-wrap gap-2">
          <Pill tone="accent">Class</Pill>
          <Pill tone="warm">Lab or event</Pill>
          <Pill tone="lilac">Work</Pill>
          <Pill tone="critical">Clash</Pill>
        </div>
        <div className="flex items-center gap-3">
          <ProgressRing value={52} label="52% done" />
          <Notice>Notices are quiet, centered and muted.</Notice>
        </div>
      </Card>

      <h2 className="text-2xl font-bold">Dashboard cards</h2>
      <ProgressCard progress={sampleDashboard.progress} />
      <WeekCard week={sampleDashboard.week} term="Spring 2027" note={sampleDashboard.weekNote} />
      <NextTermCard courses={sampleDashboard.nextTerm} />
      <ClubsCard clubs={sampleDashboard.clubs} />
      <EventsCard events={sampleDashboard.events} />
      <EventsCard events={[]} />
    </div>
  );
}

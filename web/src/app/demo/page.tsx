import type { Metadata } from "next";

import { DashboardView } from "@/components/dashboard";
import { SAMPLE_NOTICE, sampleDashboard } from "@/lib/sample";

export const metadata: Metadata = {
  title: "Sample plan",
  description: "See the dashboard a student gets: next term, path to graduation, clubs and events.",
};

export default function DemoPage() {
  return (
    <div className="flex flex-col gap-4">
      <p
        role="note"
        className="bg-warm-soft text-on-warm-soft rounded-[var(--radius-inner)] px-4 py-3 text-sm"
      >
        <strong>Sample plan.</strong> {SAMPLE_NOTICE}
      </p>
      <DashboardView
        dashboard={sampleDashboard}
        calendarHref="/demo/calendar.ics"
        planHref="/demo#next-term-heading"
      />
    </div>
  );
}

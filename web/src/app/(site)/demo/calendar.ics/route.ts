import { buildCalendar } from "@/lib/ics";
import { sampleCalendar } from "@/lib/sample";

export function GET() {
  const body = buildCalendar("Beyond the Syllabus (sample plan)", sampleCalendar);
  return new Response(body, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": 'attachment; filename="sample-plan.ics"',
    },
  });
}

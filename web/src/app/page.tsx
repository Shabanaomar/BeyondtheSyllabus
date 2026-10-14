import { HeroArt, StepIcon } from "@/components/art";
import { NextTermCard, ProgressCard } from "@/components/dashboard";
import { ButtonLink, Card, Pill } from "@/components/ui";
import { sampleDashboard } from "@/lib/sample";

const steps = [
  {
    icon: "you",
    title: "Tell us where you are",
    body: "Pick your school and major, then upload the degree progress report your school gives you, or tick the courses you've done.",
  },
  {
    icon: "week",
    title: "Draw your week",
    body: "Mark your work shifts, commute and anything else that's fixed. Classes are planned around them.",
  },
  {
    icon: "goal",
    title: "Aim at your goal",
    body: "Next term's courses, your path to graduation, clubs and career events, each with the reason it was picked, ready for your calendar.",
  },
] as const;

export default function Home() {
  return (
    <div className="flex flex-col gap-10">
      <section
        className="grid items-center gap-6 pt-4 sm:pt-8 md:grid-cols-[1.25fr_1fr]"
        aria-labelledby="hero-heading"
      >
        <div className="flex flex-col gap-4">
          <div>
            <Pill tone="accent">For students with big plans</Pill>
          </div>
          <h1 id="hero-heading" className="text-[40px] leading-[1.05] font-bold sm:text-[52px]">
            Plan your degree around your goals.
          </h1>
          <p className="text-muted max-w-[60ch] text-lg">
            Tell us your major and where you want your career to go. We build your courses and path
            to graduation from your university&apos;s own course catalog and your degree
            requirements, so every class counts. We also find the career fairs and events that match
            your major and goals, and suggest professional and social clubs where you&apos;ll find
            your people. All fitted around your work and life.
          </p>
          <div className="flex flex-wrap gap-3">
            <ButtonLink href="/demo">See a sample plan</ButtonLink>
          </div>
          <p className="text-muted text-sm">Now in a small pilot. Sign-up opens soon.</p>
        </div>
        <HeroArt className="h-auto w-full" />
      </section>

      <section className="flex flex-col gap-3" aria-labelledby="how-heading">
        <h2 id="how-heading" className="text-2xl font-bold">
          How it works
        </h2>
        <ol className="grid gap-3 sm:grid-cols-3">
          {steps.map((step, index) => (
            <li
              key={step.title}
              className="bg-surface flex flex-col gap-2 rounded-[var(--radius-card)] p-[18px]"
            >
              <StepIcon name={step.icon} />
              <span className="text-accent font-display text-sm font-bold">Step {index + 1}</span>
              <h3 className="text-lg leading-tight font-bold">{step.title}</h3>
              <p className="text-muted text-[15px]">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex flex-col gap-3" aria-labelledby="peek-heading">
        <div className="flex flex-col gap-1">
          <h2 id="peek-heading" className="text-2xl font-bold">
            A peek at a plan
          </h2>
          <p className="text-muted text-[15px]">From our sample student. Yours is built for you.</p>
        </div>
        <div className="grid items-start gap-3 sm:grid-cols-2">
          <ProgressCard progress={sampleDashboard.progress} />
          <NextTermCard courses={sampleDashboard.nextTerm} />
        </div>
      </section>

      <Card title="Your data stays yours" labelledBy="privacy-heading">
        <ul className="text-muted flex list-disc flex-col gap-1.5 pl-5 text-[15px]">
          <li>We never ask for your school password.</li>
          <li>Your uploaded progress report is read once to find your courses, then deleted.</li>
          <li>Your name, student ID and GPA are removed before anything reaches our AI.</li>
          <li>&ldquo;Delete my account&rdquo; removes everything we have about you.</li>
        </ul>
      </Card>
    </div>
  );
}

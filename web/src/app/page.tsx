import Link from "next/link";

import { StepIcon } from "@/components/art";
import { HeroSceneNarrow, HeroSceneWide, Hill, StarField } from "@/components/night";
import { NextTermCard, ProgressCard } from "@/components/dashboard";
import { ButtonLink, Card, Logo, Pill } from "@/components/ui";
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
    <div className="theme-dark bg-bg text-ink relative flex flex-1 flex-col">
      <header className="absolute inset-x-0 top-0 z-10 mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 pt-5 sm:px-8">
        <Link href="/" aria-label="Beyond the Syllabus home" className="rounded-[10px]">
          <Logo />
        </Link>
        <nav aria-label="Main">
          <Link
            href="/demo"
            className="text-accent font-bold whitespace-nowrap underline-offset-2 hover:underline"
          >
            Sample plan
          </Link>
        </nav>
      </header>

      <main id="main" className="flex flex-1 flex-col">
        <section
          className="from-night to-night-deep relative overflow-hidden bg-linear-to-b"
          aria-labelledby="hero-heading"
        >
          <StarField className="pointer-events-none absolute inset-0 size-full" />
          <Hill className="pointer-events-none absolute inset-x-0 bottom-0 h-14 w-full md:h-24" />
          <div className="relative mx-auto grid w-full max-w-6xl items-end px-4 pt-24 sm:px-8 md:grid-cols-[1.15fr_1fr] md:gap-8 md:pt-28">
            <div className="flex flex-col gap-4 pb-6 md:self-center md:pb-24">
              <div>
                <Pill tone="accent">For students with big plans</Pill>
              </div>
              <h1
                id="hero-heading"
                className="text-starlight text-[40px] leading-[1.04] font-bold sm:text-[56px]"
              >
                Plan your degree around your goals.
              </h1>
              <p className="text-muted max-w-[60ch] text-lg">
                Tell us your major and where you want your career to go. We build your courses and
                path to graduation from your university&apos;s own course catalog and your degree
                requirements, so every class counts. We also find the career fairs and events that
                match your major and goals, and suggest professional and social clubs where
                you&apos;ll find your people. All fitted around your work and life.
              </p>
              <div className="flex flex-wrap gap-3">
                <ButtonLink href="/demo">See a sample plan</ButtonLink>
              </div>
              <p className="text-muted text-sm">Now in a small pilot. Sign-up opens soon.</p>
            </div>
            <HeroSceneWide className="hidden h-auto w-full md:block" />
            <HeroSceneNarrow className="-mx-4 h-auto w-[calc(100%+2rem)] max-w-none sm:-mx-8 sm:w-[calc(100%+4rem)] md:hidden" />
          </div>
        </section>

        <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 px-4 pt-10 pb-12 sm:px-5">
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
                  <span className="text-accent font-display text-sm font-bold">
                    Step {index + 1}
                  </span>
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
              <p className="text-muted text-[15px]">
                From our sample student. Yours is built for you.
              </p>
            </div>
            <div className="grid items-start gap-3 sm:grid-cols-2">
              <ProgressCard progress={sampleDashboard.progress} />
              <NextTermCard courses={sampleDashboard.nextTerm} />
            </div>
          </section>

          <Card title="Your data stays yours" labelledBy="privacy-heading">
            <ul className="text-muted flex list-disc flex-col gap-1.5 pl-5 text-[15px]">
              <li>We never ask for your school password.</li>
              <li>
                Your uploaded progress report is read once to find your courses, then deleted.
              </li>
              <li>Your name, student ID and GPA are removed before anything reaches our AI.</li>
              <li>&ldquo;Delete my account&rdquo; removes everything we have about you.</li>
            </ul>
          </Card>
        </div>
      </main>

      <footer className="text-muted mx-auto w-full max-w-3xl px-4 pb-8 text-sm sm:px-5">
        Beyond the Syllabus is an independent student project, not affiliated with any university.
        Always confirm your plan with your academic advisor.
      </footer>
    </div>
  );
}

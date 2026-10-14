import { ButtonLink, Card, Pill } from "@/components/ui";

const steps = [
  {
    title: "Tell us where you are",
    body: "Pick your school and major, then upload the degree progress report your school gives you, or tick the courses you've done.",
  },
  {
    title: "Draw your week",
    body: "Mark your work shifts, commute and anything else that's fixed. Classes are planned around them.",
  },
  {
    title: "Get your plan",
    body: "Next term's courses, your path to graduation, clubs and career events, each with the reason it was picked, ready for your calendar.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-4 pt-4 sm:pt-10" aria-labelledby="hero-heading">
        <Pill tone="accent">For students with big plans</Pill>
        <h1 id="hero-heading" className="text-[40px] leading-[1.05] font-bold sm:text-[56px]">
          Plan your degree around your goals, not the other way round.
        </h1>
        <p className="text-muted max-w-[60ch] text-lg">
          Tell us where you want your career to go. Beyond the Syllabus builds the courses, the path
          to graduation, and the clubs and career events that get you there faster, from your
          program&apos;s real rules and fitted around your work and life.
        </p>
        <div className="flex flex-wrap gap-3">
          <ButtonLink href="/demo">See a sample plan</ButtonLink>
        </div>
        <p className="text-muted text-sm">Now in a small pilot. Sign-up opens soon.</p>
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
              <span className="text-accent font-display text-sm font-bold">Step {index + 1}</span>
              <h3 className="text-lg leading-tight font-bold">{step.title}</h3>
              <p className="text-muted text-[15px]">{step.body}</p>
            </li>
          ))}
        </ol>
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

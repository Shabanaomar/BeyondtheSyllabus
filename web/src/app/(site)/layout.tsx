import Link from "next/link";

import { Logo } from "@/components/ui";

/** The calm planner shell: the sample plan, the style guide and (later) the signed-in app. */
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 pt-5 pb-2 sm:px-5">
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
      <main
        id="main"
        className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pt-3 pb-12 sm:px-5"
      >
        {children}
      </main>
      <SiteFooter />
    </>
  );
}

function SiteFooter() {
  return (
    <footer className="text-muted mx-auto w-full max-w-3xl px-4 pb-8 text-sm sm:px-5">
      Beyond the Syllabus is an independent student project, not affiliated with any university.
      Always confirm your plan with your academic advisor.
    </footer>
  );
}

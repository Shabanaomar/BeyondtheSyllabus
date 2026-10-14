import type { Metadata, Viewport } from "next";
import Link from "next/link";

import { Logo } from "@/components/ui";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Beyond the Syllabus", template: "%s · Beyond the Syllabus" },
  description:
    "Plan your engineering degree around your job: next-term courses, a path to graduation, clubs and career events, in your calendar.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2f1f7" },
    { media: "(prefers-color-scheme: dark)", color: "#16131f" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="bg-accent text-on-accent sr-only rounded-full px-4 py-2 focus:not-sr-only focus:absolute focus:top-3 focus:left-3"
        >
          Skip to content
        </a>
        <header className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 pt-5 pb-2 sm:px-5">
          <Link href="/" aria-label="Beyond the Syllabus home" className="rounded-[10px]">
            <Logo />
          </Link>
          <nav aria-label="Main">
            <Link href="/demo" className="text-accent font-bold underline-offset-2 hover:underline">
              See a sample plan
            </Link>
          </nav>
        </header>
        <main
          id="main"
          className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pt-3 pb-12 sm:px-5"
        >
          {children}
        </main>
        <footer className="text-muted mx-auto w-full max-w-3xl px-4 pb-8 text-sm sm:px-5">
          Beyond the Syllabus is an independent student project, not affiliated with Fresno State or
          UC Berkeley. Always confirm your plan with your academic advisor.
        </footer>
      </body>
    </html>
  );
}

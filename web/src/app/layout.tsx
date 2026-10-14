import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Beyond the Syllabus", template: "%s · Beyond the Syllabus" },
  description:
    "Plan your degree around your goals: next-term courses, a path to graduation, clubs and career events, in your calendar.",
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
          className="bg-accent text-on-accent sr-only rounded-full px-4 py-2 focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-10"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}

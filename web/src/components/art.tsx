/**
 * Original brand art: the logo mark and the landing illustrations. All decorative (aria-hidden),
 * drawn with theme colors so they follow light and dark mode. No university marks or colors.
 */

import type { ReactNode } from "react";

/** An open book whose path leaves the page and ends at a star: going beyond the syllabus. */
export function LogoMark({ className = "size-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true" focusable="false">
      <rect width="32" height="32" rx="9" className="fill-accent" />
      <path
        d="M7 22.5c3-2 6-2 9 0 3-2 6-2 9 0"
        className="stroke-on-accent"
        strokeWidth="2.2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 20.5c0-5 2.5-8 5.5-9.5"
        className="stroke-on-accent"
        strokeWidth="2.2"
        fill="none"
        strokeLinecap="round"
        strokeDasharray="0.1 3.6"
      />
      <path
        d="M23.5 5.5l1.1 2.6 2.6 1.1-2.6 1.1-1.1 2.6-1.1-2.6-2.6-1.1 2.6-1.1z"
        className="fill-on-accent"
      />
    </svg>
  );
}

function Chip({ x, y, w, label }: { x: number; y: number; w: number; label: string }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height="28" rx="14" className="fill-surface stroke-line" />
      <text
        x={x + w / 2}
        y={y + 19}
        textAnchor="middle"
        className="fill-ink font-sans"
        fontSize="15"
        fontWeight="700"
      >
        {label}
      </text>
    </g>
  );
}

function Marker({ x, y, children }: { x: number; y: number; children: ReactNode }) {
  return (
    <g>
      <circle cx={x} cy={y} r="15" className="fill-surface stroke-accent" strokeWidth="3" />
      <g
        transform={`translate(${x - 8} ${y - 8})`}
        className="stroke-accent"
        fill="none"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {children}
      </g>
    </g>
  );
}

/** A path from "you, today" over the hills, past courses, clubs and a career fair, to your goal. */
export function HeroArt({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 480 360" className={className} aria-hidden="true" focusable="false">
      <defs>
        <clipPath id="hero-art-frame">
          <rect width="480" height="360" rx="24" />
        </clipPath>
      </defs>
      <g clipPath="url(#hero-art-frame)">
        <rect width="480" height="360" className="fill-surface" />
        <circle cx="402" cy="86" r="46" className="fill-warm-soft" />
        <path
          d="M40 70l2 5 5 2-5 2-2 5-2-5-5-2 5-2zM120 40l1.5 3.5 3.5 1.5-3.5 1.5-1.5 3.5-1.5-3.5-3.5-1.5 3.5-1.5zM250 72l1.5 3.5 3.5 1.5-3.5 1.5-1.5 3.5-1.5-3.5-3.5-1.5 3.5-1.5z"
          className="fill-accent"
          opacity="0.7"
        />
        <path
          d="M0 250C90 190 195 210 285 180c75-25 135-60 195-30v210H0z"
          className="fill-lilac-soft"
        />
        <path
          d="M0 300c105-40 225 0 330-50 70-25 120-15 150-10v120H0z"
          className="fill-accent-soft"
        />
        <path
          d="M30 340c75-20 60-70 135-70 75 0 83-30 105-48 30-24 82-42 120-72"
          className="stroke-accent"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="0.1 11"
          fill="none"
        />
        <circle cx="30" cy="340" r="8" className="fill-ink" />

        <Marker x={165} y={270}>
          <path d="M1 3c3-1.5 5-1.5 7 0v11c-2-1.5-4-1.5-7 0zM15 3c-3-1.5-5-1.5-7 0v11c2-1.5 4-1.5 7 0z" />
        </Marker>
        <Marker x={270} y={222}>
          <circle cx="5" cy="5" r="2.5" />
          <circle cx="11.5" cy="5" r="2.5" />
          <path d="M0.5 14c0-3 2-5 4.5-5s4.5 2 4.5 5M7.5 14c0-3 1.7-5 4-5s4 2 4 5" />
        </Marker>
        <Marker x={327} y={188}>
          <rect x="1" y="5" width="14" height="9" rx="2" />
          <path d="M5.5 5V3h5v2" />
        </Marker>

        <path d="M390 150v-46" className="stroke-ink" strokeWidth="3" strokeLinecap="round" />
        <path d="M391 104h30l-7 9 7 9h-30z" className="fill-accent" />

        <Chip x={16} y={282} w={104} label="You, today" />
        <Chip x={117} y={220} w={96} label="Next term" />
        <Chip x={240} y={244} w={66} label="Clubs" />
        <Chip x={262} y={137} w={104} label="Career fair" />
        <Chip x={380} y={166} w={92} label="Your goal" />
      </g>
    </svg>
  );
}

const stepIconPaths = {
  you: (
    <>
      <path d="M12 21s-6-5.5-6-10.5a6 6 0 0 1 12 0C18 15.5 12 21 12 21z" />
      <circle cx="12" cy="10.5" r="2.2" />
    </>
  ),
  week: (
    <>
      <rect x="3.5" y="5" width="17" height="15" rx="3" />
      <path d="M3.5 10h17M8.5 3v4M15.5 3v4M8 14h3M13 14h3M8 17h3" />
    </>
  ),
  goal: (
    <>
      <path d="M5 21V4" />
      <path d="M5 4.5h12l-2.5 4 2.5 4H5" />
    </>
  ),
};

export function StepIcon({ name }: { name: keyof typeof stepIconPaths }) {
  return (
    <span className="bg-accent-soft text-on-accent-soft flex size-11 items-center justify-center rounded-full">
      <svg
        viewBox="0 0 24 24"
        className="size-6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
      >
        {stepIconPaths[name]}
      </svg>
    </span>
  );
}

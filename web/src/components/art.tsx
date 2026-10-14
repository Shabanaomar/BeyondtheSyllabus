/**
 * Original brand art: the logo mark and small illustrations. All decorative (aria-hidden). No
 * university marks or colors.
 */

/** The Bts mark: "Bts" with a path swooping up to a star. Brand colors, the same in both themes. */
export function LogoMark({ className = "size-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true" focusable="false">
      <circle cx="50" cy="50" r="49" className="fill-night stroke-night-line" strokeWidth="2" />
      <path
        d="M16 61V33.3H26.8Q29.3 33.3 31.3 33.7Q33.3 34.2 34.7 35.1Q36 36 36.7 37.3Q37.5 38.7 37.5 40.4Q37.5 42.1 36.8 43.5Q36.1 44.8 34.6 45.6Q33 46.5 30.5 46.7V47.1Q34.7 47.3 36.6 49Q38.6 50.8 38.6 53.7Q38.6 56.1 37.3 57.7Q36.1 59.3 33.7 60.2Q31.4 61 27.8 61ZM22 56.1H27.6Q30 56.1 31.3 55.2Q32.6 54.4 32.6 52.7Q32.6 50.9 31.1 50Q29.6 49.1 26.6 49.1H22ZM22 44.9H26.2Q28.8 44.9 30.2 44Q31.5 43.2 31.5 41.5Q31.5 39.8 30.2 39Q29 38.2 26.4 38.2H22ZM49.5 61.5Q45.8 61.5 44 59.6Q42.2 57.7 42.2 53.7V43.7H39.7V39.8H40Q42.3 39.5 43.3 38.3Q44.3 37 44.5 34.5L44.6 34H48.2V39H53.4V43.9H48.2V53.2Q48.2 54.8 48.9 55.5Q49.7 56.2 50.9 56.2Q51.5 56.2 52.2 56Q52.9 55.8 53.4 55.5V60.9Q52.2 61.2 51.2 61.4Q50.3 61.5 49.5 61.5Z"
        className="fill-starlight"
      />
      <path
        d="M65.5 61.6Q63.3 61.6 61.4 61.1Q59.6 60.7 58.2 59.7Q56.8 58.8 56.1 57.2Q55.4 55.5 55.5 53.3L60.8 52.8Q60.9 54.3 61.5 55.3Q62 56.3 63.1 56.7Q64.2 57.2 65.7 57.2Q67.3 57.2 68.3 56.6Q69.4 56.1 69.4 55Q69.4 54.2 68.9 53.8Q68.5 53.4 67.5 53.1Q66.5 52.7 64.8 52.3Q62.7 51.8 61 51.3Q59.4 50.8 58.1 50.1Q56.9 49.3 56.3 48.2Q55.6 47.1 55.6 45.5Q55.6 43.2 56.8 41.6Q58 40.1 60.2 39.2Q62.3 38.4 65.1 38.4Q67.6 38.4 69.7 39.2Q71.9 40 73.2 41.7Q74.4 43.5 74.1 46.5L68.9 47Q69.1 45.6 68.5 44.7Q68 43.8 67 43.3Q66.1 42.8 64.7 42.8Q63.1 42.8 62.2 43.4Q61.3 44 61.3 45Q61.3 45.8 61.9 46.3Q62.4 46.8 63.5 47.1Q64.7 47.4 66.3 47.8Q67.7 48.1 69.3 48.5Q70.8 49 72.1 49.7Q73.5 50.5 74.3 51.7Q75.1 53 75.1 54.9Q75.1 56.9 74 58.4Q72.9 59.9 70.7 60.8Q68.6 61.6 65.5 61.6Z"
        className="fill-trail"
      />
      <path
        d="M21 72c20 6 39 3 52-9"
        className="stroke-trail"
        strokeWidth="3.4"
        fill="none"
        strokeLinecap="round"
      />
      <path d="M80 47.5l2 5.5 5.5 2-5.5 2-2 5.5-2-5.5-5.5-2 5.5-2z" className="fill-goal" />
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

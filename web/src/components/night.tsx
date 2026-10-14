/**
 * The landing page night sky: a graduate reaching for her goal star, with the plan as the path
 * between them. Decorative only (aria-hidden): the same steps are described in the page text.
 * Colors are the brand night tokens in globals.css.
 */

/** Background stars: [x, y, radius, opacity] in a 1280 x 760 box. Fixed so server and client match. */
const STARS: [number, number, number, number][] = [
  [1043, 223, 0.7, 0.3],
  [892, 432, 0.7, 0.3],
  [1162, 130, 1, 0.75],
  [1197, 67, 1.7, 0.3],
  [456, 51, 1, 0.5],
  [862, 151, 0.7, 0.75],
  [879, 325, 1.7, 0.75],
  [932, 374, 1.3, 0.3],
  [372, 719, 1, 0.3],
  [1180, 311, 1.7, 0.5],
  [923, 298, 0.7, 0.3],
  [1052, 432, 1, 0.5],
  [1221, 512, 1.7, 0.3],
  [916, 295, 1.7, 0.75],
  [714, 27, 1.7, 0.5],
  [1020, 86, 1, 0.5],
  [826, 566, 1.3, 0.3],
  [885, 567, 1.3, 0.75],
  [854, 371, 1.7, 0.3],
  [997, 607, 1, 0.5],
  [581, 8, 1, 0.5],
  [1098, 382, 1.3, 0.3],
  [1059, 636, 0.7, 0.5],
  [1149, 405, 1.7, 0.5],
  [811, 110, 1.7, 0.75],
  [824, 67, 1, 0.3],
  [4, 584, 1, 0.75],
  [715, 620, 1.3, 0.5],
  [958, 495, 1.7, 0.5],
  [705, 275, 1.7, 0.75],
  [1085, 374, 1, 0.75],
  [1116, 31, 1.3, 0.75],
  [190, 716, 1.3, 0.75],
  [755, 175, 1.3, 0.3],
  [1094, 558, 1.3, 0.75],
  [732, 752, 0.7, 0.3],
  [1243, 356, 1.7, 0.75],
  [719, 377, 0.7, 0.3],
  [1253, 5, 1.7, 0.75],
  [708, 662, 0.7, 0.75],
  [412, 493, 1, 0.3],
  [814, 478, 1.7, 0.75],
  [177, 746, 1, 0.3],
  [264, 32, 1, 0.75],
  [957, 675, 1, 0.75],
  [1224, 489, 1.3, 0.3],
  [1127, 565, 1, 0.3],
  [33, 747, 0.7, 0.75],
  [289, 448, 1, 0.3],
  [1030, 250, 1.3, 0.5],
  [1118, 433, 1, 0.3],
  [728, 473, 1.7, 0.75],
  [1049, 23, 1.7, 0.3],
  [1250, 8, 1, 0.3],
  [1065, 547, 1.7, 0.3],
  [1151, 62, 1, 0.3],
  [571, 47, 0.7, 0.75],
  [930, 579, 0.7, 0.3],
  [911, 337, 1, 0.75],
  [983, 523, 1, 0.75],
  [1075, 269, 1, 0.5],
  [909, 327, 0.7, 0.75],
  [624, 129, 1, 0.3],
  [753, 150, 1.3, 0.3],
  [961, 228, 0.7, 0.5],
  [1001, 170, 1, 0.3],
  [887, 531, 1.7, 0.5],
  [866, 204, 1.3, 0.5],
  [192, 743, 1.3, 0.3],
  [609, 528, 0.7, 0.3],
  [1058, 588, 1.7, 0.75],
  [379, 439, 1, 0.3],
  [1136, 431, 1.3, 0.75],
  [268, 48, 1, 0.3],
  [1091, 214, 1.3, 0.5],
  [1028, 692, 1, 0.5],
  [714, 22, 1.3, 0.3],
  [35, 22, 1, 0.75],
  [976, 255, 1.7, 0.3],
  [889, 676, 1.7, 0.75],
  [809, 522, 1.3, 0.75],
  [290, 418, 0.7, 0.3],
  [33, 76, 1.3, 0.5],
  [784, 522, 1.3, 0.75],
  [500, 713, 1.3, 0.3],
  [944, 193, 1, 0.5],
  [917, 7, 1.3, 0.5],
  [378, 5, 1.3, 0.5],
  [14, 97, 1.3, 0.3],
  [810, 27, 1.3, 0.5],
  [1087, 162, 1.7, 0.5],
  [1016, 157, 1.3, 0.75],
  [1271, 662, 1, 0.3],
  [1054, 646, 1.7, 0.75],
  [1039, 146, 0.7, 0.75],
  [1200, 732, 1, 0.3],
  [67, 46, 1, 0.75],
  [742, 111, 1.7, 0.5],
  [1147, 55, 0.7, 0.75],
  [1092, 701, 1, 0.5],
  [544, 7, 1.7, 0.3],
  [1034, 552, 0.7, 0.75],
  [1081, 71, 1.7, 0.5],
  [946, 509, 1.7, 0.3],
  [985, 704, 1.3, 0.3],
  [1267, 651, 1, 0.3],
  [1232, 154, 1.3, 0.5],
  [29, 497, 0.7, 0.5],
  [1061, 296, 1.7, 0.5],
  [959, 125, 1, 0.5],
  [943, 82, 1.7, 0.5],
  [796, 218, 1, 0.3],
  [1194, 96, 1, 0.75],
  [1077, 272, 1.3, 0.3],
  [1239, 650, 1.3, 0.3],
  [751, 240, 1.7, 0.5],
  [811, 29, 1, 0.3],
  [1010, 701, 1.7, 0.5],
  [622, 748, 1, 0.5],
  [708, 389, 1.3, 0.3],
  [682, 5, 1.3, 0.5],
  [819, 126, 1, 0.75],
  [28, 300, 1.3, 0.5],
  [1210, 82, 1.3, 0.5],
  [567, 53, 1.3, 0.3],
  [308, 259, 1, 0.3],
  [880, 33, 1.7, 0.75],
  [1128, 212, 0.7, 0.3],
  [845, 465, 1, 0.75],
  [1130, 134, 1, 0.5],
  [853, 355, 1.3, 0.5],
  [811, 126, 1, 0.75],
  [1022, 567, 1, 0.5],
  [1125, 201, 1, 0.3],
  [1170, 210, 0.7, 0.75],
  [849, 396, 1.7, 0.75],
  [1077, 219, 1.7, 0.5],
  [1180, 372, 1, 0.75],
  [1034, 545, 1, 0.3],
  [917, 446, 1.3, 0.3],
  [264, 37, 1.7, 0.75],
  [973, 605, 1.7, 0.3],
  [153, 404, 1, 0.3],
  [315, 538, 0.7, 0.3],
  [940, 91, 0.7, 0.3],
  [899, 719, 0.7, 0.3],
  [1197, 200, 1.7, 0.5],
  [1104, 312, 1.7, 0.5],
  [1124, 256, 0.7, 0.5],
  [1024, 694, 1.7, 0.3],
  [762, 236, 1.7, 0.3],
  [696, 739, 1.7, 0.5],
  [815, 206, 0.7, 0.5],
  [1037, 73, 1, 0.5],
  [1019, 628, 1, 0.3],
  [997, 431, 0.7, 0.75],
  [110, 730, 0.7, 0.3],
  [809, 464, 1.3, 0.75],
  [235, 85, 1, 0.3],
  [383, 672, 1, 0.3],
  [769, 343, 1.7, 0.3],
  [227, 6, 0.7, 0.5],
  [257, 578, 1, 0.3],
  [734, 320, 1.7, 0.3],
  [104, 726, 1.7, 0.3],
  [767, 558, 1.7, 0.3],
  [975, 35, 1.7, 0.3],
  [832, 45, 1.7, 0.3],
  [954, 68, 0.7, 0.5],
  [403, 68, 1, 0.3],
];

export function StarField({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 1280 760"
      preserveAspectRatio="xMidYMid slice"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {STARS.map(([x, y, r, o], i) => (
        <circle
          key={i}
          cx={x}
          cy={y}
          r={r}
          opacity={o}
          className={`fill-starlight ${i % 9 === 0 ? "motion-safe:animate-[twinkle_4s_ease-in-out_infinite]" : ""}`}
          style={i % 9 === 0 ? { animationDelay: `${(i % 7) * 0.6}s` } : undefined}
        />
      ))}
      <line
        x1="1180"
        y1="60"
        x2="1108"
        y2="114"
        strokeWidth="1.6"
        strokeLinecap="round"
        className="stroke-starlight"
        opacity="0.5"
      />
      <line
        x1="760"
        y1="40"
        x2="712"
        y2="76"
        strokeWidth="1.4"
        strokeLinecap="round"
        className="stroke-starlight"
        opacity="0.35"
      />
    </svg>
  );
}

function Star({ x, y, r, className }: { x: number; y: number; r: number; className: string }) {
  const k = r * 0.26;
  return (
    <path
      d={`M${x} ${y - r}L${x + k} ${y - k}L${x + r} ${y}L${x + k} ${y + k}L${x} ${y + r}L${x - k} ${y + k}L${x - r} ${y}L${x - k} ${y - k}Z`}
      className={className}
    />
  );
}

function Chip({
  x,
  y,
  label,
  end = false,
  goal = false,
}: {
  x: number;
  y: number;
  label: string;
  end?: boolean;
  goal?: boolean;
}) {
  const w = label.length * 8 + 22;
  const left = end ? x - w : x;
  return (
    <g>
      <rect
        x={left}
        y={y}
        width={w}
        height="26"
        rx="13"
        className={goal ? "fill-goal" : "fill-chip stroke-night-line"}
      />
      <text
        x={left + w / 2}
        y={y + 17.5}
        textAnchor="middle"
        fontSize="13"
        fontWeight="700"
        className={`font-sans ${goal ? "fill-on-goal" : "fill-starlight"}`}
      >
        {label}
      </text>
    </g>
  );
}

/** A graduate in cap and gown, seen from behind, one arm raised toward the sky. */
function Graduate({ x, y, scale }: { x: number; y: number; scale: number }) {
  const rim = { className: "fill-silhouette stroke-trail", strokeOpacity: 0.35, strokeWidth: 1.6 };
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path
        d="M126 140C140 170 150 220 154 262C146 268 134 268 128 262C126 220 122 190 118 165Z"
        {...rim}
      />
      <path
        d="M40 330C40 260 46 190 52 150C56 128 70 118 90 116C110 118 124 128 128 150C134 190 140 260 140 330Z"
        {...rim}
      />
      <path d="M62 132C48 110 34 80 20 50L8 56C20 90 34 124 48 156Z" {...rim} />
      <circle cx="13" cy="46" r="7" {...rim} />
      <ellipse cx="90" cy="86" rx="20" ry="22" className="fill-silhouette" />
      <path
        d="M70 80C62 112 60 142 66 170C72 182 82 187 90 187C98 187 108 182 114 170C120 142 118 112 110 80Z"
        {...rim}
      />
      <path
        d="M78 100C76 130 78 160 82 180M100 100C103 130 102 160 98 180"
        strokeWidth="2"
        fill="none"
        className="stroke-night-deep"
      />
      <path d="M72 68Q90 78 110 66L108 80Q90 88 74 80Z" className="fill-silhouette" />
      <polygon points="54,64 92,50 130,62 92,78" className="fill-chip" />
      <path
        d="M92 64L126 64L128 90"
        strokeWidth="2.2"
        fill="none"
        strokeLinecap="round"
        className="stroke-goal"
      />
      <rect x="125" y="88" width="6" height="12" rx="2" className="fill-goal" />
    </g>
  );
}

function Gradients({ id }: { id: string }) {
  return (
    <defs>
      <radialGradient id={`${id}-glow`}>
        <stop offset="0" stopColor="var(--goal)" stopOpacity="0.35" />
        <stop offset="1" stopColor="var(--goal)" stopOpacity="0" />
      </radialGradient>
      <linearGradient id={`${id}-trail`} x1="1" y1="1" x2="0" y2="0">
        <stop offset="0" stopColor="var(--trail)" stopOpacity="0" />
        <stop offset="0.5" stopColor="var(--trail)" stopOpacity="0.85" />
        <stop offset="1" stopColor="var(--goal)" />
      </linearGradient>
    </defs>
  );
}

/** The hill she stands on, stretched across the full width of the hero. */
export function Hill({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 1280 100"
      preserveAspectRatio="none"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path d="M0 100V72C300 34 700 12 1000 30S1220 52 1280 44V100Z" className="fill-silhouette" />
    </svg>
  );
}

/** Wide screens: the scene sits to the right of the headline. */
export function HeroSceneWide({ className }: { className?: string }) {
  return (
    <svg viewBox="720 40 560 720" className={className} aria-hidden="true" focusable="false">
      <Gradients id="wide" />
      <circle cx="880" cy="150" r="140" fill="url(#wide-glow)" />
      <path
        d="M960 566C990 540 1040 510 1030 480S985 425 990 400S1025 350 1020 330S980 285 975 265S945 222 930 205S895 168 880 150"
        stroke="url(#wide-trail)"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
      />
      <Star x={1030} y={480} r={7} className="fill-trail" />
      <Chip x={1046} y={468} label="Academic plan" />
      <Star x={990} y={400} r={7.5} className="fill-trail" />
      <Chip x={1006} y={388} label="Student organizations" />
      <Star x={1020} y={330} r={8} className="fill-trail" />
      <Chip x={1036} y={318} label="Networking" />
      <Star x={975} y={265} r={8.5} className="fill-trail" />
      <Chip x={991} y={253} label="Professional development" />
      <Star x={930} y={205} r={9.5} className="fill-trail" />
      <Chip x={946} y={193} label="Career fair" />
      <Star x={880} y={150} r={22} className="fill-goal" />
      <Chip x={912} y={104} label="Your dream job" goal />
      <Graduate x={950} y={526} scale={0.72} />
    </svg>
  );
}

/** Phones: the scene sits under the headline, reading bottom (her) to top (the goal). */
export function HeroSceneNarrow({ className }: { className?: string }) {
  return (
    <svg viewBox="0 540 390 520" className={className} aria-hidden="true" focusable="false">
      <Gradients id="narrow" />
      <circle cx="80" cy="620" r="90" fill="url(#narrow-glow)" />
      <path
        d="M239 892C262 872 284 860 272 846S228 815 232 800S266 770 262 756S210 730 200 716S165 690 150 672S100 638 80 620"
        stroke="url(#narrow-trail)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <Star x={272} y={846} r={6.5} className="fill-trail" />
      <Chip x={258} y={834} label="Academic plan" end />
      <Star x={232} y={800} r={7} className="fill-trail" />
      <Chip x={246} y={788} label="Organizations" />
      <Star x={262} y={756} r={7.5} className="fill-trail" />
      <Chip x={276} y={744} label="Networking" />
      <Star x={200} y={716} r={8} className="fill-trail" />
      <Chip x={186} y={704} label="Pro development" end />
      <Star x={150} y={672} r={8.5} className="fill-trail" />
      <Chip x={136} y={660} label="Career fair" end />
      <Star x={80} y={620} r={18} className="fill-goal" />
      <Chip x={106} y={566} label="Your dream job" goal />
      <Graduate x={232} y={866} scale={0.58} />
    </svg>
  );
}

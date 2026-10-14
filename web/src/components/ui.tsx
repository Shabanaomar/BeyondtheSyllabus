import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

import { LogoMark } from "@/components/art";

/** Shared building blocks. Colors come only from the design tokens in globals.css. */

export function Card({
  title,
  aside,
  children,
  as: Tag = "section",
  labelledBy,
}: {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  as?: "section" | "div";
  labelledBy?: string;
}) {
  return (
    <Tag
      className="bg-surface flex min-w-0 flex-col gap-3 rounded-[var(--radius-card)] p-[18px]"
      aria-labelledby={labelledBy}
    >
      {title ? (
        <div className="flex items-baseline justify-between gap-3">
          <h2 id={labelledBy} className="text-lg leading-tight font-bold">
            {title}
          </h2>
          {aside ? <div className="text-muted shrink-0 text-sm">{aside}</div> : null}
        </div>
      ) : null}
      {children}
    </Tag>
  );
}

const tones = {
  accent: "bg-accent-soft text-on-accent-soft",
  warm: "bg-warm-soft text-on-warm-soft",
  lilac: "bg-lilac-soft text-on-lilac-soft",
  critical: "bg-critical-soft text-critical",
} as const;

export type Tone = keyof typeof tones;

export function Pill({ tone = "lilac", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[13px] leading-tight ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

const buttonBase =
  "inline-flex min-h-[48px] items-center justify-center rounded-full px-6 text-base font-bold transition-colors";
const buttonKinds = {
  primary: "bg-accent text-on-accent hover:bg-accent-hover",
  secondary: "bg-surface text-ink ring-1 ring-line hover:bg-surface-soft",
} as const;

export function ButtonLink({
  kind = "primary",
  className = "",
  ...props
}: ComponentProps<typeof Link> & { kind?: keyof typeof buttonKinds }) {
  return <Link {...props} className={`${buttonBase} ${buttonKinds[kind]} ${className}`} />;
}

export function Button({
  kind = "primary",
  className = "",
  type = "button",
  ...props
}: ComponentProps<"button"> & { kind?: keyof typeof buttonKinds }) {
  return (
    <button
      {...props}
      type={type}
      className={`${buttonBase} ${buttonKinds[kind]} cursor-pointer disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    />
  );
}

/** A ring showing a share of something done (for example units toward graduation). */
export function ProgressRing({ value, label }: { value: number; label: string }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div
      role="img"
      aria-label={label}
      className="flex size-[76px] shrink-0 items-center justify-center rounded-full"
      style={{
        background: `conic-gradient(var(--accent) 0 ${pct}%, var(--lilac-soft) ${pct}% 100%)`,
      }}
    >
      <div className="bg-surface font-display flex size-14 items-center justify-center rounded-full text-lg font-bold">
        {pct}%
      </div>
    </div>
  );
}

export function Notice({ children }: { children: ReactNode }) {
  return <p className="text-muted text-center text-sm">{children}</p>;
}

export function Logo() {
  return (
    <span className="flex items-center gap-2">
      <LogoMark className="size-8" />
      <span className="font-display text-[17px] font-bold whitespace-nowrap">
        Beyond the Syllabus
      </span>
    </span>
  );
}

# Design: Calm planner

Direction B, chosen by the founder on 2026-10-14. Calm, friendly and readable: the student should
feel "I've got this" within a minute. Independent brand: no university logos, seals or colors.

## Tokens

All colors live in `src/app/globals.css` as CSS variables, with light values on `:root` and dark
values for both `prefers-color-scheme: dark` and `[data-theme="dark"]`. Components use them only
through the Tailwind names below, never literal colors.

| Token                           | Tailwind                             | Used for                                     |
| ------------------------------- | ------------------------------------ | -------------------------------------------- |
| `--bg`                          | `bg-bg`                              | Page background (soft lilac-grey)            |
| `--surface`                     | `bg-surface`                         | Cards                                        |
| `--surface-soft`                | `bg-surface-soft`                    | Panels inside cards (course rows)            |
| `--ink` / `--muted`             | `text-ink` / `text-muted`            | Text / secondary text                        |
| `--line`                        | `ring-line`                          | Dividers and outlines                        |
| `--accent`                      | `bg-accent`, `text-accent`           | Primary buttons, links, progress (evergreen) |
| `--accent-soft`                 | `bg-accent-soft text-on-accent-soft` | Class pills                                  |
| `--warm-soft`                   | `bg-warm-soft text-on-warm-soft`     | Labs, career events, notices                 |
| `--lilac-soft`                  | `bg-lilac-soft text-on-lilac-soft`   | Work shifts and other fixed time             |
| `--critical`, `--critical-soft` | `text-critical`, `bg-critical-soft`  | Clashes and problems                         |
| `--focus`                       | (outline)                            | Keyboard focus ring                          |

Contrast, checked for every text/background pair: the lowest is 5.3:1 (light) and 6.6:1 (dark),
above WCAG AA's 4.5:1.

## Type

- **Display:** Bricolage Grotesque (variable), for headings: page title 30px, card titles 18px.
- **Body:** Atkinson Hyperlegible, designed for readability: 16px body, 13px details.
- Both are bundled from npm (`@fontsource`), so no request goes to Google.

## Shape and spacing

Cards: 18px radius, 18px padding, no borders or shadows (the white card on the tinted page does
the separating). Inner panels 12px radius. Pills and buttons fully rounded. Buttons are at least
48px tall. Gaps of 16px between cards, 12px inside.

## Components

`src/components/ui.tsx`: `Card`, `Pill`, `Button`, `ButtonLink`, `ProgressRing`, `Notice`, `Logo`.
`src/components/dashboard.tsx`: `ProgressCard`, `WeekCard`, `NextTermCard`, `ClubsCard`,
`EventsCard` and the whole `DashboardView`.

Every recommendation shows its reason in one line. Status is never shown by color alone: pills say
what they are ("Work", "Lab"), and the progress ring has a text label.

## See it

- `/demo`: the dashboard with a made-up student (labelled as a sample), plus a real `.ics`
  download built with the Fresno State spring 2027 dates.
- `/styleguide`: every token and component, in development only (`npm run dev`).

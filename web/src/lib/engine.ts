/**
 * Address of the planning engine, for server-side code only (route handlers, server components,
 * server actions). Never call this from a client component or from `proxy`.
 *
 * On Vercel, ENGINE_URL is injected by the `web` -> `engine` service binding in vercel.json and
 * points at the same deployment's engine, so previews talk to their own engine. Locally, set it
 * in web/.env.local (see .env.example) or run `vercel dev`, which injects it.
 */
export function engineUrl(path: string): URL {
  const base = process.env.ENGINE_URL;
  if (!base) {
    throw new Error("ENGINE_URL is not set. Run `vercel dev`, or set it in web/.env.local.");
  }
  return new URL(path.replace(/^\/+/, ""), base.endsWith("/") ? base : `${base}/`);
}

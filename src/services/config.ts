// Shared API base URL helper.
//
// `VITE_API_BASE_URL` may be configured as either:
// - backend root (e.g. https://...run.app)
// - backend api prefix (e.g. https://...run.app/api)
// - same-origin proxy (e.g. /api)
//
// This file normalizes it so the rest of the app can always use `API_URL`
// (which includes `/api` exactly once).

// In production we always talk to the backend via same-origin `/api` (Nginx proxy),
// so the browser never hits CORS issues.
const RAW_API_BASE_URL = import.meta.env.PROD
  ? "/api"
  : ((import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api");

function trimTrailingSlashes(url: string): string {
  return (url || "").trim().replace(/\/+$/, "");
}

function buildApiUrl(url: string): string {
  const trimmed = trimTrailingSlashes(url);
  if (!trimmed) return "";
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
}

export const API_URL = buildApiUrl(RAW_API_BASE_URL);

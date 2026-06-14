const DEFAULT_RELATIVE = "/api/v1";

/** Web hostname → full FastAPI base (includes /api/v1). */
const HOSTED_API_BASE: Record<string, string> = {
  "specwright-web-production.up.railway.app":
    "https://specwright-api-production.up.railway.app/api/v1",
  "specwright-web.onrender.com": "https://specwright-api.onrender.com/api/v1",
};

function isLocalHost(host: string): boolean {
  return host === "localhost" || host === "127.0.0.1";
}

/** Resolve Specwright API base for local dev, Render, and Railway static deploys. */
export function resolveSpecwrightApiBase(): string {
  const host = globalThis.window?.location?.hostname ?? "";

  if (HOSTED_API_BASE[host]) {
    return HOSTED_API_BASE[host];
  }

  const fromEnv = import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "";
  if (fromEnv) {
    return fromEnv.endsWith("/api/v1") ? fromEnv : `${fromEnv}/api/v1`;
  }

  if (isLocalHost(host)) {
    return DEFAULT_RELATIVE;
  }

  return (
    HOSTED_API_BASE[host] ??
    HOSTED_API_BASE["specwright-web-production.up.railway.app"] ??
    DEFAULT_RELATIVE
  );
}

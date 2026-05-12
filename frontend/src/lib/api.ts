export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Active org context (set from Clerk on app load) ── */
let _activeOrgId = "org_default";
let _authToken: string | null = null;

export function setActiveOrgId(orgId: string) {
  _activeOrgId = orgId;
}

export function getActiveOrgId(): string {
  return _activeOrgId;
}

export function setAuthToken(token: string | null) {
  _authToken = token;
}

function authHeaders(): Record<string, string> {
  return _authToken ? { Authorization: `Bearer ${_authToken}` } : {};
}

/* ── Case conversion helpers ── */

/**
 * Recursively convert all snake_case object keys to camelCase.
 * Arrays are traversed; primitives pass through unchanged.
 */
export function snakeToCamel(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date)) {
    return Object.keys(obj as Record<string, unknown>).reduce(
      (acc, key) => {
        const camelKey = key.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
        acc[camelKey] = snakeToCamel((obj as Record<string, unknown>)[key]);
        return acc;
      },
      {} as Record<string, unknown>,
    );
  }
  return obj;
}

/**
 * Recursively convert all camelCase object keys to snake_case.
 * Used for outgoing request bodies so the backend receives the format it expects.
 */
export function camelToSnake(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(camelToSnake);
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date)) {
    return Object.keys(obj as Record<string, unknown>).reduce(
      (acc, key) => {
        const snakeKey = key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
        acc[snakeKey] = camelToSnake((obj as Record<string, unknown>)[key]);
        return acc;
      },
      {} as Record<string, unknown>,
    );
  }
  return obj;
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Org-Id": _activeOrgId,
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  const data = await res.json();
  return snakeToCamel(data) as T;
}

/**
 * Fetch raw response (for file downloads / worklist generation).
 */
export async function apiRaw(path: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Org-Id": _activeOrgId,
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res;
}

/**
 * Upload a file via multipart form data.
 */
export async function apiUpload<T>(path: string, file: File, extraFields?: Record<string, string>): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  if (extraFields) {
    for (const [key, value] of Object.entries(extraFields)) {
      formData.append(key, value);
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body: formData,
    headers: {
      "X-Org-Id": _activeOrgId,
      ...authHeaders(),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  const data = await res.json();
  return snakeToCamel(data) as T;
}

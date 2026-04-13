export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Active org context (set from Clerk on app load) ── */
let _activeOrgId = "org_default";

export function setActiveOrgId(orgId: string) {
  _activeOrgId = orgId;
}

export function getActiveOrgId(): string {
  return _activeOrgId;
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Org-Id": _activeOrgId,
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
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
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

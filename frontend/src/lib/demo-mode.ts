let _isDemoMode: boolean | null = null;
let _healthCheckDone = false;

export function isDemoMode(): boolean {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") return true;
  if (_isDemoMode !== null) return _isDemoMode;
  return false;
}

export async function initDemoMode(): Promise<void> {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
    _isDemoMode = true;
    return;
  }

  if (_healthCheckDone) return;
  _healthCheckDone = true;

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${apiUrl}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    _isDemoMode = !res.ok;
  } catch {
    _isDemoMode = true;
  }
}

export function setDemoMode(value: boolean): void {
  _isDemoMode = value;
}

export function showErrorToast(action: string): void {
  if (typeof window !== "undefined") {
    const event = new CustomEvent("resonantia:toast", {
      detail: { type: "error", message: `Failed to ${action}. Changes not saved.` },
    });
    window.dispatchEvent(event);
  }
}

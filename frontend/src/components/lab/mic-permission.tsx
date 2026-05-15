"use client";

import { useEffect, useState } from "react";
import { Mic, ShieldAlert } from "lucide-react";

interface MicPermissionProps {
  onGranted?: () => void;
}

export function MicPermission({ onGranted }: MicPermissionProps) {
  const [state, setState] = useState<PermissionState | "unknown">("unknown");

  useEffect(() => {
    let mounted = true;
    async function readPermission() {
      try {
        const status = await navigator.permissions.query({ name: "microphone" as PermissionName });
        if (!mounted) return;
        setState(status.state);
        status.onchange = () => setState(status.state);
        if (status.state === "granted") onGranted?.();
      } catch {
        setState("prompt");
      }
    }
    void readPermission();
    return () => {
      mounted = false;
    };
  }, [onGranted]);

  async function requestMic() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setState("granted");
      onGranted?.();
    } catch {
      setState("denied");
    }
  }

  if (state === "granted") return null;

  return (
    <div className="mb-4 w-full max-w-sm rounded border border-line bg-bg-sunk px-3 py-3 text-sm text-ink-muted">
      <div className="mb-2 flex items-center gap-2 text-ink">
        {state === "denied" ? <ShieldAlert size={15} /> : <Mic size={15} />}
        <span>Microphone access</span>
      </div>
      <button
        type="button"
        onClick={requestMic}
        className="inline-flex items-center gap-1.5 rounded-[3px] bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-strong disabled:opacity-50"
        disabled={state === "denied"}
      >
        <Mic size={13} />
        {state === "denied" ? "Blocked in browser" : "Enable mic"}
      </button>
    </div>
  );
}

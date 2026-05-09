"use client";

import { useState } from "react";
import { Check, X, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

interface ApprovalCardProps {
  token: string;
  toolName: string;
  preview: Record<string, unknown>;
  gateKind: "soft_review" | "hard_approval";
  onResolved?: (status: "approved" | "rejected") => void;
}

export function ApprovalCard({
  token,
  toolName,
  preview,
  gateKind,
  onResolved,
}: ApprovalCardProps) {
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");
  const [loading, setLoading] = useState(false);

  const isHardApproval = gateKind === "hard_approval";

  async function handleApprove() {
    setLoading(true);
    try {
      await api(`/api/v1/chat/approve/${token}`, { method: "POST" });
      setStatus("approved");
      onResolved?.("approved");
    } catch {
      setStatus("rejected");
    } finally {
      setLoading(false);
    }
  }

  async function handleReject() {
    setLoading(true);
    try {
      await api(`/api/v1/chat/reject/${token}`, { method: "POST" });
      setStatus("rejected");
      onResolved?.("rejected");
    } catch {
      // Already expired or rejected
    } finally {
      setLoading(false);
    }
  }

  if (status === "approved") {
    return (
      <div className="rounded-md border border-brand/30 bg-brand-soft/30 px-4 py-3 text-sm text-brand">
        <Check size={14} className="inline mr-1.5" />
        {toolName} — approved and executed
      </div>
    );
  }

  if (status === "rejected") {
    return (
      <div className="rounded-md border border-line bg-bg-sunk px-4 py-3 text-sm text-ink-muted">
        <X size={14} className="inline mr-1.5" />
        {toolName} — cancelled
      </div>
    );
  }

  return (
    <div className="rounded-md border border-line bg-surface p-4 space-y-3">
      {isHardApproval && (
        <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
          <AlertTriangle size={14} />
          This action will be sent to an instrument. Please verify before confirming.
        </div>
      )}

      <div className="text-xs font-mono text-ink-subtle uppercase tracking-wider">
        {toolName}
      </div>

      <pre className="text-sm text-ink-muted bg-bg-sunk rounded p-3 overflow-x-auto max-h-48 overflow-y-auto">
        {JSON.stringify(preview, null, 2)}
      </pre>

      <div className="flex gap-2 pt-1">
        <button
          onClick={handleApprove}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand text-white text-sm font-medium rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-50"
        >
          <Check size={14} />
          Confirm
        </button>
        <button
          onClick={handleReject}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-4 py-2 border border-line text-ink-muted text-sm font-medium rounded-[3px] hover:border-ink hover:text-ink transition-colors disabled:opacity-50"
        >
          <X size={14} />
          Cancel
        </button>
      </div>
    </div>
  );
}

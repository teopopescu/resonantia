"use client";

import { useMemo, useState } from "react";
import {
  Plus,
  ChevronRight,
  Send,
  Copy,
  X,
} from "lucide-react";
import { useProtocolStore, type ProtocolStatus } from "@/stores/protocol-store";
import ProtocolStepBuilder from "@/components/lab/protocol-step-builder";
import InventoryChecker from "@/components/lab/inventory-checker";
import DilutionCalculator from "@/components/lab/dilution-calculator";
import {
  PageHeader,
  PageHeaderPrimary,
} from "@/components/lab/primitives/page-header";
import { KpiStrip, Kpi } from "@/components/lab/primitives/kpi-strip";
import { Chip } from "@/components/lab/primitives/data-table";
import { cn } from "@/lib/utils";

const STATUS_TONE: Record<ProtocolStatus, "default" | "brand" | "bf"> = {
  draft: "bf",
  published: "brand",
  archived: "default",
};

const inputBase =
  "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle";

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
    </label>
  );
}

export default function ProtocolsPage() {
  const {
    protocols,
    activeProtocolId,
    setActiveProtocol,
    createProtocol,
    publishProtocol,
    newVersion,
  } = useProtocolStore();

  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newIsTemplate, setNewIsTemplate] = useState(false);
  const [activeTab, setActiveTab] =
    useState<"steps" | "inventory" | "dilution">("steps");

  const stats = useMemo(
    () => ({
      total: protocols.length,
      templates: protocols.filter((p) => p.is_template).length,
      published: protocols.filter((p) => p.status === "published").length,
      drafts: protocols.filter((p) => p.status === "draft").length,
    }),
    [protocols]
  );

  const activeProtocol = protocols.find((p) => p.id === activeProtocolId);

  function handleCreate() {
    createProtocol({
      name: newName || "Untitled Protocol",
      description: newDescription,
      is_template: newIsTemplate,
    });
    setNewName("");
    setNewDescription("");
    setNewIsTemplate(false);
    setShowNewForm(false);
  }

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="08"
        markerLabel="Protocols · builder"
        title={activeProtocol ? activeProtocol.name : "Protocol Builder"}
        meta={
          activeProtocol ? (
            <>
              v{activeProtocol.version} ·{" "}
              <em
                className="not-italic"
                style={{
                  color:
                    activeProtocol.status === "published"
                      ? "var(--color-brand)"
                      : "var(--color-bf)",
                }}
              >
                {activeProtocol.status}
              </em>{" "}
              · {activeProtocol.steps.length} steps
            </>
          ) : (
            <>
              {protocols.length} protocols · {stats.published} published ·{" "}
              {stats.templates} templates
            </>
          )
        }
      >
        {activeProtocol ? (
          <>
            <button
              onClick={() => setActiveProtocol(null)}
              className="px-3 py-2 text-[13px] font-medium text-ink-muted hover:text-ink transition-colors"
            >
              ← Back
            </button>
            {activeProtocol.status === "draft" && (
              <PageHeaderPrimary onClick={() => publishProtocol(activeProtocol.id)}>
                <Send size={13} />
                Publish
              </PageHeaderPrimary>
            )}
            {activeProtocol.status === "published" && (
              <button
                onClick={() => newVersion(activeProtocol.id)}
                className="inline-flex items-center gap-2 px-3 py-2 text-[13px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors"
              >
                <Copy size={13} />
                New version
              </button>
            )}
          </>
        ) : (
          <PageHeaderPrimary onClick={() => setShowNewForm(true)}>
            <Plus size={14} />
            New protocol
          </PageHeaderPrimary>
        )}
      </PageHeader>

      {!activeProtocol && (
        <KpiStrip columns={4}>
          <Kpi
            label="total"
            value={String(stats.total).padStart(2, "0")}
            delta="all protocols"
          />
          <Kpi
            label="published"
            value={String(stats.published).padStart(2, "0")}
            delta="active versions"
            tone="brand"
          />
          <Kpi
            label="drafts"
            value={String(stats.drafts).padStart(2, "0")}
            delta={stats.drafts > 0 ? "in progress" : "none"}
            tone="bf"
          />
          <Kpi
            label="templates"
            value={String(stats.templates).padStart(2, "0")}
            delta="reusable starting points"
            tone="dapi"
          />
        </KpiStrip>
      )}

      {/* New protocol form */}
      {showNewForm && (
        <div className="mx-6 mt-4 mb-2 bg-surface border border-brand/30 rounded-[5px] overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-bg">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-semibold tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                NEW
              </span>
              <h2 className="text-[14px] font-semibold tracking-[-0.01em] text-ink">
                New protocol
              </h2>
            </div>
            <button
              onClick={() => setShowNewForm(false)}
              className="p-1 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
            >
              <X size={16} />
            </button>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <FieldLabel>name</FieldLabel>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="protocol name…"
                className={inputBase}
              />
            </div>
            <div>
              <FieldLabel>description</FieldLabel>
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="protocol description…"
                rows={2}
                className={cn(inputBase, "resize-none")}
              />
            </div>
            <label className="flex items-center gap-2 font-mono text-[12px] uppercase tracking-[0.04em] text-ink-muted cursor-pointer">
              <input
                type="checkbox"
                checked={newIsTemplate}
                onChange={(e) => setNewIsTemplate(e.target.checked)}
                className="rounded-[2px] border-line-strong text-brand focus:ring-brand/30 accent-brand"
              />
              save as template
            </label>
            <div className="flex items-center gap-2 pt-2 border-t border-line">
              <button
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors"
                style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
              >
                Create protocol
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="px-3 py-2 text-[13px] text-ink-muted hover:text-ink transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Body */}
      <div className="flex-1 mx-6 my-4 bg-surface border border-line rounded-[5px] overflow-hidden flex flex-col min-h-0">
        {activeProtocol ? (
          <>
            <div className="px-4 py-2 border-b border-line flex items-center gap-1">
              {(["steps", "inventory", "dilution"] as const).map((tab) => {
                const isOn = activeTab === tab;
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={cn(
                      "px-3 py-1.5 font-mono text-[11.5px] uppercase tracking-[0.04em] rounded-[3px] transition-colors",
                      isOn
                        ? "bg-brand-soft text-brand"
                        : "text-ink-muted hover:text-ink hover:bg-bg"
                    )}
                  >
                    {tab === "dilution" ? "dilution calc" : tab}
                  </button>
                );
              })}
            </div>

            <div className="flex-1 overflow-auto p-4">
              {activeTab === "steps" && (
                <ProtocolStepBuilder
                  protocolId={activeProtocol.id}
                  steps={activeProtocol.steps}
                />
              )}
              {activeTab === "inventory" && (
                <InventoryChecker protocolId={activeProtocol.id} />
              )}
              {activeTab === "dilution" && <DilutionCalculator />}
            </div>
          </>
        ) : (
          <>
            <div className="px-4 py-2.5 border-b border-line bg-bg flex items-center justify-between">
              <span className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
                <span className="text-brand">›</span> protocols
              </span>
              <span className="font-mono text-[11px] uppercase tracking-[0.02em] text-ink-subtle">
                {protocols.length} total
              </span>
            </div>

            <div className="flex-1 overflow-auto">
              {protocols.map((protocol, idx) => (
                <button
                  key={protocol.id}
                  onClick={() => setActiveProtocol(protocol.id)}
                  className={cn(
                    "w-full flex items-center gap-4 px-4 py-3 hover:bg-bg transition-colors text-left",
                    idx > 0 && "border-t border-line"
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[13.5px] font-medium text-ink truncate">
                        {protocol.name}
                      </span>
                      <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-ink-subtle border border-line rounded-[2px] px-1 py-px">
                        v{protocol.version}
                      </span>
                    </div>
                    <p className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle mt-1 truncate">
                      {protocol.description || "—"}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle">
                      {protocol.steps.length} steps
                    </span>
                    {protocol.is_template && <Chip tone="dapi">template</Chip>}
                    <Chip tone={STATUS_TONE[protocol.status]}>
                      {protocol.status}
                    </Chip>
                  </div>

                  <ChevronRight
                    size={14}
                    className="text-ink-subtle shrink-0"
                  />
                </button>
              ))}

              {protocols.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16">
                  <p className="text-[13px] text-ink-muted">No protocols yet</p>
                  <p className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle mt-1.5 uppercase">
                    create your first protocol to get started
                  </p>
                </div>
              )}
            </div>

            <div className="px-4 py-2.5 border-t border-line bg-bg font-mono text-[11.5px] tracking-[0.02em] text-ink-subtle">
              showing {protocols.length} protocols
            </div>
          </>
        )}
      </div>
    </div>
  );
}

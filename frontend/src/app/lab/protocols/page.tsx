"use client";

import { useMemo, useState } from "react";
import {
  ClipboardList,
  Plus,
  FileText,
  BookTemplate,
  Globe,
  ChevronRight,
  Send,
  Copy,
  X,
} from "lucide-react";
import { useProtocolStore, type Protocol, type ProtocolStatus } from "@/stores/protocol-store";
import ProtocolStepBuilder from "@/components/lab/protocol-step-builder";
import InventoryChecker from "@/components/lab/inventory-checker";
import DilutionCalculator from "@/components/lab/dilution-calculator";

const STATUS_CONFIG: Record<ProtocolStatus, { label: string; color: string; bg: string }> = {
  draft: { label: "Draft", color: "text-amber-700", bg: "bg-amber-50" },
  published: { label: "Published", color: "text-emerald-700", bg: "bg-emerald-50" },
  archived: { label: "Archived", color: "text-gray-600", bg: "bg-gray-100" },
};

export default function ProtocolsPage() {
  const {
    protocols,
    activeProtocolId,
    setActiveProtocol,
    createProtocol,
    publishProtocol,
    newVersion,
    loading,
  } = useProtocolStore();

  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newIsTemplate, setNewIsTemplate] = useState(false);
  const [activeTab, setActiveTab] = useState<"steps" | "inventory" | "dilution">("steps");

  const stats = useMemo(() => ({
    total: protocols.length,
    templates: protocols.filter((p) => p.is_template).length,
    published: protocols.filter((p) => p.status === "published").length,
  }), [protocols]);

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
    <div className="flex flex-col h-full bg-cream">
      {/* Header */}
      <div className="px-6 py-4 bg-surface border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber/15 flex items-center justify-center">
              <ClipboardList size={18} className="text-amber" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-charcoal">Protocol Builder</h1>
              <p className="text-xs text-muted">Create, manage, and version lab protocols</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowNewForm(true)}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
            >
              <Plus size={15} />
              New Protocol
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard cards */}
      <div className="px-6 py-4 grid grid-cols-3 gap-4">
        <DashCard
          icon={<FileText size={18} className="text-amber" />}
          label="Total Protocols"
          value={stats.total}
          bg="bg-amber/10"
        />
        <DashCard
          icon={<BookTemplate size={18} className="text-blue-600" />}
          label="Templates"
          value={stats.templates}
          bg="bg-blue-50"
        />
        <DashCard
          icon={<Globe size={18} className="text-emerald-600" />}
          label="Published"
          value={stats.published}
          bg="bg-emerald-50"
        />
      </div>

      {/* New protocol form below */}

      {/* New protocol form */}
      {showNewForm && (
        <div className="mx-6 mb-4 bg-surface rounded-xl border border-amber/30 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-charcoal">New Protocol</h2>
            <button onClick={() => setShowNewForm(false)} className="p-1 text-muted hover:text-charcoal">
              <X size={16} />
            </button>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <label className="block text-xs font-medium text-charcoal mb-1">Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Protocol name..."
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-charcoal mb-1">Description</label>
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Protocol description..."
                rows={2}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 resize-none"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-charcoal cursor-pointer">
              <input
                type="checkbox"
                checked={newIsTemplate}
                onChange={(e) => setNewIsTemplate(e.target.checked)}
                className="rounded border-border text-amber focus:ring-amber"
              />
              Save as template
            </label>
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleCreate}
                className="px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
              >
                Create Protocol
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="px-4 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Protocol list or step builder */}
      <div className="flex-1 mx-6 mb-6 bg-surface rounded-xl border border-border overflow-hidden flex flex-col">
        {activeProtocol ? (
          <>
            {/* Protocol detail header */}
            <div className="px-4 py-3 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveProtocol(null)}
                  className="text-xs text-muted hover:text-charcoal transition-colors"
                >
                  Protocols
                </button>
                <ChevronRight size={12} className="text-muted" />
                <span className="text-sm font-medium text-charcoal">{activeProtocol.name}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cream text-muted border border-border">
                  v{activeProtocol.version}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CONFIG[activeProtocol.status].bg} ${STATUS_CONFIG[activeProtocol.status].color}`}
                >
                  {STATUS_CONFIG[activeProtocol.status].label}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {activeProtocol.status === "draft" && (
                  <button
                    onClick={() => publishProtocol(activeProtocol.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
                  >
                    <Send size={12} />
                    Publish
                  </button>
                )}
                {activeProtocol.status === "published" && (
                  <button
                    onClick={() => newVersion(activeProtocol.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted hover:text-charcoal rounded-lg border border-border transition-colors"
                  >
                    <Copy size={12} />
                    New Version
                  </button>
                )}
              </div>
            </div>

            {/* Tabs */}
            <div className="px-4 py-2 border-b border-border flex items-center gap-4">
              {(["steps", "inventory", "dilution"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`text-xs font-medium pb-1 border-b-2 transition-colors ${
                    activeTab === tab
                      ? "text-charcoal border-amber"
                      : "text-muted border-transparent hover:text-charcoal"
                  }`}
                >
                  {tab === "steps" ? "Steps" : tab === "inventory" ? "Inventory" : "Dilution Calculator"}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-auto p-4">
              {activeTab === "steps" && (
                <ProtocolStepBuilder protocolId={activeProtocol.id} steps={activeProtocol.steps} />
              )}
              {activeTab === "inventory" && <InventoryChecker protocolId={activeProtocol.id} />}
              {activeTab === "dilution" && <DilutionCalculator />}
            </div>
          </>
        ) : (
          <>
            <div className="px-4 py-3 border-b border-border">
              <h2 className="text-sm font-medium text-charcoal">Protocols</h2>
            </div>

            <div className="flex-1 overflow-auto divide-y divide-border/50">
              {protocols.map((protocol) => {
                const statusCfg = STATUS_CONFIG[protocol.status];
                return (
                  <button
                    key={protocol.id}
                    onClick={() => setActiveProtocol(protocol.id)}
                    className="w-full flex items-center gap-4 px-4 py-3 hover:bg-cream/30 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center shrink-0">
                      <ClipboardList size={14} className="text-amber" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-charcoal truncate">{protocol.name}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-cream text-muted border border-border">
                          v{protocol.version}
                        </span>
                      </div>
                      <p className="text-xs text-muted mt-0.5 truncate">{protocol.description}</p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-muted">{protocol.steps.length} steps</span>
                      {protocol.is_template && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 text-blue-700">
                          Template
                        </span>
                      )}
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.bg} ${statusCfg.color}`}
                      >
                        {statusCfg.label}
                      </span>
                    </div>

                    <ChevronRight size={14} className="text-muted shrink-0" />
                  </button>
                );
              })}

              {protocols.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-muted">
                  <ClipboardList size={32} className="mb-2 opacity-40" />
                  <p className="text-sm">No protocols yet</p>
                  <p className="text-xs mt-1">Create your first protocol to get started</p>
                </div>
              )}
            </div>

            <div className="px-4 py-2.5 border-t border-border text-xs text-muted">
              Showing {protocols.length} protocols
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function DashCard({
  icon,
  label,
  value,
  bg,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  bg: string;
  highlight?: string;
}) {
  return (
    <div className="bg-surface rounded-xl border border-border p-4 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center shrink-0`}>{icon}</div>
      <div>
        <div className={`text-2xl font-semibold ${highlight || "text-charcoal"}`}>{value}</div>
        <div className="text-xs text-muted">{label}</div>
      </div>
    </div>
  );
}

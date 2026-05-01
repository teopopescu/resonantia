"use client";

import { useMemo, useState } from "react";
import {
  Plus,
  Sparkles,
  Send,
  ChevronRight,
  Download,
  FileDown,
  X,
} from "lucide-react";
import { useELNStore, type ELNEntryStatus } from "@/stores/eln-store";
import ELNEditor from "@/components/lab/eln-editor";
import {
  PageHeader,
  PageHeaderPrimary,
  PageHeaderGhost,
} from "@/components/lab/primitives/page-header";
import { KpiStrip, Kpi } from "@/components/lab/primitives/kpi-strip";
import { Chip } from "@/components/lab/primitives/data-table";
import { cn } from "@/lib/utils";

const STATUS_TONE: Record<ELNEntryStatus, "default" | "brand" | "bf"> = {
  draft: "bf",
  submitted: "brand",
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

function CardPanel({
  marker,
  title,
  onClose,
  children,
}: {
  marker: string;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-6 mb-4 bg-surface border border-brand/30 rounded-[5px] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-bg">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] font-semibold tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
            {marker}
          </span>
          <h2 className="text-[14px] font-semibold tracking-[-0.01em] text-ink">
            {title}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
        >
          <X size={16} />
        </button>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

export default function ELNPage() {
  const {
    entries,
    activeEntryId,
    setActiveEntry,
    createEntry,
    autoGenerate,
    submitEntry,
    exportPdf,
    exportMarkdown,
  } = useELNStore();

  const [showNewForm, setShowNewForm] = useState(false);
  const [showAutoGen, setShowAutoGen] = useState(false);
  const [autoGenExpId, setAutoGenExpId] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newTags, setNewTags] = useState("");

  const stats = useMemo(() => {
    const now = Date.now();
    const sevenDays = 7 * 24 * 60 * 60 * 1000;
    return {
      total: entries.length,
      drafts: entries.filter((e) => e.status === "draft").length,
      submittedThisWeek: entries.filter(
        (e) =>
          e.status === "submitted" &&
          e.submitted_at &&
          now - new Date(e.submitted_at).getTime() < sevenDays
      ).length,
      submittedTotal: entries.filter((e) => e.status === "submitted").length,
    };
  }, [entries]);

  function handleCreateEntry() {
    createEntry({
      title: newTitle || "Untitled Entry",
      content: newContent,
      tags: newTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    });
    setNewTitle("");
    setNewContent("");
    setNewTags("");
    setShowNewForm(false);
  }

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="07"
        markerLabel="ELN · electronic lab notebook"
        title="Electronic Lab Notebook"
        meta={
          <>
            {entries.length} entries ·{" "}
            <em
              className="not-italic"
              style={{ color: stats.drafts > 0 ? "var(--color-bf)" : undefined }}
            >
              {stats.drafts} drafts
            </em>{" "}
            · {stats.submittedTotal} submitted
          </>
        }
      >
        <PageHeaderGhost onClick={() => setShowAutoGen(true)}>
          <Sparkles size={14} />
          Auto-generate
        </PageHeaderGhost>
        <PageHeaderPrimary onClick={() => setShowNewForm(true)}>
          <Plus size={14} />
          New entry
        </PageHeaderPrimary>
      </PageHeader>

      <KpiStrip columns={3}>
        <Kpi
          label="total entries"
          value={String(entries.length).padStart(2, "0")}
          delta="all entries"
        />
        <Kpi
          label="drafts"
          value={String(stats.drafts).padStart(2, "0")}
          delta={stats.drafts > 0 ? "awaiting review" : "no drafts"}
          tone="bf"
        />
        <Kpi
          label="submitted · 7d"
          value={String(stats.submittedThisWeek).padStart(2, "0")}
          delta={
            stats.submittedThisWeek > 0
              ? "this week"
              : "no recent submissions"
          }
          tone="brand"
        />
      </KpiStrip>

      {/* Auto-generate */}
      {showAutoGen && (
        <CardPanel
          marker="AGEN"
          title="Auto-generate from experiment"
          onClose={() => setShowAutoGen(false)}
        >
          <p className="font-mono text-[11px] tracking-[0.02em] text-ink-muted mb-3">
            <span className="text-brand">›</span> enter the experiment id to
            generate an entry with objectives, protocol, plate maps, and results
          </p>
          <input
            type="text"
            value={autoGenExpId}
            onChange={(e) => setAutoGenExpId(e.target.value)}
            placeholder="experiment uuid"
            className={cn(inputBase, "font-mono mb-3")}
          />
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (autoGenExpId.trim()) {
                  autoGenerate(autoGenExpId.trim());
                  setAutoGenExpId("");
                  setShowAutoGen(false);
                }
              }}
              disabled={!autoGenExpId.trim()}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-60"
              style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
            >
              <Sparkles size={13} /> Generate
            </button>
            <button
              onClick={() => setShowAutoGen(false)}
              className="px-3 py-2 text-[13px] text-ink-muted hover:text-ink transition-colors"
            >
              Cancel
            </button>
          </div>
          <p className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-3">
            tip · ask the agent to “create an eln entry for [experiment]”
          </p>
        </CardPanel>
      )}

      {/* New entry */}
      {showNewForm && (
        <CardPanel
          marker="NEW"
          title="New notebook entry"
          onClose={() => setShowNewForm(false)}
        >
          <div className="space-y-3">
            <div>
              <FieldLabel>title</FieldLabel>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="entry title…"
                className={inputBase}
              />
            </div>
            <ELNEditor content={newContent} onChange={setNewContent} />
            <div>
              <FieldLabel>tags · comma-separated</FieldLabel>
              <input
                type="text"
                value={newTags}
                onChange={(e) => setNewTags(e.target.value)}
                placeholder="e.g. western-blot, p53, CRISPR"
                className={cn(inputBase, "font-mono")}
              />
            </div>
            <div className="flex items-center gap-2 pt-2 border-t border-line">
              <button
                onClick={handleCreateEntry}
                className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors"
                style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
              >
                Save entry
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="px-3 py-2 text-[13px] text-ink-muted hover:text-ink transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </CardPanel>
      )}

      {/* Entry list */}
      <div className="flex-1 mx-6 mb-6 bg-surface border border-line rounded-[5px] overflow-hidden flex flex-col min-h-0">
        <div className="px-4 py-2.5 border-b border-line bg-bg flex items-center justify-between">
          <span className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
            <span className="text-brand">›</span> entries
          </span>
          <span className="font-mono text-[11px] uppercase tracking-[0.02em] text-ink-subtle">
            {entries.length} total
          </span>
        </div>

        <div className="flex-1 overflow-auto">
          {entries.map((entry, idx) => {
            const isExpanded = activeEntryId === entry.id;
            return (
              <div
                key={entry.id}
                className={cn(idx > 0 && "border-t border-line")}
              >
                <button
                  onClick={() => setActiveEntry(isExpanded ? null : entry.id)}
                  className="w-full flex items-center gap-4 px-4 py-3 hover:bg-bg transition-colors text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] tracking-[0.04em] text-ink-subtle uppercase">
                        {entry.entry_number}
                      </span>
                      <span className="text-[13.5px] font-medium text-ink truncate">
                        {entry.title}
                      </span>
                    </div>
                    <div className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-1">
                      {entry.experiment_title && (
                        <>
                          {entry.experiment_title}
                          <span className="text-line-strong mx-1.5">·</span>
                        </>
                      )}
                      {new Date(entry.updated_at).toLocaleDateString()}
                    </div>
                  </div>

                  {entry.tags.length > 0 && (
                    <div className="flex items-center gap-1 shrink-0">
                      {entry.tags.slice(0, 2).map((tag) => (
                        <Chip key={tag} tone="default">
                          {tag}
                        </Chip>
                      ))}
                      {entry.tags.length > 2 && (
                        <span className="font-mono text-[10.5px] tracking-[0.02em] text-ink-subtle">
                          +{entry.tags.length - 2}
                        </span>
                      )}
                    </div>
                  )}

                  <Chip tone={STATUS_TONE[entry.status]}>{entry.status}</Chip>

                  <ChevronRight
                    size={14}
                    className={cn(
                      "text-ink-subtle transition-transform shrink-0",
                      isExpanded && "rotate-90"
                    )}
                  />
                </button>

                {isExpanded && (
                  <div className="px-4 pb-4 bg-bg">
                    <div className="rounded-[3px] bg-surface border border-line p-3 mb-3">
                      <pre className="text-[12.5px] text-ink whitespace-pre-wrap font-sans leading-relaxed">
                        {entry.content.slice(0, 500)}
                        {entry.content.length > 500 ? "…" : ""}
                      </pre>
                    </div>
                    <div className="flex items-center gap-2">
                      {entry.status === "draft" && (
                        <button
                          onClick={() => submitEntry(entry.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors"
                          style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
                        >
                          <Send size={12} />
                          Submit
                        </button>
                      )}
                      <button
                        onClick={() => exportPdf(entry.id)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors"
                      >
                        <Download size={12} />
                        Export PDF
                      </button>
                      <button
                        onClick={() => exportMarkdown(entry.id)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors"
                      >
                        <FileDown size={12} />
                        Export markdown
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {entries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16">
              <p className="text-[13px] text-ink-muted">No entries yet</p>
              <p className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle mt-1.5 uppercase">
                create your first notebook entry to get started
              </p>
            </div>
          )}
        </div>

        <div className="px-4 py-2.5 border-t border-line bg-bg font-mono text-[11.5px] tracking-[0.02em] text-ink-subtle">
          showing {entries.length} entries
        </div>
      </div>
    </div>
  );
}

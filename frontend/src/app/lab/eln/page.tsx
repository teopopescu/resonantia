"use client";

import { useMemo, useState } from "react";
import {
  BookOpen,
  Plus,
  Sparkles,
  FileText,
  FilePenLine,
  Send,
  Archive,
  ChevronRight,
  Download,
  FileDown,
  X,
  Tag,
  Clock,
} from "lucide-react";
import { useELNStore, type ELNEntry, type ELNEntryStatus } from "@/stores/eln-store";
import ELNEditor from "@/components/lab/eln-editor";

const STATUS_CONFIG: Record<ELNEntryStatus, { label: string; color: string; bg: string }> = {
  draft: { label: "Draft", color: "text-amber-700", bg: "bg-amber-50" },
  submitted: { label: "Submitted", color: "text-emerald-700", bg: "bg-emerald-50" },
  archived: { label: "Archived", color: "text-gray-600", bg: "bg-gray-100" },
};

export default function ELNPage() {
  const {
    entries,
    activeEntryId,
    setActiveEntry,
    createEntry,
    autoGenerate,
    updateEntry,
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
        (e) => e.status === "submitted" && e.submitted_at && now - new Date(e.submitted_at).getTime() < sevenDays
      ).length,
    };
  }, [entries]);

  const activeEntry = entries.find((e) => e.id === activeEntryId);

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
    <div className="flex flex-col h-full bg-cream">
      {/* Header */}
      <div className="px-6 py-4 bg-surface border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber/15 flex items-center justify-center">
              <BookOpen size={18} className="text-amber" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-charcoal">Electronic Lab Notebook</h1>
              <p className="text-xs text-muted">Document experiments, track results, and export entries</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAutoGen(true)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted bg-cream hover:bg-cream-dark transition-colors"
            >
              <Sparkles size={15} />
              Auto-generate
            </button>
            <button
              onClick={() => setShowNewForm(true)}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
            >
              <Plus size={15} />
              New Entry
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard cards */}
      <div className="px-6 py-4 grid grid-cols-3 gap-4">
        <DashCard
          icon={<FileText size={18} className="text-amber" />}
          label="Total Entries"
          value={stats.total}
          bg="bg-amber/10"
        />
        <DashCard
          icon={<FilePenLine size={18} className="text-amber-600" />}
          label="Drafts"
          value={stats.drafts}
          bg="bg-amber-50"
          highlight={stats.drafts > 0 ? "text-amber-700" : undefined}
        />
        <DashCard
          icon={<Send size={18} className="text-emerald-600" />}
          label="Submitted This Week"
          value={stats.submittedThisWeek}
          bg="bg-emerald-50"
        />
      </div>

      {/* Auto-generate from experiment */}
      {showAutoGen && (
        <div className="mx-6 mb-4 bg-surface rounded-xl border border-amber/30 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-charcoal">Auto-generate from Experiment</h2>
            <button onClick={() => setShowAutoGen(false)} className="p-1 text-muted hover:text-charcoal"><X size={16} /></button>
          </div>
          <div className="p-4 space-y-3">
            <p className="text-xs text-muted">Enter the experiment ID to auto-generate an ELN entry with objectives, protocol, plate maps, and results.</p>
            <input
              type="text"
              value={autoGenExpId}
              onChange={(e) => setAutoGenExpId(e.target.value)}
              placeholder="Experiment UUID"
              className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={() => { if (autoGenExpId.trim()) { autoGenerate(autoGenExpId.trim()); setAutoGenExpId(""); setShowAutoGen(false); } }}
                disabled={!autoGenExpId.trim()}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors disabled:opacity-60"
              >
                <Sparkles size={14} /> Generate
              </button>
              <button onClick={() => setShowAutoGen(false)} className="px-4 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border transition-colors">Cancel</button>
            </div>
            <p className="text-[11px] text-muted">Tip: ask the chat assistant &quot;Create an ELN entry for [experiment name]&quot; — it will find the experiment automatically.</p>
          </div>
        </div>
      )}

      {/* New entry form (slide-over) */}
      {showNewForm && (
        <div className="mx-6 mb-4 bg-surface rounded-xl border border-amber/30 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-charcoal">New Notebook Entry</h2>
            <button onClick={() => setShowNewForm(false)} className="p-1 text-muted hover:text-charcoal">
              <X size={16} />
            </button>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <label className="block text-xs font-medium text-charcoal mb-1">Title</label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Entry title..."
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              />
            </div>
            <ELNEditor content={newContent} onChange={setNewContent} />
            <div>
              <label className="block text-xs font-medium text-charcoal mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={newTags}
                onChange={(e) => setNewTags(e.target.value)}
                placeholder="e.g. western-blot, p53, CRISPR"
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              />
            </div>
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleCreateEntry}
                className="px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
              >
                Save Entry
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="px-4 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Entry list */}
      <div className="flex-1 mx-6 mb-6 bg-surface rounded-xl border border-border overflow-hidden flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-medium text-charcoal">Entries</h2>
        </div>

        <div className="flex-1 overflow-auto divide-y divide-border/50">
          {entries.map((entry) => {
            const statusCfg = STATUS_CONFIG[entry.status];
            const isExpanded = activeEntryId === entry.id;
            return (
              <div key={entry.id}>
                <button
                  onClick={() => setActiveEntry(isExpanded ? null : entry.id)}
                  className="w-full flex items-center gap-4 px-4 py-3 hover:bg-cream/30 transition-colors text-left"
                >
                  <div className="w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center shrink-0">
                    <BookOpen size={14} className="text-amber" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted">{entry.entry_number}</span>
                      <span className="text-sm font-medium text-charcoal truncate">{entry.title}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      {entry.experiment_title && (
                        <span className="text-xs text-muted truncate">{entry.experiment_title}</span>
                      )}
                      <span className="flex items-center gap-1 text-xs text-muted">
                        <Clock size={10} />
                        {new Date(entry.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {entry.tags.length > 0 && (
                    <div className="flex items-center gap-1 shrink-0">
                      {entry.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-cream text-muted border border-border"
                        >
                          <Tag size={8} />
                          {tag}
                        </span>
                      ))}
                      {entry.tags.length > 2 && (
                        <span className="text-[10px] text-muted">+{entry.tags.length - 2}</span>
                      )}
                    </div>
                  )}

                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.bg} ${statusCfg.color} shrink-0`}
                  >
                    {statusCfg.label}
                  </span>

                  <ChevronRight
                    size={14}
                    className={`text-muted transition-transform shrink-0 ${isExpanded ? "rotate-90" : ""}`}
                  />
                </button>

                {/* Expanded view */}
                {isExpanded && (
                  <div className="px-4 pb-4 pl-16">
                    <div className="rounded-lg bg-cream/50 p-3 mb-3">
                      <pre className="text-xs text-charcoal/80 whitespace-pre-wrap font-sans leading-relaxed">
                        {entry.content.slice(0, 500)}
                        {entry.content.length > 500 ? "..." : ""}
                      </pre>
                    </div>
                    <div className="flex items-center gap-2">
                      {entry.status === "draft" && (
                        <button
                          onClick={() => submitEntry(entry.id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
                        >
                          <Send size={12} />
                          Submit
                        </button>
                      )}
                      <button
                        onClick={() => exportPdf(entry.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted transition-colors"
                      >
                        <Download size={12} />
                        Export PDF
                      </button>
                      <button
                        onClick={() => exportMarkdown(entry.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted transition-colors"
                      >
                        <FileDown size={12} />
                        Export Markdown
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {entries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-muted">
              <BookOpen size={32} className="mb-2 opacity-40" />
              <p className="text-sm">No entries yet</p>
              <p className="text-xs mt-1">Create your first notebook entry to get started</p>
            </div>
          )}
        </div>

        <div className="px-4 py-2.5 border-t border-border text-xs text-muted">
          Showing {entries.length} entries
        </div>
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

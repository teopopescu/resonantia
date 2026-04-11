import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, apiRaw } from "@/lib/api";

export type ELNEntryStatus = "draft" | "submitted" | "archived";

export interface ELNEntry {
  id: string;
  entry_number: string;
  title: string;
  content: string;
  experiment_id?: string;
  experiment_title?: string;
  tags: string[];
  status: ELNEntryStatus;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  appendices: string[];
}

const DEMO_ENTRIES: ELNEntry[] = [
  {
    id: "eln-1",
    entry_number: "ELN-2026-001",
    title: "HEK293T Transfection Optimization",
    content:
      "## Objective\nOptimize lipofectamine ratios for HEK293T cells.\n\n## Methods\nUsed 6-well plates with varying DNA:lipofectamine ratios (1:2, 1:3, 1:4).\n\n## Results\n1:3 ratio yielded highest GFP expression (~72% positive cells).\n\n## Conclusions\nProceed with 1:3 ratio for future experiments.",
    experiment_id: "exp-1",
    experiment_title: "Transfection Optimization Study",
    tags: ["transfection", "HEK293T", "optimization"],
    status: "submitted",
    created_at: "2026-04-08T10:00:00Z",
    updated_at: "2026-04-09T14:30:00Z",
    submitted_at: "2026-04-09T14:30:00Z",
    appendices: [],
  },
  {
    id: "eln-2",
    entry_number: "ELN-2026-002",
    title: "Staurosporine IC50 Determination",
    content:
      "## Objective\nDetermine IC50 of staurosporine in HeLa cells.\n\n## Methods\nSerial dilution from 10 uM to 0.01 uM. 72h incubation. CellTiter-Glo readout.\n\n## Results\nPending analysis...",
    experiment_id: "exp-2",
    experiment_title: "Drug Sensitivity Screen",
    tags: ["IC50", "staurosporine", "HeLa"],
    status: "draft",
    created_at: "2026-04-10T09:15:00Z",
    updated_at: "2026-04-10T16:00:00Z",
    appendices: [],
  },
  {
    id: "eln-3",
    entry_number: "ELN-2026-003",
    title: "Western Blot - p53 Expression",
    content:
      "## Objective\nConfirm p53 knockout in CRISPR-edited clones.\n\n## Methods\nStandard western blot protocol. Anti-p53 (DO-1) primary antibody at 1:1000.\n\n## Results\nClones 2, 5, and 7 show complete loss of p53 band at 53 kDa.\n\n## Conclusions\nThree validated p53 KO clones available for downstream experiments.",
    tags: ["western-blot", "p53", "CRISPR"],
    status: "submitted",
    created_at: "2026-04-07T08:00:00Z",
    updated_at: "2026-04-07T17:45:00Z",
    submitted_at: "2026-04-07T17:45:00Z",
    appendices: ["gel_image_001.tiff"],
  },
];

function generateId() {
  return "eln-" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

interface ELNState {
  entries: ELNEntry[];
  activeEntryId: string | null;
  loading: boolean;
  synced: boolean;

  fetchEntries: () => Promise<void>;
  createEntry: (entry: Partial<ELNEntry>) => Promise<void>;
  autoGenerate: (experimentId: string) => Promise<void>;
  updateEntry: (id: string, updates: Partial<ELNEntry>) => void;
  submitEntry: (id: string) => Promise<void>;
  addAppendix: (id: string, filename: string) => void;
  exportPdf: (id: string) => Promise<void>;
  exportMarkdown: (id: string) => void;
  setActiveEntry: (id: string | null) => void;
  deleteEntry: (id: string) => void;
}

export const useELNStore = create<ELNState>()(
  persist(
    (set, get) => ({
      entries: DEMO_ENTRIES,
      activeEntryId: null,
      loading: false,
      synced: false,

      fetchEntries: async () => {
        set({ loading: true });
        try {
          const data = await api<ELNEntry[]>("/api/v1/eln/entries");
          set({ entries: data.length > 0 ? data : DEMO_ENTRIES, synced: data.length > 0, loading: false });
        } catch {
          set({ synced: false, loading: false });
        }
      },

      createEntry: async (partial) => {
        const counter = get().entries.length + 1;
        const entry: ELNEntry = {
          id: generateId(),
          entry_number: `ELN-2026-${String(counter).padStart(3, "0")}`,
          title: partial.title || "Untitled Entry",
          content: partial.content || "",
          experiment_id: partial.experiment_id,
          experiment_title: partial.experiment_title,
          tags: partial.tags || [],
          status: "draft",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          appendices: [],
        };
        set({ loading: true });
        try {
          const created = await api<ELNEntry>("/api/v1/eln/entries", {
            method: "POST",
            body: JSON.stringify(entry),
          });
          set((s) => ({ entries: [created, ...s.entries], synced: true, loading: false }));
        } catch {
          set((s) => ({ entries: [entry, ...s.entries], synced: false, loading: false }));
        }
      },

      autoGenerate: async (experimentId) => {
        set({ loading: true });
        try {
          const generated = await api<ELNEntry>(`/api/v1/eln/auto-generate`, {
            method: "POST",
            body: JSON.stringify({ experiment_id: experimentId }),
          });
          set((s) => ({ entries: [generated, ...s.entries], synced: true, loading: false }));
        } catch {
          set({ loading: false });
        }
      },

      updateEntry: (id, updates) =>
        set((s) => ({
          entries: s.entries.map((e) =>
            e.id === id ? { ...e, ...updates, updated_at: new Date().toISOString() } : e
          ),
        })),

      submitEntry: async (id) => {
        const entry = get().entries.find((e) => e.id === id);
        if (!entry) return;
        set({ loading: true });
        try {
          await api<ELNEntry>(`/api/v1/eln/entries/${id}/submit`, { method: "POST" });
          set((s) => ({
            entries: s.entries.map((e) =>
              e.id === id ? { ...e, status: "submitted", submitted_at: new Date().toISOString() } : e
            ),
            synced: true,
            loading: false,
          }));
        } catch {
          set((s) => ({
            entries: s.entries.map((e) =>
              e.id === id ? { ...e, status: "submitted", submitted_at: new Date().toISOString() } : e
            ),
            synced: false,
            loading: false,
          }));
        }
      },

      addAppendix: (id, filename) =>
        set((s) => ({
          entries: s.entries.map((e) =>
            e.id === id ? { ...e, appendices: [...e.appendices, filename] } : e
          ),
        })),

      exportPdf: async (id) => {
        try {
          const res = await apiRaw(`/api/v1/eln/entries/${id}/export/pdf`);
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${id}.pdf`;
          a.click();
          URL.revokeObjectURL(url);
        } catch {
          // Fallback: download as text
          const entry = get().entries.find((e) => e.id === id);
          if (entry) {
            const blob = new Blob([`# ${entry.title}\n\n${entry.content}`], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${entry.entry_number}.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }
        }
      },

      exportMarkdown: (id) => {
        const entry = get().entries.find((e) => e.id === id);
        if (!entry) return;
        const md = `# ${entry.title}\n\n**Entry:** ${entry.entry_number}  \n**Date:** ${new Date(entry.created_at).toLocaleDateString()}  \n**Status:** ${entry.status}  \n**Tags:** ${entry.tags.join(", ")}\n\n---\n\n${entry.content}`;
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${entry.entry_number}.md`;
        a.click();
        URL.revokeObjectURL(url);
      },

      setActiveEntry: (id) => set({ activeEntryId: id }),

      deleteEntry: (id) =>
        set((s) => ({
          entries: s.entries.filter((e) => e.id !== id),
          activeEntryId: s.activeEntryId === id ? null : s.activeEntryId,
        })),
    }),
    {
      name: "resonantia-eln",
      partialize: (state) => ({ entries: state.entries }),
    }
  )
);

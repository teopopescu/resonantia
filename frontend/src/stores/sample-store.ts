import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEMO_SAMPLES, type Sample, type SampleStatus, type SampleType } from "@/lib/demo-data";
import { api } from "@/lib/api";

export interface SampleFilters {
  type: SampleType | "all";
  status: SampleStatus | "all";
  location: string;
  search: string;
}

interface SampleState {
  samples: Sample[];
  filters: SampleFilters;
  selectedSamples: string[];
  modalOpen: boolean;
  editingSample: Sample | null;
  scannerMode: "find" | "add" | null;
  loading: boolean;
  synced: boolean;

  // Sync actions
  fetchSamples: () => Promise<void>;
  createSample: (sample: Sample) => Promise<void>;
  removeSample: (id: string) => Promise<void>;

  // Local actions (kept for backwards compatibility)
  addSample: (sample: Sample) => void;
  updateSample: (id: string, updates: Partial<Sample>) => void;
  deleteSample: (id: string) => void;
  setFilters: (filters: Partial<SampleFilters>) => void;
  toggleSelected: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;
  openModal: (sample?: Sample) => void;
  closeModal: () => void;
  setScannerMode: (mode: "find" | "add" | null) => void;
}

export const useSampleStore = create<SampleState>()(
  persist(
    (set, get) => ({
      samples: DEMO_SAMPLES,
      filters: { type: "all", status: "all", location: "", search: "" },
      selectedSamples: [],
      modalOpen: false,
      editingSample: null,
      scannerMode: null,
      loading: false,
      synced: false,

      // ── API-backed actions ──

      fetchSamples: async () => {
        set({ loading: true });
        try {
          const data = await api<Sample[]>("/api/v1/samples");
          set({ samples: data.length > 0 ? data : DEMO_SAMPLES, synced: data.length > 0, loading: false });
        } catch {
          // Backend unavailable — keep demo data
          set({ synced: false, loading: false });
        }
      },

      createSample: async (sample) => {
        set({ loading: true });
        try {
          const created = await api<Sample>("/api/v1/samples", {
            method: "POST",
            body: JSON.stringify(sample),
          });
          set((state) => ({ samples: [created, ...state.samples], synced: true, loading: false }));
        } catch {
          // Fallback: add locally
          set((state) => ({ samples: [sample, ...state.samples], synced: false, loading: false }));
        }
      },

      removeSample: async (id) => {
        set({ loading: true });
        try {
          await api<void>(`/api/v1/samples/${id}`, { method: "DELETE" });
          set((state) => ({
            samples: state.samples.filter((s) => s.id !== id),
            selectedSamples: state.selectedSamples.filter((sid) => sid !== id),
            synced: true,
            loading: false,
          }));
        } catch {
          // Fallback: remove locally
          set((state) => ({
            samples: state.samples.filter((s) => s.id !== id),
            selectedSamples: state.selectedSamples.filter((sid) => sid !== id),
            synced: false,
            loading: false,
          }));
        }
      },

      // ── Local-only actions ──

      addSample: (sample) =>
        set((state) => ({ samples: [sample, ...state.samples] })),

      updateSample: (id, updates) =>
        set((state) => ({
          samples: state.samples.map((s) =>
            s.id === id ? { ...s, ...updates } : s
          ),
        })),

      deleteSample: (id) =>
        set((state) => ({
          samples: state.samples.filter((s) => s.id !== id),
          selectedSamples: state.selectedSamples.filter((sid) => sid !== id),
        })),

      setFilters: (filters) =>
        set((state) => ({ filters: { ...state.filters, ...filters } })),

      toggleSelected: (id) =>
        set((state) => ({
          selectedSamples: state.selectedSamples.includes(id)
            ? state.selectedSamples.filter((sid) => sid !== id)
            : [...state.selectedSamples, id],
        })),

      selectAll: (ids) => set({ selectedSamples: ids }),

      clearSelection: () => set({ selectedSamples: [] }),

      openModal: (sample) =>
        set({ modalOpen: true, editingSample: sample ?? null }),

      closeModal: () => set({ modalOpen: false, editingSample: null }),

      setScannerMode: (mode) => set({ scannerMode: mode }),
    }),
    {
      name: "resonantia-samples",
      partialize: (state) => ({ samples: state.samples }),
    }
  )
);

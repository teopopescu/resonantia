import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { WellData, WellType } from "@/lib/plate-utils";
import { api, apiRaw } from "@/lib/api";
import { showErrorToast } from "@/lib/demo-mode";

export type MappingMode =
  | "cherry-pick"
  | "serial-dilution"
  | "replicate"
  | "randomize";

export interface WellMapping {
  sourceWell: string;
  destWell: string;
  compound: string;
  concentration: number;
  volume: number;
  sourcePlateId: string;
}

export interface Plate {
  id: string;
  name: string;
  type: 96 | 384;
  wells: Record<string, WellData>;
  createdAt: string;
}

export interface PlateMap {
  id: string;
  name: string;
  sourcePlateIds: string[];
  destinationPlateId: string;
  mappings: WellMapping[];
  status: "draft" | "complete" | "exported";
  createdAt: string;
  updatedAt: string;
}

interface PlateState {
  // Data
  plates: Plate[];
  plateMaps: PlateMap[];
  loading: boolean;
  synced: boolean;

  // Current editor state
  activePlateMapId: string | null;
  activeSourcePlateId: string | null;
  selectedSourceWells: string[];
  selectedDestWells: string[];
  mappingMode: MappingMode;
  plateType: 96 | 384;
  transferVolume: number;
  dilutionFactor: number;
  dilutionSteps: number;
  dilutionDirection: "horizontal" | "vertical";

  // Async API actions
  fetchPlateMaps: () => Promise<void>;
  createPlateMap: (data: Partial<PlateMap>) => Promise<void>;
  generateWorklist: (plateMapId: string, format: string, volume: number) => Promise<string | null>;

  // Actions — plates
  addPlate: (plate: Plate) => void;
  removePlate: (id: string) => void;
  updateWell: (plateId: string, wellLabel: string, data: Partial<WellData>) => void;
  setWellType: (plateId: string, wells: string[], type: WellType) => void;

  // Actions — plate maps
  addPlateMap: (pm: PlateMap) => void;
  removePlateMap: (id: string) => void;
  updatePlateMap: (id: string, data: Partial<PlateMap>) => void;
  setActivePlateMap: (id: string | null) => void;

  // Actions — editor
  setActiveSourcePlate: (id: string | null) => void;
  selectSourceWells: (wells: string[]) => void;
  selectDestWells: (wells: string[]) => void;
  toggleSourceWell: (well: string) => void;
  toggleDestWell: (well: string) => void;
  clearSourceSelection: () => void;
  clearDestSelection: () => void;
  setMappingMode: (mode: MappingMode) => void;
  setPlateType: (type: 96 | 384) => void;
  setTransferVolume: (v: number) => void;
  setDilutionFactor: (f: number) => void;
  setDilutionSteps: (s: number) => void;
  setDilutionDirection: (d: "horizontal" | "vertical") => void;

  // Actions — mappings
  addMappings: (mappings: WellMapping[]) => void;
  clearMappings: (plateMapId: string) => void;
}

function makeEmptyWells(type: 96 | 384): Record<string, WellData> {
  const rows = type === 96 ? 8 : 16;
  const cols = type === 96 ? 12 : 24;
  const rowLetters = "ABCDEFGHIJKLMNOP";
  const wells: Record<string, WellData> = {};
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const label = `${rowLetters[r]}${c + 1}`;
      wells[label] = { label, type: "empty" };
    }
  }
  return wells;
}

function createDemoSourcePlate1(): Plate {
  const wells = makeEmptyWells(96);

  // Controls in column 1
  wells["A1"] = { label: "A1", type: "control-positive", compound: "DMSO", concentration: 100 };
  wells["B1"] = { label: "B1", type: "control-positive", compound: "DMSO", concentration: 100 };
  wells["G1"] = { label: "G1", type: "control-negative" };
  wells["H1"] = { label: "H1", type: "control-negative" };

  // Staurosporine dose-response (row A, cols 2-9)
  const staurConcs = [50, 25, 12.5, 6.25, 3.125, 1.56, 0.78, 0.39];
  for (let i = 0; i < staurConcs.length; i++) {
    const label = `A${i + 2}`;
    wells[label] = { label, type: "compound", compound: "Staurosporine", concentration: staurConcs[i] };
  }

  // Rapamycin dose-response (row B, cols 2-9)
  const rapaConcs = [100, 50, 25, 12.5, 6.25, 3.125, 1.56, 0.78];
  for (let i = 0; i < rapaConcs.length; i++) {
    const label = `B${i + 2}`;
    wells[label] = { label, type: "compound", compound: "Rapamycin", concentration: rapaConcs[i] };
  }

  // Samples in rows C-F
  const sampleNames = ["HEK293T lysate", "HeLa lysate", "CHO-K1 lysate", "Jurkat lysate"];
  for (let r = 0; r < 4; r++) {
    for (let c = 1; c <= 6; c++) {
      const label = `${String.fromCharCode(67 + r)}${c + 1}`;
      wells[label] = { label, type: "sample", compound: sampleNames[r], concentration: 10 * (7 - c) };
    }
  }

  return { id: "src-1", name: "Compound Library Plate A", type: 96, wells, createdAt: "2026-04-08T09:00:00Z" };
}

function createDemoSourcePlate2(): Plate {
  const wells = makeEmptyWells(96);

  // Controls
  wells["A1"] = { label: "A1", type: "control-positive", compound: "DMSO", concentration: 100 };
  wells["H12"] = { label: "H12", type: "control-negative" };

  // Kinase inhibitor panel (rows A-D, cols 2-11)
  const inhibitors = ["Imatinib", "Dasatinib", "Sorafenib", "Erlotinib"];
  const concSeries = [100, 50, 25, 12.5, 6.25, 3.125, 1.56, 0.78, 0.39, 0.195];
  for (let r = 0; r < inhibitors.length; r++) {
    for (let c = 0; c < concSeries.length; c++) {
      const label = `${String.fromCharCode(65 + r)}${c + 2}`;
      wells[label] = { label, type: "compound", compound: inhibitors[r], concentration: concSeries[c] };
    }
  }

  // Samples in rows E-G
  const samples = ["MCF7 extract", "A549 extract", "U2OS extract"];
  for (let r = 0; r < samples.length; r++) {
    for (let c = 0; c < 8; c++) {
      const label = `${String.fromCharCode(69 + r)}${c + 1}`;
      wells[label] = { label, type: "sample", compound: samples[r], concentration: 5 * (8 - c) };
    }
  }

  return { id: "src-2", name: "Kinase Inhibitor Panel", type: 96, wells, createdAt: "2026-04-09T14:30:00Z" };
}

const DEMO_PLATES = [createDemoSourcePlate1(), createDemoSourcePlate2()];

const DEMO_PLATE_MAPS: PlateMap[] = [
  {
    id: "pm-demo-1",
    name: "HTS Screen -- Round 1",
    sourcePlateIds: ["src-1"],
    destinationPlateId: "dest-demo-1",
    mappings: [
      { sourceWell: "A2", destWell: "A1", compound: "Staurosporine", concentration: 50, volume: 100, sourcePlateId: "src-1" },
      { sourceWell: "A3", destWell: "A2", compound: "Staurosporine", concentration: 25, volume: 100, sourcePlateId: "src-1" },
      { sourceWell: "A4", destWell: "A3", compound: "Staurosporine", concentration: 12.5, volume: 100, sourcePlateId: "src-1" },
      { sourceWell: "B2", destWell: "B1", compound: "Rapamycin", concentration: 100, volume: 100, sourcePlateId: "src-1" },
      { sourceWell: "B3", destWell: "B2", compound: "Rapamycin", concentration: 50, volume: 100, sourcePlateId: "src-1" },
    ],
    status: "draft",
    createdAt: "2026-04-10T10:00:00Z",
    updatedAt: "2026-04-10T14:30:00Z",
  },
  {
    id: "pm-demo-2",
    name: "Kinase Inhibitor Dose-Response",
    sourcePlateIds: ["src-2"],
    destinationPlateId: "dest-demo-2",
    mappings: [],
    status: "draft",
    createdAt: "2026-04-09T16:00:00Z",
    updatedAt: "2026-04-09T16:00:00Z",
  },
  {
    id: "pm-demo-3",
    name: "Replicate QC Plate",
    sourcePlateIds: ["src-1"],
    destinationPlateId: "dest-demo-3",
    mappings: [],
    status: "complete",
    createdAt: "2026-04-07T11:00:00Z",
    updatedAt: "2026-04-08T09:15:00Z",
  },
];

export const usePlateStore = create<PlateState>()(
  persist(
    (set, get) => ({
      // Initial data
      plates: DEMO_PLATES,
      plateMaps: DEMO_PLATE_MAPS,
      loading: false,
      synced: false,

      // Editor state
      activePlateMapId: null,
      activeSourcePlateId: "src-1",
      selectedSourceWells: [],
      selectedDestWells: [],
      mappingMode: "cherry-pick",
      plateType: 96,
      transferVolume: 100,
      dilutionFactor: 2,
      dilutionSteps: 8,
      dilutionDirection: "horizontal",

      // ── Async API actions ──

      fetchPlateMaps: async () => {
        set({ loading: true });
        try {
          const data = await api<PlateMap[]>("/api/v1/plates");
          if (data.length > 0) {
            set({ plateMaps: data, synced: true, loading: false });
          } else {
            set({ synced: false, loading: false });
          }
        } catch {
          showErrorToast("backend unavailable — keep demo data");
          // Backend unavailable — keep demo data
          set({ synced: false, loading: false });
        }
      },

      createPlateMap: async (data) => {
        set({ loading: true });
        try {
          const created = await api<PlateMap>("/api/v1/plates", {
            method: "POST",
            body: JSON.stringify(data),
          });
          set((s) => ({ plateMaps: [...s.plateMaps, created], synced: true, loading: false }));
        } catch {
          showErrorToast("save changes");
          // Fallback: add locally with generated id
          const local: PlateMap = {
            id: `pm-local-${Date.now()}`,
            name: data.name || "Untitled Plate Map",
            sourcePlateIds: data.sourcePlateIds || [],
            destinationPlateId: data.destinationPlateId || "",
            mappings: data.mappings || [],
            status: data.status || "draft",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
          set((s) => ({ plateMaps: [...s.plateMaps, local], synced: false, loading: false }));
        }
      },

      generateWorklist: async (plateMapId, format, volume) => {
        try {
          const res = await apiRaw(`/api/v1/plates/${plateMapId}/worklist`, {
            method: "POST",
            body: JSON.stringify({ format, volume }),
          });
          const content = await res.text();
          return content;
        } catch {
          showErrorToast("return null so caller can fall back to client-side generation");
          // Return null so caller can fall back to client-side generation
          return null;
        }
      },

      // Plate actions
      addPlate: (plate) =>
        set((s) => ({ plates: [...s.plates, plate] })),
      removePlate: (id) =>
        set((s) => ({ plates: s.plates.filter((p) => p.id !== id) })),
      updateWell: (plateId, wellLabel, data) =>
        set((s) => ({
          plates: s.plates.map((p) =>
            p.id === plateId
              ? { ...p, wells: { ...p.wells, [wellLabel]: { ...p.wells[wellLabel], ...data } } }
              : p
          ),
        })),
      setWellType: (plateId, wells, type) =>
        set((s) => ({
          plates: s.plates.map((p) => {
            if (p.id !== plateId) return p;
            const updated = { ...p.wells };
            for (const w of wells) {
              updated[w] = { ...updated[w], type };
            }
            return { ...p, wells: updated };
          }),
        })),

      // Plate map actions
      addPlateMap: (pm) =>
        set((s) => ({ plateMaps: [...s.plateMaps, pm] })),
      removePlateMap: (id) =>
        set((s) => ({ plateMaps: s.plateMaps.filter((pm) => pm.id !== id) })),
      updatePlateMap: (id, data) =>
        set((s) => ({
          plateMaps: s.plateMaps.map((pm) =>
            pm.id === id ? { ...pm, ...data, updatedAt: new Date().toISOString() } : pm
          ),
        })),
      setActivePlateMap: (id) => set({ activePlateMapId: id }),

      // Editor actions
      setActiveSourcePlate: (id) => set({ activeSourcePlateId: id }),
      selectSourceWells: (wells) => set({ selectedSourceWells: wells }),
      selectDestWells: (wells) => set({ selectedDestWells: wells }),
      toggleSourceWell: (well) =>
        set((s) => ({
          selectedSourceWells: s.selectedSourceWells.includes(well)
            ? s.selectedSourceWells.filter((w) => w !== well)
            : [...s.selectedSourceWells, well],
        })),
      toggleDestWell: (well) =>
        set((s) => ({
          selectedDestWells: s.selectedDestWells.includes(well)
            ? s.selectedDestWells.filter((w) => w !== well)
            : [...s.selectedDestWells, well],
        })),
      clearSourceSelection: () => set({ selectedSourceWells: [] }),
      clearDestSelection: () => set({ selectedDestWells: [] }),
      setMappingMode: (mode) => set({ mappingMode: mode }),
      setPlateType: (type) => set({ plateType: type }),
      setTransferVolume: (v) => set({ transferVolume: v }),
      setDilutionFactor: (f) => set({ dilutionFactor: f }),
      setDilutionSteps: (s) => set({ dilutionSteps: s }),
      setDilutionDirection: (d) => set({ dilutionDirection: d }),

      // Mapping actions
      addMappings: (mappings) =>
        set((s) => {
          const id = s.activePlateMapId;
          if (!id) return s;
          return {
            plateMaps: s.plateMaps.map((pm) =>
              pm.id === id
                ? { ...pm, mappings: [...pm.mappings, ...mappings], updatedAt: new Date().toISOString() }
                : pm
            ),
          };
        }),
      clearMappings: (plateMapId) =>
        set((s) => ({
          plateMaps: s.plateMaps.map((pm) =>
            pm.id === plateMapId
              ? { ...pm, mappings: [], updatedAt: new Date().toISOString() }
              : pm
          ),
        })),
    }),
    {
      name: "resonantia-plate-store",
    }
  )
);

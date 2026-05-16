import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";
import { isDemoMode, shouldUseDemoData, showErrorToast } from "@/lib/demo-mode";

export interface Reagent {
  name: string;
  volume: number;
  unit: string;
}

export interface ProtocolStep {
  id: string;
  step_number: number;
  title: string;
  description: string;
  duration_minutes?: number;
  temperature_celsius?: number;
  equipment?: string;
  reagents: Reagent[];
  notes?: string;
}

export type ProtocolStatus = "draft" | "published" | "archived";

export interface Protocol {
  id: string;
  name: string;
  description: string;
  version: number;
  status: ProtocolStatus;
  is_template: boolean;
  steps: ProtocolStep[];
  created_at: string;
  updated_at: string;
}

export interface InventoryCheckResult {
  reagent_name: string;
  required_volume: number;
  required_unit: string;
  available_volume: number;
  available: boolean;
}

export interface DilutionResult {
  stock_volume: number;
  diluent_volume: number;
  unit: string;
}

function generateId() {
  return "proto-" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

function generateStepId() {
  return "step-" + Math.random().toString(36).substring(2, 10);
}

const DEMO_PROTOCOLS: Protocol[] = [
  {
    id: "proto-1",
    name: "Standard Western Blot",
    description: "Standard protocol for SDS-PAGE and western blotting",
    version: 2,
    status: "published",
    is_template: true,
    steps: [
      {
        id: "step-1a",
        step_number: 1,
        title: "Sample Preparation",
        description: "Lyse cells in RIPA buffer with protease inhibitors. Incubate on ice for 30 min.",
        duration_minutes: 30,
        temperature_celsius: 4,
        equipment: "Sonicator",
        reagents: [
          { name: "RIPA Buffer", volume: 200, unit: "uL" },
          { name: "Protease Inhibitor Cocktail", volume: 2, unit: "uL" },
        ],
        notes: "Keep samples on ice at all times",
      },
      {
        id: "step-1b",
        step_number: 2,
        title: "Gel Electrophoresis",
        description: "Load 20 ug protein per lane on 10% SDS-PAGE gel. Run at 120V for 90 min.",
        duration_minutes: 90,
        temperature_celsius: 25,
        equipment: "Mini-PROTEAN system",
        reagents: [
          { name: "Loading Buffer (4x)", volume: 5, unit: "uL" },
          { name: "Running Buffer", volume: 500, unit: "mL" },
        ],
      },
      {
        id: "step-1c",
        step_number: 3,
        title: "Transfer",
        description: "Transfer to PVDF membrane at 100V for 60 min in cold transfer buffer.",
        duration_minutes: 60,
        temperature_celsius: 4,
        equipment: "Transfer apparatus",
        reagents: [
          { name: "Transfer Buffer", volume: 1000, unit: "mL" },
          { name: "Methanol", volume: 200, unit: "mL" },
        ],
      },
    ],
    created_at: "2026-03-15T10:00:00Z",
    updated_at: "2026-04-05T14:00:00Z",
  },
  {
    id: "proto-2",
    name: "Cell Viability Assay (CellTiter-Glo)",
    description: "Luminescence-based cell viability measurement",
    version: 1,
    status: "published",
    is_template: false,
    steps: [
      {
        id: "step-2a",
        step_number: 1,
        title: "Plate Cells",
        description: "Seed 5000 cells/well in 96-well white plates. Incubate 24h.",
        duration_minutes: 15,
        temperature_celsius: 37,
        equipment: "Multichannel pipette",
        reagents: [{ name: "Complete DMEM", volume: 100, unit: "uL" }],
      },
      {
        id: "step-2b",
        step_number: 2,
        title: "Add CellTiter-Glo Reagent",
        description: "Add equal volume of CellTiter-Glo reagent. Mix on orbital shaker for 2 min.",
        duration_minutes: 12,
        temperature_celsius: 25,
        equipment: "Orbital shaker, Plate reader",
        reagents: [{ name: "CellTiter-Glo Reagent", volume: 100, unit: "uL" }],
      },
    ],
    created_at: "2026-04-01T11:00:00Z",
    updated_at: "2026-04-01T11:00:00Z",
  },
  {
    id: "proto-3",
    name: "RNA Extraction (TRIzol)",
    description: "Total RNA isolation using TRIzol reagent",
    version: 1,
    status: "draft",
    is_template: true,
    steps: [
      {
        id: "step-3a",
        step_number: 1,
        title: "Cell Lysis",
        description: "Add 1 mL TRIzol per 10 cm2 of culture area. Pipette up and down to lyse.",
        duration_minutes: 5,
        temperature_celsius: 25,
        reagents: [{ name: "TRIzol Reagent", volume: 1, unit: "mL" }],
      },
    ],
    created_at: "2026-04-09T15:30:00Z",
    updated_at: "2026-04-09T15:30:00Z",
  },
];

interface ProtocolState {
  protocols: Protocol[];
  activeProtocolId: string | null;
  loading: boolean;
  inventoryCheck: InventoryCheckResult[] | null;
  dilutionResult: DilutionResult | null;

  fetchProtocols: () => Promise<void>;
  createProtocol: (partial: Partial<Protocol>) => Promise<void>;
  generateProtocol: (description: string) => Promise<void>;
  addStep: (protocolId: string) => void;
  updateStep: (protocolId: string, stepId: string, updates: Partial<ProtocolStep>) => void;
  removeStep: (protocolId: string, stepId: string) => void;
  reorderSteps: (protocolId: string, fromIndex: number, toIndex: number) => void;
  publishProtocol: (id: string) => Promise<void>;
  newVersion: (id: string) => void;
  checkInventory: (id: string) => Promise<void>;
  calculateDilution: (stockConc: number, targetConc: number, targetVol: number, unit: string) => Promise<void>;
  setActiveProtocol: (id: string | null) => void;
  updateProtocol: (id: string, updates: Partial<Protocol>) => void;
  deleteProtocol: (id: string) => void;
}

export const useProtocolStore = create<ProtocolState>()(
  persist(
    (set, get) => ({
      protocols: shouldUseDemoData() ? DEMO_PROTOCOLS : [],
      activeProtocolId: null,
      loading: false,
      inventoryCheck: null,
      dilutionResult: null,

      fetchProtocols: async () => {
        set({ loading: true });
        try {
          const data = await api<Protocol[]>("/api/v1/protocols");
          set({ protocols: data.length > 0 ? data : (isDemoMode() ? DEMO_PROTOCOLS : []), loading: false });
        } catch {
          showErrorToast("save changes");
          set({ loading: false });
        }
      },

      createProtocol: async (partial) => {
        const protocol: Protocol = {
          id: generateId(),
          name: partial.name || "Untitled Protocol",
          description: partial.description || "",
          version: 1,
          status: "draft",
          is_template: partial.is_template || false,
          steps: partial.steps || [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        set({ loading: true });
        try {
          const created = await api<Protocol>("/api/v1/protocols", {
            method: "POST",
            body: JSON.stringify(protocol),
          });
          set((s) => ({ protocols: [created, ...s.protocols], loading: false }));
        } catch {
          showErrorToast("save changes");
          if (isDemoMode()) {
            set((s) => ({ protocols: [protocol, ...s.protocols], loading: false }));
          } else {
            set({ loading: false });
          }
        }
      },

      generateProtocol: async (description) => {
        set({ loading: true });
        try {
          const generated = await api<Protocol>("/api/v1/protocols/generate", {
            method: "POST",
            body: JSON.stringify({ description }),
          });
          set((s) => ({ protocols: [generated, ...s.protocols], loading: false }));
        } catch {
          showErrorToast("save changes");
          set({ loading: false });
        }
      },

      addStep: (protocolId) =>
        set((s) => ({
          protocols: s.protocols.map((p) => {
            if (p.id !== protocolId) return p;
            const newStep: ProtocolStep = {
              id: generateStepId(),
              step_number: p.steps.length + 1,
              title: "",
              description: "",
              reagents: [],
            };
            return { ...p, steps: [...p.steps, newStep], updated_at: new Date().toISOString() };
          }),
        })),

      updateStep: (protocolId, stepId, updates) =>
        set((s) => ({
          protocols: s.protocols.map((p) => {
            if (p.id !== protocolId) return p;
            return {
              ...p,
              steps: p.steps.map((st) => (st.id === stepId ? { ...st, ...updates } : st)),
              updated_at: new Date().toISOString(),
            };
          }),
        })),

      removeStep: (protocolId, stepId) =>
        set((s) => ({
          protocols: s.protocols.map((p) => {
            if (p.id !== protocolId) return p;
            const filtered = p.steps.filter((st) => st.id !== stepId);
            return {
              ...p,
              steps: filtered.map((st, i) => ({ ...st, step_number: i + 1 })),
              updated_at: new Date().toISOString(),
            };
          }),
        })),

      reorderSteps: (protocolId, fromIndex, toIndex) =>
        set((s) => ({
          protocols: s.protocols.map((p) => {
            if (p.id !== protocolId) return p;
            const steps = [...p.steps];
            const [moved] = steps.splice(fromIndex, 1);
            steps.splice(toIndex, 0, moved);
            return {
              ...p,
              steps: steps.map((st, i) => ({ ...st, step_number: i + 1 })),
              updated_at: new Date().toISOString(),
            };
          }),
        })),

      publishProtocol: async (id) => {
        set({ loading: true });
        try {
          await api<Protocol>(`/api/v1/protocols/${id}/publish`, { method: "POST" });
          set((s) => ({
            protocols: s.protocols.map((p) =>
              p.id === id ? { ...p, status: "published" as const, updated_at: new Date().toISOString() } : p
            ),
            loading: false,
          }));
        } catch {
          showErrorToast("save changes");
          if (isDemoMode()) {
            set((s) => ({
              protocols: s.protocols.map((p) =>
                p.id === id ? { ...p, status: "published" as const, updated_at: new Date().toISOString() } : p
              ),
              loading: false,
            }));
          } else {
            set({ loading: false });
          }
        }
      },

      newVersion: (id) =>
        set((s) => ({
          protocols: s.protocols.map((p) =>
            p.id === id
              ? { ...p, version: p.version + 1, status: "draft" as const, updated_at: new Date().toISOString() }
              : p
          ),
        })),

      checkInventory: async (id) => {
        set({ loading: true, inventoryCheck: null });
        try {
          const result = await api<InventoryCheckResult[]>(`/api/v1/protocols/${id}/inventory-check`, {
            method: "POST",
          });
          set({ inventoryCheck: result, loading: false });
        } catch {
          showErrorToast("check inventory");
          if (!isDemoMode()) {
            set({ loading: false });
            return;
          }
          const protocol = get().protocols.find((p) => p.id === id);
          if (protocol) {
            const mockCheck: InventoryCheckResult[] = protocol.steps.flatMap((step) =>
              step.reagents.map((r) => ({
                reagent_name: r.name,
                required_volume: r.volume,
                required_unit: r.unit,
                available_volume: Math.random() > 0.3 ? r.volume * 2 : r.volume * 0.5,
                available: Math.random() > 0.3,
              }))
            );
            set({ inventoryCheck: mockCheck, loading: false });
          } else {
            set({ loading: false });
          }
        }
      },

      calculateDilution: async (stockConc, targetConc, targetVol, unit) => {
        set({ loading: true, dilutionResult: null });
        try {
          const result = await api<DilutionResult>("/api/v1/protocols/dilution-calculator", {
            method: "POST",
            body: JSON.stringify({
              c1: stockConc,
              c2: targetConc,
              v2: targetVol,
              unit_concentration: unit,
              unit_volume: unit,
            }),
          });
          set({ dilutionResult: result, loading: false });
        } catch {
          showErrorToast("c1v1 = c2v2 -> v1 = c2*v2/c1");
          // C1V1 = C2V2 -> V1 = C2*V2/C1
          const stockVol = (targetConc * targetVol) / stockConc;
          const diluentVol = targetVol - stockVol;
          set({
            dilutionResult: {
              stock_volume: Math.round(stockVol * 100) / 100,
              diluent_volume: Math.round(diluentVol * 100) / 100,
              unit,
            },
            loading: false,
          });
        }
      },

      setActiveProtocol: (id) => set({ activeProtocolId: id }),

      updateProtocol: (id, updates) =>
        set((s) => ({
          protocols: s.protocols.map((p) =>
            p.id === id ? { ...p, ...updates, updated_at: new Date().toISOString() } : p
          ),
        })),

      deleteProtocol: (id) =>
        set((s) => ({
          protocols: s.protocols.filter((p) => p.id !== id),
          activeProtocolId: s.activeProtocolId === id ? null : s.activeProtocolId,
        })),
    }),
    {
      name: "resonantia-protocols",
      partialize: (state) => ({ protocols: state.protocols }),
    }
  )
);

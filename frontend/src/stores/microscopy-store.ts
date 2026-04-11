import { create } from "zustand";
import type { Channel } from "@/lib/microscopy-demo";

interface CellCache {
  [key: string]: { x: number; y: number; radius: number; intensity: number }[];
}

interface MicroscopyState {
  selectedPlate: number;
  selectedWell: { row: number; col: number };
  selectedChannels: Channel[];
  selectedFOV: number;
  objective: "4x" | "10x" | "20x" | "40x";
  zoom: number;
  panOffset: { x: number; y: number };
  cellsCache: CellCache;

  setPlate: (index: number) => void;
  setWell: (row: number, col: number) => void;
  toggleChannel: (channel: Channel) => void;
  setChannels: (channels: Channel[]) => void;
  setFOV: (fov: number) => void;
  setObjective: (obj: "4x" | "10x" | "20x" | "40x") => void;
  setZoom: (zoom: number) => void;
  setPanOffset: (offset: { x: number; y: number }) => void;
  resetView: () => void;
  cacheCells: (
    key: string,
    cells: { x: number; y: number; radius: number; intensity: number }[]
  ) => void;
}

export const useMicroscopyStore = create<MicroscopyState>()((set) => ({
  selectedPlate: 0,
  selectedWell: { row: 0, col: 1 },
  selectedChannels: ["dapi", "gfp"],
  selectedFOV: 1,
  objective: "20x",
  zoom: 1,
  panOffset: { x: 0, y: 0 },
  cellsCache: {},

  setPlate: (index) =>
    set({ selectedPlate: index, selectedFOV: 1, zoom: 1, panOffset: { x: 0, y: 0 } }),

  setWell: (row, col) =>
    set({ selectedWell: { row, col }, selectedFOV: 1, zoom: 1, panOffset: { x: 0, y: 0 } }),

  toggleChannel: (channel) =>
    set((state) => ({
      selectedChannels: state.selectedChannels.includes(channel)
        ? state.selectedChannels.filter((c) => c !== channel)
        : [...state.selectedChannels, channel],
    })),

  setChannels: (channels) => set({ selectedChannels: channels }),

  setFOV: (fov) => set({ selectedFOV: fov }),

  setObjective: (obj) => set({ objective: obj }),

  setZoom: (zoom) =>
    set((state) => ({
      zoom: Math.max(1, Math.min(zoom, 8)),
      panOffset: zoom <= 1 ? { x: 0, y: 0 } : state.panOffset,
    })),

  setPanOffset: (offset) => set({ panOffset: offset }),

  resetView: () => set({ zoom: 1, panOffset: { x: 0, y: 0 } }),

  cacheCells: (key, cells) =>
    set((state) => ({
      cellsCache: { ...state.cellsCache, [key]: cells },
    })),
}));

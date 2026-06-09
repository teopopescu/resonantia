"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Grid3X3, X } from "lucide-react";
import PlateMapper from "@/components/lab/plate-mapper";
import PlateMapList from "@/components/lab/plate-map-list";
import WorklistGenerator from "@/components/lab/worklist-generator";
import { usePlateStore, type Plate, type PlateMap } from "@/stores/plate-store";
import { generateWellLabels, PLATE_CONFIGS } from "@/lib/plate-utils";
import type { WellData } from "@/lib/plate-utils";
import {
  PageHeader,
  PageHeaderPrimary,
  SegmentedControl,
} from "@/components/lab/primitives/page-header";

function generateId() {
  return `pm-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

function createEmptyPlate(name: string, type: 96 | 384): Plate {
  const config = PLATE_CONFIGS[type];
  const labels = generateWellLabels(config.rows, config.cols);
  const wells: Record<string, WellData> = {};
  for (const label of labels) {
    wells[label] = { label, type: "empty" };
  }
  return {
    id: generateId(),
    name,
    type,
    wells,
    createdAt: new Date().toISOString(),
  };
}

export default function PlatesPage() {
  const {
    plateType,
    setPlateType,
    activePlateMapId,
    setActivePlateMap,
    addPlateMap,
    addPlate,
    plateMaps,
  } = usePlateStore();

  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newMapName, setNewMapName] = useState("");

  const activeMap = plateMaps.find((m) => m.id === activePlateMapId);
  const draftCount = plateMaps.filter((m) => m.status === "draft").length;

  const handleCreatePlateMap = () => {
    const name = newMapName.trim() || `Plate Map ${Date.now().toString(36)}`;
    const destPlate = createEmptyPlate(`${name} — Dest`, plateType);
    addPlate(destPlate);
    const pm: PlateMap = {
      id: generateId(),
      name,
      sourcePlateIds: [],
      destinationPlateId: destPlate.id,
      mappings: [],
      status: "draft",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    addPlateMap(pm);
    setActivePlateMap(pm.id);
    setShowNewDialog(false);
    setNewMapName("");
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="03"
        markerLabel="Run Builder · plate maps & worklists"
        title="Run Builder"
        meta={
          activeMap ? (
            <>
              <em className="not-italic text-brand">{activeMap.name}</em> ·{" "}
              {plateType}-well · {activeMap.status}
            </>
          ) : (
            <>
              {plateMaps.length} runs · {draftCount} draft · {plateType}-well default
            </>
          )
        }
      >
        <SegmentedControl<"96" | "384">
          options={[
            { label: "96", value: "96" },
            { label: "384", value: "384" },
          ]}
          value={String(plateType) as "96" | "384"}
          onChange={(v) => setPlateType(v === "96" ? 96 : 384)}
        />
        <PageHeaderPrimary onClick={() => setShowNewDialog(true)}>
          <Plus size={14} />
          New run
        </PageHeaderPrimary>
      </PageHeader>

      <main className="flex-1 overflow-auto px-6 lg:px-8 py-8 min-h-0">
        <div className="max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-8">
          <aside>
            <h2 className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
              Runs
            </h2>
            <PlateMapList />
          </aside>

          <div className="space-y-6">
            {activePlateMapId ? (
              <>
                <section className="bg-surface border border-line rounded-md p-6">
                  <PlateMapper />
                </section>
                <section className="bg-surface border border-line rounded-md p-6">
                  <WorklistGenerator />
                </section>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-center bg-surface border border-line rounded-md">
                <div className="w-12 h-12 rounded-md bg-brand-soft flex items-center justify-center mb-4">
                  <Grid3X3 size={22} className="text-brand" />
                </div>
                <h3 className="text-[15px] font-semibold text-ink mb-1">
                  No run selected
                </h3>
                <p className="text-[13px] text-ink-muted max-w-xs">
                  Select an existing run from the sidebar or create a new one
                  to design the plate map and export an approved worklist.
                </p>
                <button
                  onClick={() => setShowNewDialog(true)}
                  className="mt-5 inline-flex items-center gap-2 px-3.5 py-2 bg-brand text-white text-[13px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
                  style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
                >
                  <Plus size={14} />
                  New run
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* New plate map dialog */}
      <AnimatePresence>
        {showNewDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm"
            onClick={() => setShowNewDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.97, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.97, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 400 }}
              className="bg-surface border border-line rounded-md shadow-xl p-6 w-full max-w-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-[15px] font-semibold text-ink">
                  New run
                </h3>
                <button
                  onClick={() => setShowNewDialog(false)}
                  className="p-1 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              <label className="block font-mono text-[10.5px] font-medium text-ink-subtle uppercase tracking-[0.06em] mb-2">
                Name
              </label>
              <input
                type="text"
                value={newMapName}
                onChange={(e) => setNewMapName(e.target.value)}
                placeholder="e.g. HTS Screen Round 2"
                className="w-full text-sm px-3 py-2 rounded-[3px] border border-line bg-bg text-ink placeholder:text-ink-subtle focus:outline-none focus:border-brand/40 transition-colors mb-5"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreatePlateMap();
                }}
                autoFocus
              />

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowNewDialog(false)}
                  className="px-3 py-1.5 text-[13px] text-ink-muted hover:text-ink transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreatePlateMap}
                  className="inline-flex items-center gap-2 px-3.5 py-2 bg-brand text-white text-[13px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
                  style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
                >
                  Create run
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

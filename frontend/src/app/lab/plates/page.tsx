"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Grid3X3, LayoutGrid, X } from "lucide-react";
import PlateMapper from "@/components/lab/plate-mapper";
import PlateMapList from "@/components/lab/plate-map-list";
import WorklistGenerator from "@/components/lab/worklist-generator";
import { usePlateStore, type Plate, type PlateMap } from "@/stores/plate-store";
import { generateWellLabels, PLATE_CONFIGS } from "@/lib/plate-utils";
import type { WellData } from "@/lib/plate-utils";

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
    plates,
  } = usePlateStore();

  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newMapName, setNewMapName] = useState("");

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
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-charcoal tracking-tight">
              Plate Map Designer
            </h1>
            <p className="text-xs text-muted mt-0.5">
              Design, map, and export microwell plate layouts
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Plate type toggle */}
            <div className="flex items-center bg-cream rounded-md border border-border p-0.5">
              <button
                onClick={() => setPlateType(96)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  plateType === 96
                    ? "bg-white shadow-sm text-charcoal"
                    : "text-muted hover:text-charcoal"
                }`}
              >
                <Grid3X3 size={12} />
                96
              </button>
              <button
                onClick={() => setPlateType(384)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  plateType === 384
                    ? "bg-white shadow-sm text-charcoal"
                    : "text-muted hover:text-charcoal"
                }`}
              >
                <LayoutGrid size={12} />
                384
              </button>
            </div>

            {/* New plate map button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowNewDialog(true)}
              className="flex items-center gap-1.5 bg-amber text-charcoal px-4 py-2 rounded-md text-xs font-semibold shadow-sm hover:bg-amber-light transition-colors"
            >
              <Plus size={14} />
              New Plate Map
            </motion.button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1440px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          {/* Sidebar — Plate map list */}
          <aside>
            <div className="sticky top-24">
              <h2 className="text-xs font-medium text-muted uppercase tracking-wider mb-3">
                Plate Maps
              </h2>
              <PlateMapList />
            </div>
          </aside>

          {/* Main panel */}
          <div className="space-y-8">
            {activePlateMapId ? (
              <>
                {/* Mapper */}
                <section className="bg-white/60 border border-border rounded-xl p-6">
                  <PlateMapper />
                </section>

                {/* Worklist */}
                <section className="bg-white/60 border border-border rounded-xl p-6">
                  <WorklistGenerator />
                </section>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 rounded-full bg-amber/10 flex items-center justify-center mb-4">
                  <Grid3X3 size={28} className="text-amber" />
                </div>
                <h3 className="text-sm font-semibold text-charcoal mb-1">
                  No plate map selected
                </h3>
                <p className="text-xs text-muted max-w-xs">
                  Select an existing plate map from the sidebar or create a new one to start
                  designing your plate layout.
                </p>
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
            className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/30 backdrop-blur-sm"
            onClick={() => setShowNewDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 400 }}
              className="bg-surface border border-border rounded-xl shadow-xl p-6 w-full max-w-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-charcoal">New Plate Map</h3>
                <button
                  onClick={() => setShowNewDialog(false)}
                  className="p-1 rounded-md text-muted hover:text-charcoal hover:bg-cream transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1.5">
                Name
              </label>
              <input
                type="text"
                value={newMapName}
                onChange={(e) => setNewMapName(e.target.value)}
                placeholder="e.g. HTS Screen Round 2"
                className="w-full text-sm px-3 py-2 rounded-xl border border-border bg-surface text-charcoal placeholder:text-muted/60 focus:outline-none focus:border-amber/40 transition-colors mb-4"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreatePlateMap();
                }}
                autoFocus
              />

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowNewDialog(false)}
                  className="px-3 py-1.5 text-xs text-muted hover:text-charcoal transition-colors"
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCreatePlateMap}
                  className="bg-amber text-charcoal px-4 py-1.5 rounded-md text-xs font-semibold hover:bg-amber-light transition-colors"
                >
                  Create
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Shuffle, Copy, FlaskConical, Cherry, Trash2 } from "lucide-react";
import PlateView from "./plate-view";
import { usePlateStore, type MappingMode, type WellMapping } from "@/stores/plate-store";
import {
  PLATE_CONFIGS,
  generateCherryPickMapping,
  generateSerialDilution,
  generateWellLabels,
  wellToCoords,
} from "@/lib/plate-utils";
import type { WellData } from "@/lib/plate-utils";

const MODE_CONFIG: Record<MappingMode, { label: string; icon: React.ReactNode; desc: string }> = {
  "cherry-pick": {
    label: "Cherry Pick",
    icon: <Cherry size={14} />,
    desc: "Select individual source wells and map to destination",
  },
  "serial-dilution": {
    label: "Serial Dilution",
    icon: <FlaskConical size={14} />,
    desc: "Create dilution series from a starting well",
  },
  replicate: {
    label: "Replicate",
    icon: <Copy size={14} />,
    desc: "Copy source layout to destination plate",
  },
  randomize: {
    label: "Randomize",
    icon: <Shuffle size={14} />,
    desc: "Randomize well assignments on destination",
  },
};

function createEmptyPlateWells(type: 96 | 384): Record<string, WellData> {
  const config = PLATE_CONFIGS[type];
  const labels = generateWellLabels(config.rows, config.cols);
  const wells: Record<string, WellData> = {};
  for (const label of labels) {
    wells[label] = { label, type: "empty" };
  }
  return wells;
}

export default function PlateMapper() {
  const {
    plates,
    plateMaps,
    activePlateMapId,
    activeSourcePlateId,
    selectedSourceWells,
    selectedDestWells,
    mappingMode,
    plateType,
    transferVolume,
    dilutionFactor,
    dilutionSteps,
    dilutionDirection,
    setActiveSourcePlate,
    toggleSourceWell,
    selectSourceWells,
    toggleDestWell,
    selectDestWells,
    clearSourceSelection,
    clearDestSelection,
    setMappingMode,
    setTransferVolume,
    setDilutionFactor,
    setDilutionSteps,
    setDilutionDirection,
    addMappings,
    clearMappings,
  } = usePlateStore();

  const [showMappingTable, setShowMappingTable] = useState(true);

  const activeMap = plateMaps.find((pm) => pm.id === activePlateMapId);
  const sourcePlate = plates.find((p) => p.id === activeSourcePlateId);
  const destWells = useMemo(() => createEmptyPlateWells(plateType), [plateType]);

  // Build destination wells with mapping colors
  const destWellsWithMappings = useMemo(() => {
    if (!activeMap) return destWells;
    const updated = { ...destWells };
    for (const m of activeMap.mappings) {
      const srcPlate = plates.find((p) => p.id === m.sourcePlateId);
      const srcWell = srcPlate?.wells[m.sourceWell];
      if (srcWell) {
        updated[m.destWell] = {
          label: m.destWell,
          type: srcWell.type,
          compound: m.compound,
          concentration: m.concentration,
        };
      }
    }
    return updated;
  }, [activeMap, destWells, plates]);

  const handleApplyMapping = () => {
    if (!activeMap || !sourcePlate || !activeSourcePlateId) return;

    let newMappings: WellMapping[] = [];

    if (mappingMode === "cherry-pick") {
      if (selectedSourceWells.length === 0) return;
      const destStart = selectedDestWells[0] || "A1";
      const pairs = generateCherryPickMapping(selectedSourceWells, destStart);
      newMappings = pairs.map((p) => ({
        sourceWell: p.sourceWell,
        destWell: p.destWell,
        compound: sourcePlate.wells[p.sourceWell]?.compound || "",
        concentration: sourcePlate.wells[p.sourceWell]?.concentration || 0,
        volume: transferVolume,
        sourcePlateId: activeSourcePlateId,
      }));
    } else if (mappingMode === "serial-dilution") {
      if (selectedSourceWells.length === 0 || selectedDestWells.length === 0) return;
      const srcWell = selectedSourceWells[0];
      const destStart = selectedDestWells[0];
      const series = generateSerialDilution(destStart, dilutionDirection, dilutionSteps, dilutionFactor);
      const baseConc = sourcePlate.wells[srcWell]?.concentration || 100;
      newMappings = series.map((s) => ({
        sourceWell: srcWell,
        destWell: s.well,
        compound: sourcePlate.wells[srcWell]?.compound || "",
        concentration: baseConc * s.dilution,
        volume: transferVolume,
        sourcePlateId: activeSourcePlateId,
      }));
    } else if (mappingMode === "replicate") {
      if (selectedSourceWells.length === 0) return;
      newMappings = selectedSourceWells.map((sw) => ({
        sourceWell: sw,
        destWell: sw,
        compound: sourcePlate.wells[sw]?.compound || "",
        concentration: sourcePlate.wells[sw]?.concentration || 0,
        volume: transferVolume,
        sourcePlateId: activeSourcePlateId,
      }));
    } else if (mappingMode === "randomize") {
      if (selectedSourceWells.length === 0) return;
      const config = PLATE_CONFIGS[plateType];
      const allDest = generateWellLabels(config.rows, config.cols);
      const shuffled = [...allDest].sort(() => Math.random() - 0.5);
      newMappings = selectedSourceWells.map((sw, i) => ({
        sourceWell: sw,
        destWell: shuffled[i % shuffled.length],
        compound: sourcePlate.wells[sw]?.compound || "",
        concentration: sourcePlate.wells[sw]?.concentration || 0,
        volume: transferVolume,
        sourcePlateId: activeSourcePlateId,
      }));
    }

    if (newMappings.length > 0) {
      addMappings(newMappings);
      clearSourceSelection();
      clearDestSelection();
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode selector */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(MODE_CONFIG) as [MappingMode, typeof MODE_CONFIG[MappingMode]][]).map(
          ([mode, cfg]) => (
            <button
              key={mode}
              onClick={() => setMappingMode(mode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                mappingMode === mode
                  ? "bg-amber text-charcoal shadow-sm"
                  : "bg-surface border border-border text-muted hover:border-amber/50 hover:text-charcoal"
              }`}
            >
              {cfg.icon}
              {cfg.label}
            </button>
          )
        )}
      </div>

      {/* Mode description */}
      <p className="text-xs text-muted">
        {MODE_CONFIG[mappingMode].desc}
      </p>

      {/* Parameters row */}
      <div className="flex flex-wrap items-end gap-4">
        {/* Source plate selector */}
        <div>
          <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1">
            Source Plate
          </label>
          <select
            value={activeSourcePlateId || ""}
            onChange={(e) => setActiveSourcePlate(e.target.value || null)}
            className="text-xs px-2.5 py-1.5 rounded-xl border border-border bg-surface text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.5rem_center] pr-7 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
          >
            <option value="">Select plate...</option>
            {plates.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Transfer volume */}
        <div>
          <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1">
            Volume (nL)
          </label>
          <input
            type="number"
            value={transferVolume}
            onChange={(e) => setTransferVolume(Number(e.target.value))}
            className="w-20 text-xs px-2.5 py-1.5 rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
            min={0}
          />
        </div>

        {/* Dilution-specific params */}
        <AnimatePresence>
          {mappingMode === "serial-dilution" && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="flex items-end gap-4"
            >
              <div>
                <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1">
                  Dilution Factor
                </label>
                <input
                  type="number"
                  value={dilutionFactor}
                  onChange={(e) => setDilutionFactor(Number(e.target.value))}
                  className="w-16 text-xs px-2.5 py-1.5 rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
                  min={1}
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1">
                  Steps
                </label>
                <input
                  type="number"
                  value={dilutionSteps}
                  onChange={(e) => setDilutionSteps(Number(e.target.value))}
                  className="w-16 text-xs px-2.5 py-1.5 rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
                  min={1}
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-muted uppercase tracking-wider mb-1">
                  Direction
                </label>
                <select
                  value={dilutionDirection}
                  onChange={(e) =>
                    setDilutionDirection(e.target.value as "horizontal" | "vertical")
                  }
                  className="text-xs px-2.5 py-1.5 rounded-xl border border-border bg-surface text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.5rem_center] pr-7 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
                >
                  <option value="horizontal">Horizontal</option>
                  <option value="vertical">Vertical</option>
                </select>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Plates side-by-side */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_auto_1fr] gap-4 items-start">
        {/* Source plate */}
        <div>
          {sourcePlate ? (
            <PlateView
              plateType={sourcePlate.type}
              wells={sourcePlate.wells}
              selectedWells={selectedSourceWells}
              onWellClick={(w) => toggleSourceWell(w)}
              onWellsSelect={(ws) => selectSourceWells(ws)}
              label={`Source: ${sourcePlate.name}`}
            />
          ) : (
            <div className="flex items-center justify-center h-48 bg-surface border border-dashed border-border rounded-lg text-xs text-muted">
              Select a source plate
            </div>
          )}
        </div>

        {/* Arrow + Apply */}
        <div className="flex flex-col items-center justify-center gap-3 py-8 xl:py-16">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleApplyMapping}
            className="flex items-center gap-1.5 bg-amber text-charcoal px-4 py-2 rounded-md text-xs font-semibold shadow-sm hover:bg-amber-light transition-colors"
          >
            Apply
            <ArrowRight size={14} />
          </motion.button>
          {activeMap && activeMap.mappings.length > 0 && (
            <button
              onClick={() => clearMappings(activeMap.id)}
              className="flex items-center gap-1 text-[11px] text-muted hover:text-red-500 transition-colors"
            >
              <Trash2 size={12} />
              Clear
            </button>
          )}
        </div>

        {/* Destination plate */}
        <div>
          <PlateView
            plateType={plateType}
            wells={destWellsWithMappings}
            selectedWells={selectedDestWells}
            onWellClick={(w) => toggleDestWell(w)}
            onWellsSelect={(ws) => selectDestWells(ws)}
            label="Destination"
          />
        </div>
      </div>

      {/* Selection summary */}
      <div className="flex gap-6 text-[11px] text-muted">
        <span>
          Source selected:{" "}
          <span className="font-semibold text-charcoal">{selectedSourceWells.length}</span> wells
        </span>
        <span>
          Dest selected:{" "}
          <span className="font-semibold text-charcoal">{selectedDestWells.length}</span> wells
        </span>
        {activeMap && (
          <span>
            Mappings:{" "}
            <span className="font-semibold text-charcoal">{activeMap.mappings.length}</span>
          </span>
        )}
      </div>

      {/* Mapping table */}
      {activeMap && activeMap.mappings.length > 0 && (
        <div>
          <button
            onClick={() => setShowMappingTable((v) => !v)}
            className="text-xs text-muted hover:text-charcoal mb-2 flex items-center gap-1 transition-colors"
          >
            <motion.span
              animate={{ rotate: showMappingTable ? 90 : 0 }}
              className="inline-block"
            >
              &#9654;
            </motion.span>
            Mapping Table ({activeMap.mappings.length} transfers)
          </button>
          <AnimatePresence>
            {showMappingTable && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="bg-surface border border-border rounded-lg overflow-hidden">
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-cream">
                        <tr className="text-left text-[10px] uppercase tracking-wider text-muted">
                          <th className="px-3 py-2">#</th>
                          <th className="px-3 py-2">Source</th>
                          <th className="px-3 py-2">Dest</th>
                          <th className="px-3 py-2">Compound</th>
                          <th className="px-3 py-2">Conc. (uM)</th>
                          <th className="px-3 py-2">Vol. (nL)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeMap.mappings.map((m, i) => (
                          <tr
                            key={i}
                            className="border-t border-border/50 hover:bg-cream/50 transition-colors"
                          >
                            <td className="px-3 py-1.5 text-muted">{i + 1}</td>
                            <td className="px-3 py-1.5 font-mono">{m.sourceWell}</td>
                            <td className="px-3 py-1.5 font-mono">{m.destWell}</td>
                            <td className="px-3 py-1.5">{m.compound || "-"}</td>
                            <td className="px-3 py-1.5">{m.concentration || "-"}</td>
                            <td className="px-3 py-1.5">{m.volume}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

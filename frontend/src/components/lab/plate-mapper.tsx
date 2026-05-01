"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Shuffle, Copy, FlaskConical, Cherry, Trash2, ChevronRight } from "lucide-react";
import PlateView from "./plate-view";
import { usePlateStore, type MappingMode, type WellMapping } from "@/stores/plate-store";
import {
  PLATE_CONFIGS,
  generateCherryPickMapping,
  generateSerialDilution,
  generateWellLabels,
} from "@/lib/plate-utils";
import type { WellData } from "@/lib/plate-utils";
import { cn } from "@/lib/utils";

const MODE_CONFIG: Record<
  MappingMode,
  { label: string; icon: React.ReactNode; desc: string; code: string }
> = {
  "cherry-pick": {
    label: "Cherry pick",
    icon: <Cherry size={13} />,
    desc: "Select individual source wells and map them to the destination.",
    code: "MD/01",
  },
  "serial-dilution": {
    label: "Serial dilution",
    icon: <FlaskConical size={13} />,
    desc: "Create a dilution series from a starting well.",
    code: "MD/02",
  },
  replicate: {
    label: "Replicate",
    icon: <Copy size={13} />,
    desc: "Copy the source layout onto the destination plate.",
    code: "MD/03",
  },
  randomize: {
    label: "Randomize",
    icon: <Shuffle size={13} />,
    desc: "Randomize well assignments on the destination.",
    code: "MD/04",
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

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
    </label>
  );
}

const inputClass =
  "px-2.5 py-1.5 font-mono text-[12px] rounded-[3px] border border-line bg-bg text-ink focus:outline-none focus:border-brand/40 transition-colors";

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
    <div className="space-y-5">
      {/* Mode selector */}
      <div className="flex flex-wrap items-center gap-2">
        {(Object.entries(MODE_CONFIG) as [MappingMode, typeof MODE_CONFIG[MappingMode]][]).map(
          ([mode, cfg]) => {
            const isOn = mappingMode === mode;
            return (
              <button
                key={mode}
                onClick={() => setMappingMode(mode)}
                className={cn(
                  "inline-flex items-center gap-2 px-3 py-1.5 rounded-[3px] text-[12.5px] font-medium transition-colors border",
                  isOn
                    ? "bg-brand-soft text-brand border-brand/30"
                    : "bg-surface text-ink-muted border-line hover:border-line-strong hover:text-ink"
                )}
              >
                <span className="font-mono text-[10px] tracking-[0.04em] opacity-70">
                  {cfg.code}
                </span>
                {cfg.icon}
                {cfg.label}
              </button>
            );
          }
        )}
      </div>

      <p className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle">
        <span className="text-brand">›</span> {MODE_CONFIG[mappingMode].desc}
      </p>

      {/* Parameters row */}
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <FieldLabel>source plate</FieldLabel>
          <select
            value={activeSourcePlateId || ""}
            onChange={(e) => setActiveSourcePlate(e.target.value || null)}
            className={cn(inputClass, "min-w-[180px] cursor-pointer")}
          >
            <option value="">select plate…</option>
            {plates.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <FieldLabel>volume (nL)</FieldLabel>
          <input
            type="number"
            value={transferVolume}
            onChange={(e) => setTransferVolume(Number(e.target.value))}
            className={cn(inputClass, "w-24")}
            min={0}
          />
        </div>

        <AnimatePresence>
          {mappingMode === "serial-dilution" && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="flex items-end gap-3"
            >
              <div>
                <FieldLabel>dilution factor</FieldLabel>
                <input
                  type="number"
                  value={dilutionFactor}
                  onChange={(e) => setDilutionFactor(Number(e.target.value))}
                  className={cn(inputClass, "w-20")}
                  min={1}
                />
              </div>
              <div>
                <FieldLabel>steps</FieldLabel>
                <input
                  type="number"
                  value={dilutionSteps}
                  onChange={(e) => setDilutionSteps(Number(e.target.value))}
                  className={cn(inputClass, "w-20")}
                  min={1}
                />
              </div>
              <div>
                <FieldLabel>direction</FieldLabel>
                <select
                  value={dilutionDirection}
                  onChange={(e) =>
                    setDilutionDirection(e.target.value as "horizontal" | "vertical")
                  }
                  className={cn(inputClass, "cursor-pointer")}
                >
                  <option value="horizontal">horizontal</option>
                  <option value="vertical">vertical</option>
                </select>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Plates side-by-side */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_auto_1fr] gap-5 items-start">
        <div>
          {sourcePlate ? (
            <PlateView
              plateType={sourcePlate.type}
              wells={sourcePlate.wells}
              selectedWells={selectedSourceWells}
              onWellClick={(w) => toggleSourceWell(w)}
              onWellsSelect={(ws) => selectSourceWells(ws)}
              label={`SOURCE · ${sourcePlate.name}`}
            />
          ) : (
            <div className="flex items-center justify-center h-48 bg-bg border border-dashed border-line-strong rounded-[5px] font-mono text-[11.5px] tracking-[0.02em] uppercase text-ink-subtle">
              select a source plate
            </div>
          )}
        </div>

        <div className="flex flex-col items-center justify-center gap-3 py-8 xl:py-16">
          <button
            onClick={handleApplyMapping}
            className="inline-flex items-center gap-2 bg-brand text-white px-3.5 py-2 rounded-[3px] text-[13px] font-semibold hover:bg-brand-strong transition-colors"
            style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
          >
            Apply
            <ArrowRight size={14} />
          </button>
          {activeMap && activeMap.mappings.length > 0 && (
            <button
              onClick={() => clearMappings(activeMap.id)}
              className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle hover:text-mch transition-colors"
            >
              <Trash2 size={11} />
              clear all
            </button>
          )}
        </div>

        <div>
          <PlateView
            plateType={plateType}
            wells={destWellsWithMappings}
            selectedWells={selectedDestWells}
            onWellClick={(w) => toggleDestWell(w)}
            onWellsSelect={(ws) => selectDestWells(ws)}
            label="DESTINATION"
          />
        </div>
      </div>

      {/* Selection summary */}
      <div className="flex flex-wrap gap-x-6 gap-y-2 font-mono text-[11px] tracking-[0.02em] text-ink-subtle uppercase">
        <span>
          source selected ·{" "}
          <span className="text-ink font-medium normal-case tracking-normal">
            {selectedSourceWells.length}
          </span>
        </span>
        <span>
          dest selected ·{" "}
          <span className="text-ink font-medium normal-case tracking-normal">
            {selectedDestWells.length}
          </span>
        </span>
        {activeMap && (
          <span>
            mappings ·{" "}
            <span className="text-brand font-semibold normal-case tracking-normal">
              {activeMap.mappings.length}
            </span>
          </span>
        )}
      </div>

      {/* Mapping table */}
      {activeMap && activeMap.mappings.length > 0 && (
        <div>
          <button
            onClick={() => setShowMappingTable((v) => !v)}
            className="inline-flex items-center gap-1 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-muted hover:text-ink mb-2 transition-colors"
          >
            <ChevronRight
              size={12}
              className={cn(
                "transition-transform",
                showMappingTable && "rotate-90"
              )}
            />
            mapping table · {activeMap.mappings.length} transfers
          </button>
          <AnimatePresence>
            {showMappingTable && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="bg-bg border border-line rounded-[5px] overflow-hidden">
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full">
                      <thead className="sticky top-0 bg-surface">
                        <tr>
                          {["#", "source", "dest", "compound", "conc. (µM)", "vol. (nL)"].map(
                            (h) => (
                              <th
                                key={h}
                                className="text-left px-3 py-2.5 border-b border-line font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle"
                              >
                                {h}
                              </th>
                            )
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {activeMap.mappings.map((m, i) => (
                          <tr
                            key={i}
                            className="border-b border-line last:border-b-0 hover:bg-surface transition-colors"
                          >
                            <td className="px-3 py-2 font-mono text-[11.5px] text-ink-subtle">
                              {i + 1}
                            </td>
                            <td className="px-3 py-2 font-mono text-[12px] text-ink">
                              {m.sourceWell}
                            </td>
                            <td className="px-3 py-2 font-mono text-[12px] text-brand font-medium">
                              {m.destWell}
                            </td>
                            <td className="px-3 py-2 text-[12.5px] text-ink-muted">
                              {m.compound || "—"}
                            </td>
                            <td className="px-3 py-2 font-mono text-[11.5px] text-ink-muted">
                              {m.concentration ? m.concentration.toFixed(2) : "—"}
                            </td>
                            <td className="px-3 py-2 font-mono text-[11.5px] text-ink-muted">
                              {m.volume}
                            </td>
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

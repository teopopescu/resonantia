"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PLATE_CONFIGS,
  rowLetter,
  coordsToWell,
  wellColor,
  wellTypeLabel,
} from "@/lib/plate-utils";
import type { WellData } from "@/lib/plate-utils";

interface PlateViewProps {
  plateType: 96 | 384;
  wells: Record<string, WellData>;
  selectedWells: string[];
  onWellClick?: (well: string) => void;
  onWellsSelect?: (wells: string[]) => void;
  readonly?: boolean;
  compact?: boolean;
  label?: string;
}

interface TooltipData {
  well: WellData;
  x: number;
  y: number;
}

export default function PlateView({
  plateType,
  wells,
  selectedWells,
  onWellClick,
  onWellsSelect,
  readonly = false,
  compact = false,
  label,
}: PlateViewProps) {
  const config = PLATE_CONFIGS[plateType];
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ row: number; col: number } | null>(null);
  const [dragEnd, setDragEnd] = useState<{ row: number; col: number } | null>(null);

  const wellSize = compact ? 18 : plateType === 384 ? 16 : 28;
  const gap = compact ? 2 : plateType === 384 ? 2 : 4;
  const headerSize = compact ? 20 : 28;
  const totalW = headerSize + config.cols * (wellSize + gap) + gap;
  const totalH = headerSize + config.rows * (wellSize + gap) + gap;

  const getDragSelectedWells = useCallback(() => {
    if (!dragStart || !dragEnd) return [];
    const minR = Math.min(dragStart.row, dragEnd.row);
    const maxR = Math.max(dragStart.row, dragEnd.row);
    const minC = Math.min(dragStart.col, dragEnd.col);
    const maxC = Math.max(dragStart.col, dragEnd.col);
    const result: string[] = [];
    for (let r = minR; r <= maxR; r++) {
      for (let c = minC; c <= maxC; c++) {
        result.push(coordsToWell(r, c));
      }
    }
    return result;
  }, [dragStart, dragEnd]);

  const dragSelected = getDragSelectedWells();

  const handleMouseDown = (row: number, col: number) => {
    if (readonly) return;
    setIsDragging(true);
    setDragStart({ row, col });
    setDragEnd({ row, col });
  };

  const handleMouseEnter = (row: number, col: number) => {
    if (isDragging) {
      setDragEnd({ row, col });
    }
  };

  const handleMouseUp = () => {
    if (isDragging && dragStart && dragEnd) {
      const selected = getDragSelectedWells();
      if (selected.length === 1 && onWellClick) {
        onWellClick(selected[0]);
      } else if (onWellsSelect) {
        onWellsSelect(selected);
      }
    }
    setIsDragging(false);
    setDragStart(null);
    setDragEnd(null);
  };

  return (
    <div className="relative" ref={containerRef}>
      {label && (
        <p className="font-mono text-[10.5px] font-medium text-ink-subtle mb-2 uppercase tracking-[0.06em]">
          {label}
        </p>
      )}
      <div
        className="relative bg-bg border border-line rounded-[5px] p-3 select-none overflow-x-auto"
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          if (isDragging) handleMouseUp();
          setTooltip(null);
        }}
      >
        <svg
          width={totalW}
          height={totalH}
          viewBox={`0 0 ${totalW} ${totalH}`}
          className="block"
        >
          {/* Column headers */}
          {Array.from({ length: config.cols }, (_, c) => (
            <text
              key={`ch-${c}`}
              x={headerSize + c * (wellSize + gap) + gap + wellSize / 2}
              y={headerSize / 2 + 1}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-muted"
              fontSize={compact ? 8 : 10}
              fontFamily="var(--font-sans)"
              fontWeight={500}
            >
              {c + 1}
            </text>
          ))}

          {/* Row headers */}
          {Array.from({ length: config.rows }, (_, r) => (
            <text
              key={`rh-${r}`}
              x={headerSize / 2}
              y={headerSize + r * (wellSize + gap) + gap + wellSize / 2}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-muted"
              fontSize={compact ? 8 : 10}
              fontFamily="var(--font-sans)"
              fontWeight={500}
            >
              {rowLetter(r)}
            </text>
          ))}

          {/* Wells */}
          {Array.from({ length: config.rows }, (_, r) =>
            Array.from({ length: config.cols }, (_, c) => {
              const label = coordsToWell(r, c);
              const well = wells[label] || { label, type: "empty" as const };
              const isSelected = selectedWells.includes(label);
              const isDragSel = dragSelected.includes(label);
              const cx =
                headerSize + c * (wellSize + gap) + gap + wellSize / 2;
              const cy =
                headerSize + r * (wellSize + gap) + gap + wellSize / 2;
              const radius = wellSize / 2 - 1;

              return (
                <g
                  key={label}
                  onMouseDown={() => handleMouseDown(r, c)}
                  onMouseEnter={(e) => {
                    handleMouseEnter(r, c);
                    if (!isDragging) {
                      const rect = containerRef.current?.getBoundingClientRect();
                      if (rect) {
                        setTooltip({
                          well,
                          x: e.clientX - rect.left,
                          y: e.clientY - rect.top - 10,
                        });
                      }
                    }
                  }}
                  onMouseLeave={() => {
                    if (!isDragging) setTooltip(null);
                  }}
                  style={{ cursor: readonly ? "default" : "pointer" }}
                >
                  {/* Well circle */}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={radius}
                    fill={wellColor(well.type)}
                    opacity={isSelected || isDragSel ? 1 : 0.75}
                    stroke={
                      isSelected
                        ? "#1F4D3A"
                        : isDragSel
                          ? "#1F4D3A"
                          : "transparent"
                    }
                    strokeWidth={isSelected ? 2.5 : isDragSel ? 1.5 : 0}
                    style={{
                      transition: "all 0.15s ease",
                    }}
                  />
                  {/* Selection ring */}
                  {isSelected && (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={radius + 2}
                      fill="none"
                      stroke="#1F4D3A"
                      strokeWidth={1}
                      opacity={0.5}
                    />
                  )}
                </g>
              );
            })
          )}
        </svg>

        {/* Tooltip */}
        <AnimatePresence>
          {tooltip && !isDragging && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.12 }}
              className="absolute z-50 pointer-events-none bg-ink text-bg text-[11px] font-mono leading-tight rounded-[3px] px-2.5 py-1.5 shadow-md"
              style={{
                left: tooltip.x,
                top: tooltip.y,
                transform: "translate(-50%, -100%)",
              }}
            >
              <span className="font-semibold">{tooltip.well.label}</span>
              <span className="mx-1 opacity-40">|</span>
              <span>{wellTypeLabel(tooltip.well.type)}</span>
              {tooltip.well.compound && (
                <>
                  <br />
                  <span className="opacity-70">{tooltip.well.compound}</span>
                  {tooltip.well.concentration != null && (
                    <span className="opacity-70">
                      {" "}
                      {tooltip.well.concentration} uM
                    </span>
                  )}
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Legend */}
      {!compact && (
        <div className="flex flex-wrap gap-4 mt-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted">
          {(
            [
              ["empty", "empty"],
              ["sample", "sample · DAPI"],
              ["compound", "compound · GFP"],
              ["control-negative", "control − · mCh"],
              ["control-positive", "control + · BF"],
            ] as const
          ).map(([type, lbl]) => (
            <span key={type} className="flex items-center gap-1.5">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: wellColor(type) }}
              />
              {lbl}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

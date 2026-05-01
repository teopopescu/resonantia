"use client";

import React, { useState, useCallback } from "react";
import { Grid3X3 } from "lucide-react";
import MicroscopyViewer from "@/components/lab/microscopy-viewer";
import ThumbnailStrip from "@/components/lab/thumbnail-strip";
import {
  ROWS,
  COLS,
  wellLabel,
  seedForWellFov,
  CHANNELS,
  type Channel,
} from "@/lib/microscopy-demo";
import { DEMO_PLATES } from "@/lib/demo-data";
import {
  PageHeader,
  PageHeaderGhost,
} from "@/components/lab/primitives/page-header";
import { cn } from "@/lib/utils";

const TOTAL_FOV = 9;

const inputBase =
  "w-full px-2.5 py-1.5 font-mono text-[12px] rounded-[3px] border border-line bg-bg text-ink focus:outline-none focus:border-brand/40 transition-colors";

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
    </label>
  );
}

export default function MicroscopyPage() {
  const [plateIndex, setPlateIndex] = useState(0);
  const [selectedRow, setSelectedRow] = useState(0);
  const [selectedCol, setSelectedCol] = useState(1);
  const [fov, setFov] = useState(1);
  const [activeChannels, setActiveChannels] = useState<Channel[]>(["dapi", "gfp"]);
  const [metadataOpen, setMetadataOpen] = useState(false);

  const plate = DEMO_PLATES[plateIndex];
  const currentWell = wellLabel(selectedRow, selectedCol);
  const seed = seedForWellFov(plateIndex, selectedRow, selectedCol, fov);

  const handlePrevFov = useCallback(() => setFov((f) => Math.max(1, f - 1)), []);
  const handleNextFov = useCallback(
    () => setFov((f) => Math.min(TOTAL_FOV, f + 1)),
    []
  );

  const toggleChannel = (ch: Channel) => {
    setActiveChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="05"
        markerLabel="Microscopy · browser"
        title="Microscopy Browser"
        meta={
          <>
            {plate?.name} ·{" "}
            <em className="not-italic text-brand">{currentWell}</em> · FOV{" "}
            {fov} / {TOTAL_FOV} · {activeChannels.length} channels
          </>
        }
      >
        <PageHeaderGhost onClick={() => setMetadataOpen((v) => !v)}>
          <Grid3X3 size={14} />
          {metadataOpen ? "Hide metadata" : "Show metadata"}
        </PageHeaderGhost>
      </PageHeader>

      <div className="flex flex-1 min-h-0">
        {/* Left filter panel */}
        <aside className="w-64 shrink-0 bg-bg border-r border-line flex flex-col overflow-y-auto">
          {/* Plate selector */}
          <div className="px-4 py-4 border-b border-line">
            <FieldLabel>plate</FieldLabel>
            <select
              value={plateIndex}
              onChange={(e) => {
                setPlateIndex(Number(e.target.value));
                setFov(1);
              }}
              className={cn(inputBase, "cursor-pointer")}
            >
              {DEMO_PLATES.map((p, i) => (
                <option key={p.id} value={i}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Well selector */}
          <div className="px-4 py-4 border-b border-line">
            <FieldLabel>well</FieldLabel>
            <div className="overflow-x-auto">
              <div
                className="grid gap-[2px]"
                style={{ gridTemplateColumns: `18px repeat(${COLS.length}, 1fr)` }}
              >
                <div />
                {COLS.map((c) => (
                  <div
                    key={c}
                    className="text-[9px] text-ink-subtle text-center py-0.5 font-mono"
                  >
                    {c}
                  </div>
                ))}
                {ROWS.map((row, ri) => (
                  <React.Fragment key={row}>
                    <div className="text-[9px] text-ink-subtle flex items-center justify-center font-mono">
                      {row}
                    </div>
                    {COLS.map((col) => {
                      const isSelected =
                        ri === selectedRow && col === selectedCol;
                      return (
                        <button
                          key={`${row}${col}`}
                          onClick={() => {
                            setSelectedRow(ri);
                            setSelectedCol(col);
                            setFov(1);
                          }}
                          className={cn(
                            "aspect-square rounded-[2px] transition-colors",
                            isSelected
                              ? "bg-brand"
                              : "bg-bg-sunk hover:bg-brand-soft"
                          )}
                        />
                      );
                    })}
                  </React.Fragment>
                ))}
              </div>
            </div>
            <div className="mt-2.5 text-center font-mono text-[12px] text-brand font-medium">
              {currentWell}
            </div>
          </div>

          {/* Channels */}
          <div className="px-4 py-4 border-b border-line">
            <FieldLabel>channels</FieldLabel>
            <div className="space-y-1">
              {CHANNELS.map((ch) => {
                const isOn = activeChannels.includes(ch.id);
                return (
                  <label
                    key={ch.id}
                    className="flex items-center gap-2.5 cursor-pointer group py-1"
                  >
                    <input
                      type="checkbox"
                      checked={isOn}
                      onChange={() => toggleChannel(ch.id)}
                      className="sr-only"
                    />
                    <span
                      className={cn(
                        "w-4 h-4 rounded-[2px] border flex items-center justify-center transition-colors shrink-0",
                        isOn
                          ? "border-current"
                          : "border-line-strong group-hover:border-ink-muted"
                      )}
                      style={{
                        color: isOn ? ch.color : undefined,
                        backgroundColor: isOn ? `${ch.color}20` : undefined,
                      }}
                    >
                      {isOn && (
                        <svg width="9" height="7" viewBox="0 0 10 8" fill="none">
                          <path
                            d="M1 4L3.5 6.5L9 1"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </span>
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: ch.color }}
                    />
                    <span className="font-mono text-[11.5px] uppercase tracking-[0.04em] text-ink">
                      {ch.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* FOV selector */}
          <div className="px-4 py-4 border-b border-line">
            <FieldLabel>field of view</FieldLabel>
            <div className="grid grid-cols-3 gap-1.5">
              {Array.from({ length: TOTAL_FOV }, (_, i) => i + 1).map((f) => {
                const isOn = f === fov;
                return (
                  <button
                    key={f}
                    onClick={() => setFov(f)}
                    className={cn(
                      "aspect-square rounded-[3px] font-mono text-[12px] font-medium transition-colors flex items-center justify-center",
                      isOn
                        ? "bg-brand text-white"
                        : "bg-bg-sunk text-ink-muted hover:bg-brand-soft hover:text-brand"
                    )}
                    style={
                      isOn
                        ? { boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }
                        : undefined
                    }
                  >
                    {f}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Time point */}
          <div className="px-4 py-4">
            <FieldLabel>time point</FieldLabel>
            <input
              type="range"
              min={0}
              max={24}
              defaultValue={0}
              className="w-full accent-brand"
            />
            <div className="flex justify-between font-mono text-[10px] uppercase tracking-[0.04em] text-ink-subtle mt-1">
              <span>0h</span>
              <span>12h</span>
              <span>24h</span>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0">
          <MicroscopyViewer
            seed={seed}
            wellLabel={currentWell}
            plateName={plate?.name || ""}
            fov={fov}
            totalFov={TOTAL_FOV}
            onPrevFov={handlePrevFov}
            onNextFov={handleNextFov}
          />

          <ThumbnailStrip
            plateIndex={plateIndex}
            row={selectedRow}
            col={selectedCol}
            activeFov={fov}
            totalFov={TOTAL_FOV}
            activeChannels={activeChannels}
            onSelectFov={setFov}
          />
        </div>

        {/* Right metadata panel */}
        {metadataOpen && (
          <aside className="w-72 shrink-0 bg-bg border-l border-line overflow-y-auto">
            <div className="px-4 py-4 border-b border-line">
              <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-1">
                metadata
              </div>
              <h2 className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
                Image metadata
              </h2>
            </div>

            <div className="p-4 space-y-5">
              <MetaSection
                title="acquisition"
                rows={[
                  ["objective", "20x / 0.75 NA"],
                  ["exposure", "200 ms"],
                  ["gain", "1.0"],
                  ["binning", "1×1"],
                  ["light source", "LED"],
                  ["camera", "sCMOS 4.2"],
                ]}
              />
              <div className="h-px bg-line" />
              <MetaSection
                title="dimensions"
                rows={[
                  ["width", "512 px"],
                  ["height", "512 px"],
                  ["pixel size", "0.65 µm"],
                  ["physical", "332.8 × 332.8 µm"],
                  ["bit depth", "16-bit"],
                ]}
              />
              <div className="h-px bg-line" />
              <MetaSection
                title="file"
                rows={[
                  ["format", "TIFF"],
                  ["size", "512 KB"],
                  ["channels", String(activeChannels.length)],
                  [
                    "path",
                    `/data/plates/${plate?.id}/${currentWell}/fov${fov}.tif`,
                  ],
                ]}
              />
              <div className="h-px bg-line" />
              <div>
                <div className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-2">
                  timestamp
                </div>
                <p className="font-mono text-[12px] text-ink">
                  {new Date().toISOString().replace("T", " ").split(".")[0]}
                </p>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

function MetaSection({
  title,
  rows,
}: {
  title: string;
  rows: Array<[string, string]>;
}) {
  return (
    <section>
      <h3 className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-2">
        {title}
      </h3>
      <dl className="space-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3">
            <dt className="font-mono text-[11px] uppercase tracking-[0.04em] text-ink-subtle">
              {k}
            </dt>
            <dd className="font-mono text-[12px] text-ink text-right max-w-[160px] truncate">
              {v}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

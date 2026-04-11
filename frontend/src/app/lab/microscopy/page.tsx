"use client";

import React, { useState, useCallback } from "react";
import { Eye, Grid3X3 } from "lucide-react";
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

const TOTAL_FOV = 9;

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
  const handleNextFov = useCallback(() => setFov((f) => Math.min(TOTAL_FOV, f + 1)), []);

  const toggleChannel = (ch: Channel) => {
    setActiveChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  return (
    <div className="flex h-full bg-cream">
      {/* Left filter panel */}
      <aside className="w-64 shrink-0 bg-surface border-r border-border flex flex-col overflow-y-auto">
        <div className="px-4 py-4 border-b border-border">
          <div className="flex items-center gap-2 mb-1">
            <Eye size={18} className="text-amber" />
            <h1 className="text-sm font-semibold text-charcoal">Microscopy Browser</h1>
          </div>
          <p className="text-xs text-muted">Browse FOV images by plate and well</p>
        </div>

        {/* Plate selector */}
        <div className="px-4 py-3 border-b border-border">
          <label className="block text-xs font-medium text-muted mb-1.5">Plate</label>
          <select
            value={plateIndex}
            onChange={(e) => {
              setPlateIndex(Number(e.target.value));
              setFov(1);
            }}
            className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
          >
            {DEMO_PLATES.map((p, i) => (
              <option key={p.id} value={i}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Well selector grid */}
        <div className="px-4 py-3 border-b border-border">
          <label className="block text-xs font-medium text-muted mb-2">Well</label>
          <div className="overflow-x-auto">
            <div className="grid gap-[2px]" style={{ gridTemplateColumns: `20px repeat(${COLS.length}, 1fr)` }}>
              {/* Column headers */}
              <div />
              {COLS.map((c) => (
                <div key={c} className="text-[9px] text-muted text-center py-0.5 font-mono">
                  {c}
                </div>
              ))}
              {/* Rows */}
              {ROWS.map((row, ri) => (
                <React.Fragment key={row}>
                  <div className="text-[9px] text-muted flex items-center justify-center font-mono">
                    {row}
                  </div>
                  {COLS.map((col) => {
                    const isSelected = ri === selectedRow && col === selectedCol;
                    return (
                      <button
                        key={`${row}${col}`}
                        onClick={() => {
                          setSelectedRow(ri);
                          setSelectedCol(col);
                          setFov(1);
                        }}
                        className={`aspect-square rounded-[3px] transition-all text-[7px] font-mono ${
                          isSelected
                            ? "bg-amber text-charcoal ring-1 ring-amber-dark scale-110 font-bold"
                            : "bg-cream-dark hover:bg-amber/20 text-muted hover:text-charcoal"
                        }`}
                      />
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
          <div className="mt-2 text-xs text-center font-mono text-charcoal font-medium">
            {currentWell}
          </div>
        </div>

        {/* Channel selector */}
        <div className="px-4 py-3 border-b border-border">
          <label className="block text-xs font-medium text-muted mb-2">Channels</label>
          <div className="space-y-1.5">
            {CHANNELS.map((ch) => (
              <label
                key={ch.id}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={activeChannels.includes(ch.id)}
                  onChange={() => toggleChannel(ch.id)}
                  className="sr-only"
                />
                <span
                  className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                    activeChannels.includes(ch.id)
                      ? "border-current"
                      : "border-border group-hover:border-muted"
                  }`}
                  style={{
                    color: activeChannels.includes(ch.id) ? ch.color : undefined,
                    backgroundColor: activeChannels.includes(ch.id) ? `${ch.color}20` : undefined,
                  }}
                >
                  {activeChannels.includes(ch.id) && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </span>
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: ch.color }}
                />
                <span className="text-xs text-charcoal">{ch.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* FOV selector */}
        <div className="px-4 py-3 border-b border-border">
          <label className="block text-xs font-medium text-muted mb-2">
            Field of View
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {Array.from({ length: TOTAL_FOV }, (_, i) => i + 1).map((f) => (
              <button
                key={f}
                onClick={() => setFov(f)}
                className={`aspect-square rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center ${
                  f === fov
                    ? "bg-amber text-charcoal shadow-sm"
                    : "bg-cream-dark text-muted hover:bg-amber/20 hover:text-charcoal"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Time point (decorative) */}
        <div className="px-4 py-3">
          <label className="block text-xs font-medium text-muted mb-2">
            Time Point
          </label>
          <input
            type="range"
            min={0}
            max={24}
            defaultValue={0}
            className="w-full accent-amber"
          />
          <div className="flex justify-between text-[10px] text-muted mt-1">
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

      {/* Right metadata panel (collapsible) */}
      <button
        onClick={() => setMetadataOpen(!metadataOpen)}
        className={`absolute right-0 top-1/2 -translate-y-1/2 z-30 p-1.5 bg-surface border border-border rounded-l-lg shadow-sm text-muted hover:text-charcoal transition-colors ${
          metadataOpen ? "right-72" : "right-0"
        }`}
        style={{ right: metadataOpen ? "18rem" : 0 }}
      >
        <Grid3X3 size={14} />
      </button>

      {metadataOpen && (
        <aside className="w-72 shrink-0 bg-surface border-l border-border overflow-y-auto">
          <div className="px-4 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-charcoal">Image Metadata</h2>
          </div>

          <div className="p-4 space-y-4 text-xs">
            <section>
              <h3 className="text-muted font-medium uppercase tracking-wider text-[10px] mb-2">
                Acquisition
              </h3>
              <dl className="space-y-1.5">
                {[
                  ["Objective", "20x / 0.75 NA"],
                  ["Exposure", "200 ms"],
                  ["Gain", "1.0"],
                  ["Binning", "1x1"],
                  ["Light Source", "LED"],
                  ["Camera", "sCMOS 4.2"],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-muted">{k}</dt>
                    <dd className="text-charcoal font-medium font-mono">{v}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <div className="h-px bg-border" />

            <section>
              <h3 className="text-muted font-medium uppercase tracking-wider text-[10px] mb-2">
                Dimensions
              </h3>
              <dl className="space-y-1.5">
                {[
                  ["Width", "512 px"],
                  ["Height", "512 px"],
                  ["Pixel Size", "0.65 um"],
                  ["Physical", "332.8 x 332.8 um"],
                  ["Bit Depth", "16-bit"],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-muted">{k}</dt>
                    <dd className="text-charcoal font-medium font-mono">{v}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <div className="h-px bg-border" />

            <section>
              <h3 className="text-muted font-medium uppercase tracking-wider text-[10px] mb-2">
                File Info
              </h3>
              <dl className="space-y-1.5">
                {[
                  ["Format", "TIFF"],
                  ["Size", "512 KB"],
                  ["Channels", activeChannels.length.toString()],
                  ["Path", `/data/plates/${plate?.id}/${currentWell}/fov${fov}.tif`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-muted">{k}</dt>
                    <dd className="text-charcoal font-medium font-mono text-right max-w-[140px] truncate">
                      {v}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>

            <div className="h-px bg-border" />

            <section>
              <h3 className="text-muted font-medium uppercase tracking-wider text-[10px] mb-2">
                Timestamp
              </h3>
              <p className="text-charcoal font-mono">
                {new Date().toISOString().replace("T", " ").split(".")[0]}
              </p>
            </section>
          </div>
        </aside>
      )}
    </div>
  );
}

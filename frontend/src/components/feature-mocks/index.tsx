"use client";

/* ── Feature page mocks ──
 * Marketing-only static demonstrations of each module,
 * styled to match the v4 mockup (claude-design-mockup.html).
 * They render real UI — not screenshots — so they restyle when tokens change.
 */

import { Fragment } from "react";
import {
  Cherry,
  FlaskConical,
  Copy,
  Shuffle,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Info,
  Mic,
  MessageSquare,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Check,
  Search,
  Download,
  Printer,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ──────────────────────────────────────────────────────────
   Shared bits
   ────────────────────────────────────────────────────────── */

function MockFrame({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-md border border-line bg-surface overflow-hidden"
      style={{
        boxShadow:
          "0 1px 2px rgba(20,16,10,.04), 0 12px 28px -16px rgba(20,16,10,.10)",
      }}
    >
      {children}
    </div>
  );
}

function FrameHeader({
  marker,
  title,
  meta,
  right,
}: {
  marker?: string;
  title: React.ReactNode;
  meta?: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-end justify-between px-5 py-4 border-b border-line bg-bg gap-4">
      <div className="min-w-0">
        {marker && (
          <div className="inline-flex items-center gap-2 mb-1.5 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
            <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
              {marker}
            </span>
          </div>
        )}
        <div className="text-[16px] font-semibold tracking-[-0.015em] text-ink">
          {title}
        </div>
        {meta && (
          <div className="mt-1 font-mono text-[11px] tracking-[0.04em] uppercase text-ink-muted">
            {meta}
          </div>
        )}
      </div>
      {right && <div className="flex items-center gap-2 shrink-0">{right}</div>}
    </div>
  );
}

/* ──────────────────────────────────────────────────────────
   PLATE MAPPER
   ────────────────────────────────────────────────────────── */

const plateRows = ["A", "B", "C", "D", "E", "F", "G", "H"];

function fillForCell(r: number, c: number) {
  if (c === 1 && (r === 1 || r === 2)) return "bf";
  if (c === 1 && (r === 7 || r === 8)) return "mch";
  if (r >= 1 && r <= 2 && c >= 2 && c <= 9) return "dapi";
  if (r >= 3 && r <= 6 && c >= 2 && c <= 9) return "gfp";
  return "empty";
}

const wellTone: Record<string, { ring: string; fill: string; soft: string }> = {
  empty: { ring: "var(--color-line)", fill: "transparent", soft: "var(--color-surface)" },
  dapi: { ring: "rgba(31,108,160,0.4)", fill: "var(--color-dapi)", soft: "var(--color-dapi-soft)" },
  gfp: { ring: "rgba(130,184,47,0.4)", fill: "var(--color-gfp)", soft: "var(--color-gfp-soft)" },
  mch: { ring: "rgba(195,42,85,0.4)", fill: "var(--color-mch)", soft: "var(--color-mch-soft)" },
  bf: { ring: "rgba(166,113,27,0.4)", fill: "var(--color-bf)", soft: "var(--color-bf-soft)" },
};

function MiniPlate() {
  return (
    <div className="bg-bg border border-line rounded-[5px] p-4">
      <div
        className="grid gap-1.5"
        style={{
          gridTemplateColumns: "20px repeat(12, minmax(0, 1fr))",
          gridTemplateRows: "20px repeat(8, minmax(0, 1fr))",
        }}
      >
        <div />
        {Array.from({ length: 12 }, (_, i) => (
          <div
            key={`c${i}`}
            className="font-mono text-[10px] text-ink-subtle text-center"
          >
            {i + 1}
          </div>
        ))}
        {plateRows.map((rl, ri) => (
          <Fragment key={rl}>
            <div className="font-mono text-[10px] text-ink-subtle text-center self-center">
              {rl}
            </div>
            {Array.from({ length: 12 }, (_, ci) => {
              const tone = fillForCell(ri + 1, ci + 1);
              const t = wellTone[tone];
              return (
                <div
                  key={`${rl}${ci}`}
                  className="aspect-square rounded-full"
                  style={{
                    background: t.soft,
                    border: `1px solid ${t.ring}`,
                    position: "relative",
                  }}
                >
                  {tone !== "empty" && (
                    <div
                      className="absolute rounded-full"
                      style={{
                        inset: "22%",
                        background: t.fill,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle">
        <span>SOURCE · COMPOUND-LIBRARY-A</span>
        <span>96 · 8×12</span>
      </div>
    </div>
  );
}

const plateModes = [
  { code: "MD/01", label: "Cherry pick", icon: Cherry, active: true },
  { code: "MD/02", label: "Serial dilution", icon: FlaskConical },
  { code: "MD/03", label: "Replicate", icon: Copy },
  { code: "MD/04", label: "Randomize", icon: Shuffle },
];

export function PlateMapperMock() {
  return (
    <MockFrame>
      <FrameHeader
        marker="PLT/01"
        title="Plate Map Designer"
        meta={
          <>
            PM-2026-0428 ·{" "}
            <em className="not-italic text-brand">kinase-inhibitor-DR</em> ·
            96-well · draft
          </>
        }
        right={
          <div className="inline-flex p-0.5 border border-line bg-bg rounded-[3px]">
            {["96", "384", "1536"].map((s) => {
              const isOn = s === "384";
              return (
                <span
                  key={s}
                  className={cn(
                    "px-2.5 py-1 font-mono text-[11px] tracking-[0.02em] rounded-[2px]",
                    isOn
                      ? "bg-surface text-brand"
                      : "text-ink-muted"
                  )}
                  style={
                    isOn
                      ? { boxShadow: "0 0 0 1px var(--color-brand-soft)" }
                      : undefined
                  }
                >
                  {s}
                </span>
              );
            })}
          </div>
        }
      />
      <div className="grid grid-cols-[180px_1fr_220px]">
        {/* Modes */}
        <aside className="p-4 border-r border-line bg-bg">
          <div className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-2">
            Mode
          </div>
          <div className="space-y-0.5">
            {plateModes.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.code}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 rounded-[3px] text-[12.5px]",
                    m.active
                      ? "bg-surface text-brand"
                      : "text-ink-muted"
                  )}
                  style={
                    m.active
                      ? {
                          boxShadow:
                            "inset 2px 0 0 0 var(--color-brand), inset 0 0 0 1px var(--color-line)",
                        }
                      : undefined
                  }
                >
                  <Icon size={12} />
                  <span className="flex-1 truncate">{m.label}</span>
                </div>
              );
            })}
          </div>
          <div className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mt-5 mb-2">
            Parameters
          </div>
          <div className="space-y-2">
            {[
              ["volume · nL", "100"],
              ["replicates", "3"],
            ].map(([k, v]) => (
              <div key={k}>
                <div className="font-mono text-[10px] uppercase tracking-[0.04em] text-ink-subtle mb-1">
                  {k}
                </div>
                <div className="bg-surface border border-line rounded-[3px] px-2.5 py-1 font-mono text-[12px] text-ink">
                  {v}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Plate */}
        <main className="p-5">
          <MiniPlate />
          <div className="mt-3 flex flex-wrap gap-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted">
            <Legend tone="empty" label="empty" />
            <Legend tone="dapi" label="sample · DAPI" />
            <Legend tone="gfp" label="compound · GFP" />
            <Legend tone="mch" label="control − · mCh" />
            <Legend tone="bf" label="control + · BF" />
          </div>
        </main>

        {/* Summary */}
        <aside className="p-4 border-l border-line bg-bg">
          <div className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-2">
            Selection
          </div>
          <div className="bg-surface border border-line rounded-[4px]">
            {[
              ["mode", "cherry-pick"],
              ["wells", "63"],
              ["vol/well", "100 nL"],
              ["total", "6.3 µL"],
              ["source", "lib-A"],
              ["dest", "dest-1"],
              ["est. time", "00:04:18"],
            ].map(([k, v], i) => (
              <div
                key={k}
                className={cn(
                  "flex justify-between gap-2 px-3 py-2 font-mono text-[11.5px]",
                  i < 6 && "border-b border-line"
                )}
              >
                <span className="font-mono text-[10px] uppercase tracking-[0.04em] text-ink-subtle self-center">
                  {k}
                </span>
                <span className="text-ink font-medium">{v}</span>
              </div>
            ))}
          </div>
          <div className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mt-4 mb-2">
            Worklist target
          </div>
          <div className="flex flex-wrap gap-1.5">
            {["echo-550", "hamilton-STAR", "opentrons-OT-2"].map((t, i) => (
              <span
                key={t}
                className={cn(
                  "font-mono text-[10px] uppercase tracking-[0.02em] px-1.5 py-0.5 rounded-[2px] border",
                  i === 0
                    ? "bg-brand-soft text-brand border-brand/30"
                    : "bg-surface text-ink-muted border-line"
                )}
              >
                {t}
              </span>
            ))}
          </div>
          <div className="mt-4 inline-flex items-center justify-center gap-2 w-full px-3 py-2 bg-brand text-white font-mono text-[11px] uppercase tracking-[0.04em] rounded-[3px]">
            generate worklist →
          </div>
        </aside>
      </div>
    </MockFrame>
  );
}

function Legend({
  tone,
  label,
}: {
  tone: keyof typeof wellTone;
  label: string;
}) {
  const t = wellTone[tone];
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="inline-block w-2 h-2 rounded-full"
        style={{
          background: tone === "empty" ? "var(--color-bg)" : t.fill,
          border: `1px solid ${t.ring}`,
        }}
      />
      {label}
    </span>
  );
}

/* ──────────────────────────────────────────────────────────
   INVENTORY
   ────────────────────────────────────────────────────────── */

const inventoryRows = [
  {
    name: "DMEM + 10% FBS",
    sub: "cell-culture · 500 mL · 90% rem",
    barcode: "RES-2024-1007",
    type: "media",
    typeT: "dapi",
    loc: "fridge-1 / shelf-3",
    temp: "4°C",
    lot: "MD-2024-7712",
    expiry: "2026-05-06",
    expT: "bf",
  },
  {
    name: "RPMI 1640",
    sub: "cell-culture · 500 mL · 35% rem",
    barcode: "RES-2024-1008",
    type: "media",
    typeT: "dapi",
    loc: "fridge-1 / shelf-3",
    temp: "4°C",
    lot: "MD-2024-7720",
    expiry: "2026-06-10",
    expT: "default",
  },
  {
    name: "Puromycin (10 mg/mL)",
    sub: "selection · 1 mL aliquots",
    barcode: "RES-2024-1020",
    type: "reagent",
    typeT: "gfp",
    loc: "freezer-B / shelf-2 / box-4",
    temp: "−20°C",
    lot: "RG-2024-8860",
    expiry: "2026-12-17",
    expT: "mch",
  },
  {
    name: "Staurosporine",
    sub: "compound · positive control",
    barcode: "RES-2024-2201",
    type: "compound",
    typeT: "gfp",
    loc: "freezer-A / shelf-1",
    temp: "−80°C",
    lot: "CP-2024-1180",
    expiry: "2027-08-01",
    expT: "default",
  },
];

const chipMap: Record<string, string> = {
  dapi: "bg-dapi-soft border-dapi/30 text-dapi",
  gfp: "bg-gfp-soft border-gfp/40 text-[#4D7600]",
  mch: "bg-mch-soft border-mch/30 text-mch",
  bf: "bg-bf-soft border-bf/30 text-bf",
  brand: "bg-brand-soft border-brand/30 text-brand",
  default: "bg-bg border-line text-ink-muted",
};

function Chip({
  tone,
  children,
}: {
  tone: keyof typeof chipMap;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[10px] tracking-[0.02em] uppercase rounded-[2px] border",
        chipMap[tone]
      )}
    >
      {children}
    </span>
  );
}

export function InventoryMock() {
  return (
    <MockFrame>
      <FrameHeader
        marker="INV/04"
        title="Inventory"
        meta={
          <>
            22 samples ·{" "}
            <em className="not-italic" style={{ color: "var(--color-bf)" }}>
              3 expiring in 30d
            </em>{" "}
            · sync 02:14 ago
          </>
        }
      />

      {/* KPI strip */}
      <div className="grid grid-cols-4 border-b border-line bg-surface">
        {[
          { k: "total", v: "22", d: "all samples", tone: "ink" },
          { k: "expiring < 30d", v: "03", d: "puromycin · DMEM · RPMI", tone: "bf" },
          { k: "low stock", v: "03", d: "2 reorders queued", tone: "mch" },
          { k: "added this wk", v: "01", d: "tris-HCl buffer", tone: "brand" },
        ].map((kpi, i) => (
          <div
            key={kpi.k}
            className={cn("px-5 py-4", i < 3 && "border-r border-line")}
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle">
              {kpi.k}
            </div>
            <div
              className="mt-1.5 font-semibold text-[28px] tracking-[-0.04em] tabular-nums leading-none"
              style={{
                color:
                  kpi.tone === "bf"
                    ? "var(--color-bf)"
                    : kpi.tone === "mch"
                    ? "var(--color-mch)"
                    : kpi.tone === "brand"
                    ? "var(--color-brand)"
                    : "var(--color-ink)",
              }}
            >
              {kpi.v}
            </div>
            <div className="mt-1 font-mono text-[10.5px] tracking-[0.02em] text-ink-muted truncate">
              {kpi.d}
            </div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-line bg-bg">
        <span className="bg-surface border border-line rounded-[3px] px-2.5 py-1 font-mono text-[11px] text-ink-subtle inline-flex items-center gap-1.5 min-w-[220px]">
          <Search size={12} />
          search by name, barcode, lot…
        </span>
        <span className="font-mono text-[11px] text-ink-muted bg-surface border border-line rounded-[3px] px-2 py-1">
          type · all ▾
        </span>
        <span className="font-mono text-[11px] text-ink-muted bg-surface border border-line rounded-[3px] px-2 py-1">
          status · all ▾
        </span>
        <div className="flex-1" />
        <span className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted">
          <Download size={12} /> export
        </span>
        <span className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted">
          <Printer size={12} /> print
        </span>
      </div>

      {/* Table */}
      <div className="overflow-hidden">
        <table className="w-full">
          <thead className="bg-bg">
            <tr>
              {["name", "barcode", "type", "location", "temp", "lot", "expiry"].map(
                (h, i) => (
                  <th
                    key={h}
                    className={cn(
                      "text-left px-3 py-2 border-b border-line font-mono text-[10px] font-medium uppercase tracking-[0.06em] text-ink-subtle",
                      ["barcode", "type"].includes(h) && "w-[16%]"
                    )}
                  >
                    {h}
                    {i < 4 && (
                      <ChevronsUpDown
                        size={10}
                        className="inline-block ml-1 opacity-40"
                      />
                    )}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {inventoryRows.map((row, i) => (
              <tr
                key={row.barcode}
                className={cn(i < inventoryRows.length - 1 && "border-b border-line")}
              >
                <td className="px-3 py-2.5">
                  <div className="text-[13px] font-medium text-ink">{row.name}</div>
                  <div className="font-mono text-[10.5px] tracking-[0.02em] text-ink-subtle mt-0.5">
                    {row.sub}
                  </div>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11.5px] text-ink-muted">
                  {row.barcode}
                </td>
                <td className="px-3 py-2.5">
                  <Chip tone={row.typeT as keyof typeof chipMap}>{row.type}</Chip>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11.5px] text-ink-muted">
                  {row.loc}
                </td>
                <td className="px-3 py-2.5 font-mono text-[11.5px] text-ink-muted">
                  {row.temp}
                </td>
                <td className="px-3 py-2.5 font-mono text-[11.5px] text-ink-muted">
                  {row.lot}
                </td>
                <td className="px-3 py-2.5">
                  {row.expT === "default" ? (
                    <span className="font-mono text-[11.5px] text-ink">
                      {row.expiry}
                    </span>
                  ) : (
                    <Chip tone={row.expT as keyof typeof chipMap}>{row.expiry}</Chip>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-2 border-t border-line bg-bg flex items-center justify-between font-mono text-[11px] tracking-[0.02em] text-ink-subtle">
        <span>showing 4 / 22 samples</span>
        <span>
          0 selected · <span className="text-brand">bulk actions →</span>
        </span>
      </div>
    </MockFrame>
  );
}

/* ──────────────────────────────────────────────────────────
   MICROSCOPY
   ────────────────────────────────────────────────────────── */

const channels = [
  { id: "dapi", label: "DAPI", color: "#6FD8FF" },
  { id: "gfp", label: "GFP", color: "#5BC07F" },
  { id: "mcherry", label: "mCherry", color: "#FF5C7A" },
  { id: "bf", label: "BF", color: "#FFC857" },
];

export function MicroscopyMock() {
  return (
    <MockFrame>
      <FrameHeader
        marker="MIC/02"
        title="Microscopy Browser"
        meta={
          <>
            Plate A · row B ·{" "}
            <em className="not-italic text-brand">FOV 4 / 6</em> · 2 channels
          </>
        }
      />
      {/* Channel bar */}
      <div className="flex items-center gap-1 px-4 py-2 bg-bg border-b border-line">
        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-[3px] font-mono text-[10.5px] uppercase tracking-[0.04em] bg-brand-soft text-brand border border-brand/30">
          <Layers size={11} /> composite
        </span>
        <div className="w-px h-4 bg-line mx-1" />
        {channels.map((ch, i) => {
          const on = i < 2;
          return (
            <span
              key={ch.id}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-[3px] font-mono text-[10.5px] uppercase tracking-[0.04em]"
              style={{
                color: on ? ch.color : "var(--color-ink-subtle)",
                backgroundColor: on ? `${ch.color}1F` : "transparent",
                boxShadow: on
                  ? `inset 0 0 0 1px ${ch.color}`
                  : "inset 0 0 0 1px var(--color-line)",
                opacity: on ? 1 : 0.6,
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: ch.color }}
              />
              {ch.label}
            </span>
          );
        })}
        <div className="flex-1" />
        <span className="inline-flex items-center gap-0.5 text-ink-muted">
          <ZoomOut size={13} className="p-1 box-content rounded-[3px]" />
          <span className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle w-10 text-center">
            100%
          </span>
          <ZoomIn size={13} className="p-1 box-content rounded-[3px]" />
          <Maximize2 size={13} className="p-1 box-content rounded-[3px] ml-1" />
          <Info size={13} className="p-1 box-content rounded-[3px] ml-1" />
        </span>
      </div>

      {/* Image viewport */}
      <div
        className="relative overflow-hidden"
        style={{
          background:
            "radial-gradient(circle at 30% 35%, #102634 0%, #050a0e 60%, #000 100%)",
          height: 360,
        }}
      >
        {/* simulated fluorescent dots */}
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 600 360"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <defs>
            <radialGradient id="dapi-glow">
              <stop offset="0%" stopColor="#6FD8FF" stopOpacity="0.85" />
              <stop offset="60%" stopColor="#6FD8FF" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#6FD8FF" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="gfp-glow">
              <stop offset="0%" stopColor="#5BC07F" stopOpacity="0.9" />
              <stop offset="60%" stopColor="#5BC07F" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#5BC07F" stopOpacity="0" />
            </radialGradient>
          </defs>
          {/* DAPI dots */}
          {[
            [80, 120, 18],
            [150, 200, 14],
            [220, 80, 16],
            [300, 240, 22],
            [400, 120, 20],
            [470, 230, 17],
            [540, 80, 14],
            [380, 290, 18],
            [120, 290, 16],
            [240, 160, 12],
          ].map(([x, y, r], i) => (
            <circle
              key={`d${i}`}
              cx={x}
              cy={y}
              r={r}
              fill="url(#dapi-glow)"
            />
          ))}
          {/* GFP dots */}
          {[
            [180, 140, 14],
            [260, 210, 18],
            [340, 90, 16],
            [430, 200, 20],
            [490, 290, 14],
            [110, 220, 18],
            [350, 290, 12],
            [560, 180, 16],
          ].map(([x, y, r], i) => (
            <circle
              key={`g${i}`}
              cx={x}
              cy={y}
              r={r}
              fill="url(#gfp-glow)"
            />
          ))}
        </svg>

        {/* Scale bar */}
        <div className="absolute bottom-3 left-4">
          <div className="w-20 h-0.5 bg-white" />
          <div className="font-mono text-[9.5px] uppercase tracking-[0.04em] text-white/70 mt-1">
            100 µm
          </div>
        </div>
        {/* Well badge */}
        <div className="absolute top-3 right-4 bg-black/55 backdrop-blur-sm rounded-[3px] px-2 py-1 font-mono text-[10.5px] tracking-[0.04em] text-white/90 uppercase">
          B4 · FOV 4
        </div>
      </div>

      {/* Thumbnail strip */}
      <div className="bg-ink py-3 px-4 flex gap-2 overflow-hidden">
        {[1, 2, 3, 4, 5, 6].map((f) => {
          const active = f === 4;
          return (
            <div
              key={f}
              className={cn(
                "shrink-0 rounded-[3px] overflow-hidden relative",
                active
                  ? "ring-2 ring-brand ring-offset-2 ring-offset-ink"
                  : "ring-1 ring-white/10 opacity-60"
              )}
              style={{
                width: 56,
                height: 56,
                background:
                  "radial-gradient(circle at 50% 50%, #102634, #050a0e)",
              }}
            >
              <div className="absolute bottom-0 inset-x-0 bg-black/55 font-mono text-[9px] tracking-[0.04em] text-white/80 uppercase text-center py-0.5">
                FOV {f}
              </div>
            </div>
          );
        })}
      </div>
    </MockFrame>
  );
}

/* ──────────────────────────────────────────────────────────
   DATA PROCESSING — 4PL curve
   ────────────────────────────────────────────────────────── */

export function ProcessingMock() {
  return (
    <MockFrame>
      <FrameHeader
        marker="DAT/03"
        title="Dose-Response Fit"
        meta={
          <>
            CH-1 · 4PL · <em className="not-italic text-brand">staurosporine</em>{" "}
            · n = 9
          </>
        }
        right={
          <span className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.06em] text-brand">
            <span className="inline-block w-[7px] h-[7px] rounded-full bg-brand pulse-led" />
            live
          </span>
        }
      />
      <div className="p-5">
        <div className="bg-bg border border-line rounded-[5px] p-4 relative">
          <svg viewBox="0 0 600 320" className="w-full" aria-hidden="true">
            {/* grid */}
            <g stroke="#CFD3C6" strokeWidth="0.6">
              {[60, 120, 180, 240].map((y) => (
                <line key={y} x1="0" y1={y} x2="600" y2={y} />
              ))}
              {[120, 240, 360, 480].map((x) => (
                <line key={x} x1={x} y1="0" x2={x} y2="320" />
              ))}
            </g>
            {/* axis labels */}
            <g
              fontFamily="JetBrains Mono"
              fontSize="9"
              fill="#828776"
              letterSpacing="0.5"
            >
              <text x="2" y="58">
                100%
              </text>
              <text x="2" y="178">
                50%
              </text>
              <text x="2" y="258">
                0%
              </text>
              <text x="116" y="310">
                −9
              </text>
              <text x="236" y="310">
                −8
              </text>
              <text x="356" y="310">
                −7
              </text>
              <text x="476" y="310">
                −6
              </text>
              <text x="556" y="310">
                log[M]
              </text>
            </g>
            {/* replicate dots */}
            <g fill="#1F4D3A" opacity="0.35">
              {[
                [60, 84],
                [120, 92],
                [180, 106],
                [240, 132],
                [300, 178],
                [360, 218],
                [420, 244],
                [480, 254],
                [540, 258],
              ].map(([x, y]) => (
                <circle key={`r-${x}`} cx={x} cy={y} r="3" />
              ))}
            </g>
            {/* main scatter */}
            <g fill="#1F4D3A">
              {[
                [60, 78],
                [120, 86],
                [180, 98],
                [240, 124],
                [300, 170],
                [360, 210],
                [420, 238],
                [480, 250],
                [540, 254],
              ].map(([x, y]) => (
                <circle key={`m-${x}`} cx={x} cy={y} r="3.5" />
              ))}
            </g>
            {/* curve */}
            <path
              d="M 0,80 C 80,80 140,84 200,108 C 260,140 300,178 360,212 C 420,238 480,250 600,254"
              fill="none"
              stroke="#1F4D3A"
              strokeWidth="2.4"
            />
            {/* IC50 crosshair */}
            <g>
              <line
                x1="300"
                y1="0"
                x2="300"
                y2="320"
                stroke="#1F6CA0"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
              <line
                x1="0"
                y1="170"
                x2="600"
                y2="170"
                stroke="#1F6CA0"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
              <circle
                cx="300"
                cy="170"
                r="5"
                fill="#FFFFFF"
                stroke="#1F6CA0"
                strokeWidth="2"
              />
              <text
                x="308"
                y="166"
                fontFamily="JetBrains Mono"
                fontSize="9"
                fill="#1F6CA0"
              >
                IC₅₀
              </text>
            </g>
          </svg>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            ["IC₅₀", "42.3", "nM", true],
            ["Hill slope", "−1.18", "", false],
            ["Z′", "0.71", "", false],
          ].map(([k, v, suf, hi]) => (
            <div
              key={k as string}
              className="bg-bg border border-line rounded-[3px] px-3 py-2.5"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle">
                {k}
              </div>
              <div className="mt-1 font-mono text-[18px] text-ink leading-none">
                <span className={hi ? "text-brand font-semibold" : ""}>
                  {v}
                </span>
                {suf && <span className="text-ink-muted ml-1 text-[14px]">{suf}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </MockFrame>
  );
}

/* ──────────────────────────────────────────────────────────
   AGENT
   ────────────────────────────────────────────────────────── */

export function AgentMock() {
  const turns = [
    {
      kind: "voice",
      time: "tue · 14:32",
      text: "Plan a kinase screen — 24 compounds, three replicates.",
    },
    {
      kind: "agent",
      time: "14:32:08",
      text: (
        <>
          Created a plate map. <em className="not-italic text-brand">72 wells</em>{" "}
          on a 96 plate, three replicates per compound, two control wells per row.
        </>
      ),
      chips: ["PLT/01 · cherry-pick", "echo-550 · 100 nL"],
    },
    {
      kind: "chat",
      time: "wed · 09:14",
      text: "How did round 1 go?",
    },
    {
      kind: "agent",
      time: "09:14:11",
      text: (
        <>
          IC₅₀ <em className="not-italic text-brand">42.3 nM</em> · Hill −1.18 ·
          Z′ 0.71. ELN draft is ready for review.
        </>
      ),
      chips: ["DAT/03 · fit done", "ELN-2026-0428"],
    },
  ];

  return (
    <MockFrame>
      <FrameHeader
        marker="AGT/05"
        title="Agent Console"
        meta={
          <>
            Round 1 · kinase screen ·{" "}
            <em className="not-italic text-brand">live</em>
          </>
        }
        right={
          <span className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.06em] text-brand">
            <span className="inline-block w-[7px] h-[7px] rounded-full bg-brand pulse-led" />
            live
          </span>
        }
      />
      <div className="p-5 space-y-4">
        {turns.map((t, i) => {
          const isAgent = t.kind === "agent";
          return (
            <div key={i} className="flex items-start gap-2.5">
              {isAgent ? (
                <span
                  className="inline-grid grid-cols-2 grid-rows-2 gap-[2px] p-[3px] rounded-[4px] bg-surface border border-line-strong shrink-0"
                  style={{ width: 22, height: 22 }}
                >
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-brand" />
                </span>
              ) : (
                <span
                  className={cn(
                    "inline-flex items-center justify-center w-[22px] h-[22px] rounded-[4px] shrink-0",
                    t.kind === "voice"
                      ? "bg-brand-soft border border-brand/30 text-brand"
                      : "bg-bg-sunk border border-line text-ink-muted"
                  )}
                >
                  {t.kind === "voice" ? <Mic size={12} /> : <MessageSquare size={12} />}
                </span>
              )}
              <div className="min-w-0 flex-1">
                <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle mb-0.5">
                  {isAgent
                    ? "agent"
                    : t.kind === "voice"
                    ? "you · voice"
                    : "you · chat"}{" "}
                  · {t.time}
                </div>
                <div
                  className={cn(
                    "text-[13px] leading-[1.5]",
                    isAgent ? "text-ink" : "text-ink-muted"
                  )}
                >
                  {t.text}
                </div>
                {t.chips && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {t.chips.map((c) => (
                      <span
                        key={c}
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] font-mono text-[10px] tracking-[0.02em] uppercase bg-brand-soft border border-brand/30 text-brand"
                      >
                        <span className="inline-block w-[5px] h-[5px] rounded-full bg-brand" />
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="border-t border-line px-5 py-3 flex items-center justify-between font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle bg-bg">
        <span className="inline-flex items-center gap-1.5">
          <Mic size={11} className="text-brand" /> voice ·
          <MessageSquare size={11} className="text-ink-muted ml-0.5" /> chat ·
          <span className="text-ink-muted">⌘ K</span>
        </span>
        <span>30+ tools · cited traces</span>
      </div>
    </MockFrame>
  );
}

/* ──────────────────────────────────────────────────────────
   AUDIT LOG
   ────────────────────────────────────────────────────────── */

export function AuditMock() {
  const entries = [
    { t: "14:32:04", text: <>received <em className="not-italic text-ink font-medium">fit_dose_response</em></>, dot: "brand" },
    { t: "14:32:04", text: <>→ <em className="not-italic text-ink font-medium">get_plate_map_details</em>(plate=A)</>, dot: "brand" },
    { t: "14:32:05", text: <>← 96 wells · DAPI+GFP</>, dot: "brand" },
    { t: "14:32:05", text: <>→ <em className="not-italic text-ink font-medium">browse_microscopy</em>(fovs=6)</>, dot: "dapi" },
    { t: "14:32:08", text: <>← 576 images · 1.4 GB</>, dot: "dapi" },
    { t: "14:32:09", text: <>running 4PL · n=9 · stauro</>, dot: "brand" },
    { t: "14:32:11", text: <>IC₅₀ = <em className="not-italic text-ink font-medium">42.3 nM</em></>, dot: "brand" },
    { t: "14:32:11", text: <>Hill = −1.18 · Z′ = 0.71</>, dot: "brand" },
    { t: "14:32:12", text: <>⚠ row C col 4 outlier · flagged</>, dot: "mch" },
    { t: "14:32:13", text: <>→ <em className="not-italic text-ink font-medium">create_eln_entry</em>(draft)</>, dot: "bf" },
    { t: "14:32:14", text: <>← entry <em className="not-italic text-ink font-medium">ELN-2026-0428</em></>, dot: "brand" },
    { t: "14:32:15", text: <>signed by <em className="not-italic text-ink font-medium">@beatriz</em> · immutable</>, dot: "brand" },
  ];

  const dotMap: Record<string, string> = {
    brand: "bg-brand",
    dapi: "bg-dapi",
    mch: "bg-mch",
    bf: "bg-bf",
  };

  return (
    <MockFrame>
      <FrameHeader
        marker="AUD/06"
        title="Activity Log"
        meta={
          <>
            kinase-screen-q2 ·{" "}
            <em className="not-italic text-brand">12 events</em> · 11s span
          </>
        }
        right={
          <span className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
            <Check size={11} className="text-brand" />
            cited
          </span>
        }
      />
      <div className="p-5 bg-bg">
        <div className="bg-surface border border-line rounded-[5px] p-4">
          <div className="space-y-1.5">
            {entries.map((e, i) => (
              <div
                key={i}
                className="grid items-start gap-2.5 font-mono text-[11px] tracking-[0.01em] text-ink-muted"
                style={{ gridTemplateColumns: "60px 6px 1fr" }}
              >
                <span className="text-ink-subtle">{e.t}</span>
                <span
                  className={cn(
                    "inline-block w-[6px] h-[6px] rounded-full mt-1.5",
                    dotMap[e.dot]
                  )}
                />
                <span>{e.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </MockFrame>
  );
}

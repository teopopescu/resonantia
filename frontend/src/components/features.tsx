"use client";

import { motion } from "framer-motion";

/**
 * Modules — a system manifest, not a marketing card grid.
 * Each entry has a mono call-sign, a status, a specs strip, and a tiny
 * inline telemetry line so the page reads as a spec sheet for the bench.
 */

type Status = "GA" | "BETA" | "PREVIEW";

const modules: Array<{
  code: string;
  title: string;
  desc: string;
  status: Status;
  ver: string;
  specs: string[];
  /** small inline telemetry line under the description */
  telemetry?: string;
}> = [
  {
    code: "PLT/01",
    title: "Run Builder",
    desc:
      "Source-destination layouts with cherry-pick, serial dilution, and replicate modes. Export worklists only after validation and approval.",
    status: "GA",
    ver: "v1.2",
    specs: ["96 / 384", "Echo · Hamilton · OT-2", "5 tools"],
    telemetry: "PM-2026-0428 · 63 transfers · 6.3 µL · 00:04:18",
  },
  {
    code: "DAT/03",
    title: "Results Analysis",
    desc:
      "Ingest plate-reader and qPCR outputs, fit results, flag issues, and attach provenance back to the run record.",
    status: "GA",
    ver: "v1.1",
    specs: ["4PL · ΔΔCt · Z-prime", "Z′ = 0.71", "5 tools"],
    telemetry: "STAUROSPORINE · IC₅₀ 42.3 nM · Hill −1.18",
  },
  {
    code: "INV/04",
    title: "Source Inventory",
    desc:
      "Source plates, lots, aliquots, and dead-volume checks. Barcode lookup, expiry alerts, and stock constraints for executable runs.",
    status: "GA",
    ver: "v1.0",
    specs: ["Barcode · RFID", "Expiry · lot · location", "3 tools"],
    telemetry: "22 samples · 3 expiring < 30d · sync 02:14 ago",
  },
  {
    code: "AGT/05",
    title: "Intent Console",
    desc:
      "Natural-language and voice setup for worklist runs. The agent asks clarifying questions instead of guessing at ambiguous execution details.",
    status: "BETA",
    ver: "v0.9",
    specs: ["30+ tools · 7 categories", "Voice · plan mode", "Cited traces"],
    telemetry: "fit_dose_response → IC₅₀ 42.3 nM · 14:32:11",
  },
  {
    code: "AUD/06",
    title: "Run Audit Trail",
    desc:
      "Every input, validation, approval, export, result, and write-back timestamped and reproducible from saved artifacts.",
    status: "PREVIEW",
    ver: "v0.4",
    specs: ["Timestamped trace", "CSV / JSON export", "Immutable on submit"],
    telemetry: "108 / 108 tests · last sync 00:42 ago",
  },
];

const statusTone: Record<Status, string> = {
  GA: "bg-brand-soft text-brand border-brand/40",
  BETA: "bg-bf-soft text-bf border-bf/40",
  PREVIEW: "bg-bg-sunk text-ink-muted border-line-strong",
};

function ModuleRow({
  m,
  index,
}: {
  m: (typeof modules)[number];
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.05 }}
      className="group relative grid grid-cols-1 md:grid-cols-[120px_1fr_240px] gap-x-8 gap-y-4 px-6 lg:px-8 py-7 border-t border-line hover:bg-surface transition-colors"
    >
      {/* Call-sign + status (left) */}
      <div className="flex flex-col gap-2">
        <span className="font-mono text-[11px] tracking-[0.06em] text-ink-subtle uppercase">
          {m.code}
        </span>
        <span
          className={
            "inline-flex items-center gap-1.5 self-start px-1.5 py-0.5 rounded-[2px] border font-mono text-[10.5px] font-semibold tracking-[0.04em] uppercase " +
            statusTone[m.status]
          }
        >
          <span className="inline-block w-[5px] h-[5px] rounded-full bg-current" />
          {m.status}
          <span className="opacity-60 normal-case font-normal">· {m.ver}</span>
        </span>
      </div>

      {/* Title + desc (center) */}
      <div className="min-w-0">
        <h3 className="text-[20px] font-semibold tracking-[-0.02em] text-ink mb-2 group-hover:text-brand transition-colors">
          {m.title}
        </h3>
        <p className="text-[14.5px] leading-relaxed text-ink-muted max-w-[60ch]">
          {m.desc}
        </p>
        {m.telemetry && (
          <p className="mt-3 font-mono text-[11px] tracking-[0.02em] text-ink-subtle">
            <span className="text-brand">›</span> {m.telemetry}
          </p>
        )}
      </div>

      {/* Specs strip (right) */}
      <div className="flex flex-col gap-1.5 md:items-end">
        {m.specs.map((s) => (
          <span
            key={s}
            className="font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted"
          >
            {s}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

export function Features() {
  return (
    <section id="features" className="relative py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 mb-12 lg:mb-14">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-12 items-end"
        >
          <div>
            <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                03
              </span>
              <span>Execution workflow · system manifest</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink">
              One workflow.<br />
              Validated <span className="text-brand">execution.</span>
            </h2>
          </div>
          <p className="text-[15.5px] text-ink-muted leading-relaxed max-w-[42ch] md:justify-self-end">
            The surfaces support one operational path: build the run, check
            constraints, approve the worklist, ingest results, and write the
            record back to the system of record.
          </p>
        </motion.div>
      </div>

      {/* The manifest */}
      <div className="max-w-7xl mx-auto border-b border-line">
        {/* column header strip — like a CSV preamble */}
        <div className="hidden md:grid grid-cols-[120px_1fr_240px] gap-x-8 px-6 lg:px-8 py-3 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle border-t border-line bg-bg">
          <span>code · status</span>
          <span>module</span>
          <span className="md:text-right">specs</span>
        </div>

        {modules.map((m, i) => (
          <ModuleRow key={m.code} m={m} index={i} />
        ))}
      </div>
    </section>
  );
}

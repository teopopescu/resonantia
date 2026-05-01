"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { Search, X, FlaskConical, AlertCircle } from "lucide-react";
import { useSampleStore } from "@/stores/sample-store";
import type { Sample } from "@/lib/demo-data";

const TYPE_LABELS: Record<string, string> = {
  antibody: "Antibody",
  cell_line: "Cell Line",
  compound: "Compound",
  media: "Media",
  buffer: "Buffer",
  enzyme: "Enzyme",
  primer: "Primer",
  plasmid: "Plasmid",
  reagent: "Reagent",
};

const STATUS_STYLE: Record<string, { label: string; color: string; bg: string }> = {
  active: { label: "active", color: "text-brand", bg: "bg-brand-soft" },
  expiring: { label: "expiring", color: "text-bf", bg: "bg-bf-soft" },
  expired: { label: "expired", color: "text-mch", bg: "bg-mch-soft" },
  low_stock: { label: "low stock", color: "text-mch", bg: "bg-mch-soft" },
};

export default function BarcodeScanner() {
  const { scannerMode, setScannerMode, samples, openModal } = useSampleStore();
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on open
  useEffect(() => {
    if (scannerMode) {
      // Small delay so the DOM is ready
      const t = setTimeout(() => inputRef.current?.focus(), 50);
      return () => clearTimeout(t);
    }
  }, [scannerMode]);

  // Reset query when closing
  useEffect(() => {
    if (!scannerMode) setQuery("");
  }, [scannerMode]);

  const matches: Sample[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return samples.filter(
      (s) =>
        s.barcode.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
    );
  }, [query, samples]);

  if (!scannerMode) return null;

  const handleResultClick = (sample: Sample) => {
    openModal(sample);
    setScannerMode(null);
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-ink/40 backdrop-blur-sm"
        onClick={() => setScannerMode(null)}
      />

      <div className="relative bg-surface rounded-[5px] shadow-xl w-full max-w-md border border-line">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-line">
          <div>
            <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-1">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5 mr-2">
                SCAN
              </span>
              barcode lookup
            </div>
            <h2 className="text-[16px] font-semibold tracking-[-0.02em] text-ink">
              Barcode lookup
            </h2>
          </div>
          <button
            onClick={() => setScannerMode(null)}
            className="p-1.5 rounded-[3px] hover:bg-bg text-ink-muted hover:text-ink transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search input */}
        <div className="px-6 pt-5 pb-3">
          <div className="relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle pointer-events-none"
            />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="RES-2024-XXXX"
              className="w-full pl-9 pr-3 py-2.5 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors font-mono placeholder:text-ink-subtle"
            />
          </div>
          <p className="font-mono text-[11px] uppercase tracking-[0.04em] text-ink-subtle mt-2.5">
            <span className="text-brand">›</span> usb scanners auto-fill this field
          </p>
        </div>

        {/* Results */}
        <div className="px-6 pb-5">
          {query.trim() === "" ? (
            <div className="text-center py-6 font-mono text-[11.5px] uppercase tracking-[0.02em] text-ink-subtle">
              start typing to search samples
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-6">
              <AlertCircle size={20} className="mx-auto text-ink-subtle mb-2" />
              <p className="text-[13px] text-ink-muted">
                No samples matching{" "}
                <span className="font-mono text-ink">
                  &quot;{query.trim()}&quot;
                </span>
              </p>
            </div>
          ) : (
            <div className="space-y-1 max-h-64 overflow-auto">
              {matches.map((sample) => {
                const statusCfg = STATUS_STYLE[sample.status] ?? {
                  label: sample.status,
                  color: "text-ink-muted",
                  bg: "bg-bg",
                };
                return (
                  <button
                    key={sample.id}
                    onClick={() => handleResultClick(sample)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[3px] hover:bg-bg transition-colors text-left group border border-transparent hover:border-line"
                  >
                    <div className="w-8 h-8 rounded-[3px] bg-brand-soft border border-brand/30 flex items-center justify-center shrink-0">
                      <FlaskConical size={13} className="text-brand" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] font-medium text-ink truncate group-hover:text-brand transition-colors">
                        {sample.name}
                      </div>
                      <div className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-1">
                        <span>{sample.barcode}</span>
                        <span className="text-line-strong">·</span>
                        <span>{TYPE_LABELS[sample.type] ?? sample.type}</span>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center px-1.5 py-0.5 rounded-[2px] font-mono text-[10px] uppercase tracking-[0.04em] ${statusCfg.bg} ${statusCfg.color} shrink-0`}
                    >
                      {statusCfg.label}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

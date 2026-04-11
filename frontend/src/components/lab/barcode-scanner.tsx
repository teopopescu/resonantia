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
  active: { label: "Active", color: "text-emerald-600", bg: "bg-emerald-50" },
  expiring: { label: "Expiring", color: "text-yellow-600", bg: "bg-yellow-50" },
  expired: { label: "Expired", color: "text-red-600", bg: "bg-red-50" },
  low_stock: { label: "Low Stock", color: "text-orange-600", bg: "bg-orange-50" },
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
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => setScannerMode(null)}
      />

      <div className="relative bg-surface rounded-xl shadow-2xl w-full max-w-md border border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Search size={18} className="text-amber" />
            <h2 className="text-lg font-semibold text-charcoal">
              Barcode Lookup
            </h2>
          </div>
          <button
            onClick={() => setScannerMode(null)}
            className="p-1.5 rounded-lg hover:bg-cream-dark text-muted hover:text-charcoal transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search input */}
        <div className="px-6 pt-5 pb-3">
          <div className="relative">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
            />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="RES-2024-XXXX"
              className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors font-mono placeholder:text-muted/60"
            />
          </div>
          <p className="text-xs text-muted mt-2 leading-relaxed">
            Type or paste a barcode. USB barcode scanners will auto-fill this
            field.
          </p>
        </div>

        {/* Results */}
        <div className="px-6 pb-5">
          {query.trim() === "" ? (
            <div className="text-center py-6 text-xs text-muted">
              Start typing to search samples
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-6">
              <AlertCircle size={24} className="mx-auto text-muted/40 mb-2" />
              <p className="text-sm text-muted">
                No samples matching{" "}
                <span className="font-mono text-charcoal">
                  &quot;{query.trim()}&quot;
                </span>
              </p>
            </div>
          ) : (
            <div className="space-y-1.5 max-h-64 overflow-auto">
              {matches.map((sample) => {
                const statusCfg = STATUS_STYLE[sample.status] ?? {
                  label: sample.status,
                  color: "text-muted",
                  bg: "bg-cream",
                };
                return (
                  <button
                    key={sample.id}
                    onClick={() => handleResultClick(sample)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-cream transition-colors text-left group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center shrink-0">
                      <FlaskConical size={14} className="text-amber" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-charcoal truncate group-hover:text-amber transition-colors">
                        {sample.name}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted mt-0.5">
                        <span className="font-mono">{sample.barcode}</span>
                        <span className="text-border">|</span>
                        <span>{TYPE_LABELS[sample.type] ?? sample.type}</span>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${statusCfg.bg} ${statusCfg.color} shrink-0`}
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

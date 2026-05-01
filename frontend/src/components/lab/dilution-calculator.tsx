"use client";

import { useState } from "react";
import { Calculator, Loader2, Beaker } from "lucide-react";
import { useProtocolStore } from "@/stores/protocol-store";
import { cn } from "@/lib/utils";

const inputClass =
  "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle";

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
    </label>
  );
}

export default function DilutionCalculator() {
  const { dilutionResult, calculateDilution, loading } = useProtocolStore();
  const [stockConc, setStockConc] = useState("");
  const [targetConc, setTargetConc] = useState("");
  const [targetVol, setTargetVol] = useState("");
  const [unit, setUnit] = useState("uL");

  const handleCalculate = () => {
    const sc = parseFloat(stockConc);
    const tc = parseFloat(targetConc);
    const tv = parseFloat(targetVol);
    if (!isNaN(sc) && !isNaN(tc) && !isNaN(tv) && sc > 0 && tc > 0 && tv > 0) {
      calculateDilution(sc, tc, tv, unit);
    }
  };

  return (
    <div className="rounded-[5px] border border-line bg-surface overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-line bg-bg">
        <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
          C₁V₁
        </span>
        <Calculator size={14} className="text-brand" />
        <h3 className="text-[14px] font-semibold tracking-[-0.01em] text-ink">
          Dilution calculator
        </h3>
      </div>

      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FieldLabel>stock concentration</FieldLabel>
            <input
              type="number"
              value={stockConc}
              onChange={(e) => setStockConc(e.target.value)}
              placeholder="e.g. 100"
              className={cn(inputClass, "font-mono")}
            />
          </div>
          <div>
            <FieldLabel>target concentration</FieldLabel>
            <input
              type="number"
              value={targetConc}
              onChange={(e) => setTargetConc(e.target.value)}
              placeholder="e.g. 10"
              className={cn(inputClass, "font-mono")}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <FieldLabel>target volume</FieldLabel>
            <input
              type="number"
              value={targetVol}
              onChange={(e) => setTargetVol(e.target.value)}
              placeholder="e.g. 1000"
              className={cn(inputClass, "font-mono")}
            />
          </div>
          <div>
            <FieldLabel>unit</FieldLabel>
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className={cn(inputClass, "font-mono cursor-pointer")}
            >
              <option value="uL">µL</option>
              <option value="mL">mL</option>
              <option value="L">L</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading || !stockConc || !targetConc || !targetVol}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
        >
          {loading ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            <Calculator size={13} />
          )}
          Calculate
        </button>

        {dilutionResult && (
          <div className="flex items-start gap-3 p-3 bg-brand-soft rounded-[3px] border border-brand/30 mt-2">
            <Beaker size={16} className="text-brand shrink-0 mt-0.5" />
            <div className="font-mono text-[12px] text-brand leading-relaxed">
              <span className="font-semibold uppercase tracking-[0.04em] text-[10.5px]">
                result ·
              </span>{" "}
              add{" "}
              <span className="font-semibold text-ink">
                {dilutionResult.stock_volume} {dilutionResult.unit}
              </span>{" "}
              of stock to{" "}
              <span className="font-semibold text-ink">
                {dilutionResult.diluent_volume} {dilutionResult.unit}
              </span>{" "}
              of diluent
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Calculator, Loader2, Beaker } from "lucide-react";
import { useProtocolStore } from "@/stores/protocol-store";

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

  const inputClass =
    "w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40";

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <Calculator size={16} className="text-amber" />
        <h3 className="text-sm font-medium text-charcoal">Dilution Calculator</h3>
      </div>

      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Stock Concentration</label>
            <input
              type="number"
              value={stockConc}
              onChange={(e) => setStockConc(e.target.value)}
              placeholder="e.g. 100"
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Target Concentration</label>
            <input
              type="number"
              value={targetConc}
              onChange={(e) => setTargetConc(e.target.value)}
              placeholder="e.g. 10"
              className={inputClass}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Target Volume</label>
            <input
              type="number"
              value={targetVol}
              onChange={(e) => setTargetVol(e.target.value)}
              placeholder="e.g. 1000"
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Unit</label>
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className={inputClass}
            >
              <option value="uL">uL</option>
              <option value="mL">mL</option>
              <option value="L">L</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading || !stockConc || !targetConc || !targetVol}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Calculator size={14} />}
          Calculate
        </button>

        {dilutionResult && (
          <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <Beaker size={18} className="text-emerald-600 shrink-0 mt-0.5" />
            <div className="text-sm text-emerald-800">
              <p className="font-medium mb-1">Result:</p>
              <p>
                Add <strong>{dilutionResult.stock_volume} {dilutionResult.unit}</strong> of stock
                to <strong>{dilutionResult.diluent_volume} {dilutionResult.unit}</strong> of diluent
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

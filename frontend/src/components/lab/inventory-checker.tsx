"use client";

import { CheckCircle2, XCircle, Loader2, Package } from "lucide-react";
import { useProtocolStore, type InventoryCheckResult } from "@/stores/protocol-store";

interface InventoryCheckerProps {
  protocolId: string;
}

export default function InventoryChecker({ protocolId }: InventoryCheckerProps) {
  const { inventoryCheck, checkInventory, loading } = useProtocolStore();

  const availableCount = inventoryCheck?.filter((r) => r.available).length ?? 0;
  const totalCount = inventoryCheck?.length ?? 0;
  const allAvailable = availableCount === totalCount && totalCount > 0;
  const noneAvailable = availableCount === 0 && totalCount > 0;

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Package size={16} className="text-amber" />
          <h3 className="text-sm font-medium text-charcoal">Inventory Check</h3>
        </div>
        <button
          onClick={() => checkInventory(protocolId)}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors disabled:opacity-60"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Package size={12} />}
          Check Inventory
        </button>
      </div>

      {inventoryCheck && inventoryCheck.length > 0 ? (
        <>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-cream/50">
                  <th className="text-left px-4 py-2 text-xs font-medium text-muted">Reagent</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-muted">Required</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-muted">Available</th>
                  <th className="text-center px-4 py-2 text-xs font-medium text-muted">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {inventoryCheck.map((item, i) => (
                  <tr key={i} className="hover:bg-cream/30 transition-colors">
                    <td className="px-4 py-2 text-charcoal font-medium">{item.reagent_name}</td>
                    <td className="px-4 py-2 text-muted">
                      {item.required_volume} {item.required_unit}
                    </td>
                    <td className="px-4 py-2 text-muted">
                      {item.available_volume.toFixed(1)} {item.required_unit}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {item.available ? (
                        <CheckCircle2 size={16} className="text-emerald-500 inline" />
                      ) : (
                        <XCircle size={16} className="text-red-500 inline" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div
            className={`px-4 py-2.5 border-t text-xs font-medium ${
              allAvailable
                ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                : noneAvailable
                ? "bg-red-50 text-red-700 border-red-100"
                : "bg-amber-50 text-amber-700 border-amber-100"
            }`}
          >
            {availableCount} of {totalCount} reagents available
          </div>
        </>
      ) : (
        <div className="px-4 py-8 text-center text-xs text-muted">
          Click &quot;Check Inventory&quot; to verify reagent availability
        </div>
      )}
    </div>
  );
}

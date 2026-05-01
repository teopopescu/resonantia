"use client";

import { CheckCircle2, XCircle, Loader2, Package } from "lucide-react";
import { useProtocolStore } from "@/stores/protocol-store";
import { cn } from "@/lib/utils";

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
    <div className="rounded-[5px] border border-line bg-surface overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-bg">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
            INV
          </span>
          <Package size={14} className="text-brand" />
          <h3 className="text-[14px] font-semibold tracking-[-0.01em] text-ink">
            Inventory check
          </h3>
        </div>
        <button
          onClick={() => checkInventory(protocolId)}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-60"
          style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
        >
          {loading ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Package size={12} />
          )}
          Check inventory
        </button>
      </div>

      {inventoryCheck && inventoryCheck.length > 0 ? (
        <>
          <div className="overflow-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-bg">
                  {["reagent", "required", "available", "status"].map((h, i) => (
                    <th
                      key={h}
                      className={cn(
                        "px-4 py-2.5 border-b border-line font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle",
                        i === 3 ? "text-center" : "text-left"
                      )}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {inventoryCheck.map((item, i) => (
                  <tr
                    key={i}
                    className="border-b border-line last:border-b-0 hover:bg-bg transition-colors"
                  >
                    <td className="px-4 py-2.5 text-[13px] text-ink font-medium">
                      {item.reagent_name}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[12px] text-ink-muted">
                      {item.required_volume} {item.required_unit}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[12px] text-ink-muted">
                      {item.available_volume.toFixed(1)} {item.required_unit}
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      {item.available ? (
                        <CheckCircle2
                          size={14}
                          className="text-brand inline"
                        />
                      ) : (
                        <XCircle size={14} className="text-mch inline" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div
            className={cn(
              "px-4 py-2.5 border-t font-mono text-[11.5px] uppercase tracking-[0.04em]",
              allAvailable
                ? "bg-brand-soft text-brand border-brand/30"
                : noneAvailable
                ? "bg-mch-soft text-mch border-mch/30"
                : "bg-bf-soft text-bf border-bf/30"
            )}
          >
            <span className="text-ink-subtle">›</span>{" "}
            {availableCount} / {totalCount} reagents available
          </div>
        </>
      ) : (
        <div className="px-4 py-8 text-center font-mono text-[11.5px] tracking-[0.02em] uppercase text-ink-subtle">
          click <span className="text-ink">check inventory</span> to verify reagent availability
        </div>
      )}
    </div>
  );
}

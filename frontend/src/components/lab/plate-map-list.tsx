"use client";

import { motion } from "framer-motion";
import { FileText, Trash2 } from "lucide-react";
import { usePlateStore } from "@/stores/plate-store";
import { Chip } from "./primitives/data-table";
import { cn } from "@/lib/utils";

const STATUS_TONE: Record<string, "brand" | "gfp" | "dapi" | "default"> = {
  draft: "default",
  complete: "gfp",
  exported: "dapi",
};

function relTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function PlateMapList() {
  const { plateMaps, activePlateMapId, setActivePlateMap, removePlateMap } =
    usePlateStore();

  if (plateMaps.length === 0) {
    return (
      <div className="text-center py-10 bg-surface border border-line rounded-md">
        <FileText size={28} className="mx-auto mb-3 text-ink-subtle" />
        <p className="text-[13px] text-ink-muted">No runs yet</p>
        <p className="font-mono text-[11px] text-ink-subtle mt-1.5 tracking-[0.02em]">
          create one to get started
        </p>
      </div>
    );
  }

  return (
    <div className="border border-line rounded-md bg-surface overflow-hidden">
      {plateMaps.map((pm, index) => {
        const isActive = pm.id === activePlateMapId;
        return (
          <motion.div
            key={pm.id}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            onClick={() => setActivePlateMap(isActive ? null : pm.id)}
            role="button"
            tabIndex={0}
            className={cn(
              "group flex items-center gap-3 px-4 py-3 border-b border-line last:border-b-0 cursor-pointer transition-colors",
              isActive ? "bg-brand-soft" : "hover:bg-bg"
            )}
            style={
              isActive
                ? { boxShadow: "inset 2px 0 0 0 var(--color-brand)" }
                : undefined
            }
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={cn(
                    "text-[13.5px] font-medium truncate",
                    isActive ? "text-brand" : "text-ink"
                  )}
                >
                  {pm.name}
                </span>
                <Chip tone={STATUS_TONE[pm.status] || "default"}>
                  {pm.status}
                </Chip>
              </div>
              <div className="flex items-center gap-3 font-mono text-[10.5px] tracking-[0.02em] uppercase text-ink-subtle">
                <span>{relTime(pm.updatedAt)}</span>
                <span className="text-line-strong">·</span>
                <span>{pm.mappings.length} transfers</span>
                {pm.runConfig?.instrument && (
                  <>
                    <span className="text-line-strong">·</span>
                    <span>{pm.runConfig.instrument}</span>
                  </>
                )}
              </div>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                removePlateMap(pm.id);
              }}
              className="p-1.5 rounded-[3px] text-ink-subtle hover:text-mch hover:bg-mch-soft opacity-0 group-hover:opacity-100 transition-all"
              aria-label="Delete"
            >
              <Trash2 size={13} />
            </button>
          </motion.div>
        );
      })}
    </div>
  );
}

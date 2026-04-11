"use client";

import { motion } from "framer-motion";
import { FileText, Clock, ChevronRight, Trash2 } from "lucide-react";
import { usePlateStore } from "@/stores/plate-store";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-amber/15 text-amber-dark",
  complete: "bg-green-100 text-green-700",
  exported: "bg-blue-100 text-blue-700",
};

export default function PlateMapList() {
  const { plateMaps, activePlateMapId, setActivePlateMap, removePlateMap } =
    usePlateStore();

  if (plateMaps.length === 0) {
    return (
      <div className="text-center py-10 text-sm text-muted">
        <FileText size={32} className="mx-auto mb-3 opacity-40" />
        <p>No plate maps yet.</p>
        <p className="text-xs mt-1">Create one to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {plateMaps.map((pm, index) => {
        const isActive = pm.id === activePlateMapId;
        return (
          <motion.div
            key={pm.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            onClick={() => setActivePlateMap(isActive ? null : pm.id)}
            role="button"
            tabIndex={0}
            className={`w-full text-left group flex items-center gap-3 px-4 py-3 rounded-lg border transition-all cursor-pointer ${
              isActive
                ? "bg-amber/10 border-amber/40 shadow-sm"
                : "bg-surface border-border hover:border-amber/30 hover:shadow-sm"
            }`}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm font-medium text-charcoal truncate">
                  {pm.name}
                </span>
                <span
                  className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full capitalize ${
                    STATUS_STYLES[pm.status] || STATUS_STYLES.draft
                  }`}
                >
                  {pm.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-muted">
                <span className="flex items-center gap-1">
                  <Clock size={10} />
                  {new Date(pm.updatedAt).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span>{pm.mappings.length} transfers</span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removePlateMap(pm.id);
                }}
                className="p-1 rounded text-muted/50 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 size={13} />
              </button>
              <ChevronRight
                size={14}
                className={`text-muted transition-transform ${
                  isActive ? "rotate-90 text-amber" : ""
                }`}
              />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

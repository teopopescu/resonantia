"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Download, FileText, Code, FileSpreadsheet, Copy, Check } from "lucide-react";
import { usePlateStore } from "@/stores/plate-store";
import {
  generateEchoCSV,
  generateHamiltonGWL,
  generateOpentronsPython,
} from "@/lib/plate-utils";
import { API_URL } from "@/lib/api";

type WorklistFormat = "echo" | "hamilton" | "opentrons";

const FORMATS: Record<WorklistFormat, { label: string; ext: string; icon: React.ReactNode }> = {
  echo: { label: "Echo CSV", ext: ".csv", icon: <FileSpreadsheet size={14} /> },
  hamilton: { label: "Hamilton GWL", ext: ".gwl", icon: <FileText size={14} /> },
  opentrons: { label: "Opentrons Python", ext: ".py", icon: <Code size={14} /> },
};

export default function WorklistGenerator() {
  const { plateMaps, activePlateMapId } = usePlateStore();
  const [format, setFormat] = useState<WorklistFormat>("echo");
  const [copied, setCopied] = useState(false);

  const activeMap = plateMaps.find((pm) => pm.id === activePlateMapId);

  const generated = useMemo(() => {
    if (!activeMap || activeMap.mappings.length === 0) return "";
    const data = activeMap.mappings.map((m) => ({
      sourceWell: m.sourceWell,
      destWell: m.destWell,
      volume: m.volume,
      sourcePlate: "Source_1",
      destPlate: "Dest_1",
    }));

    switch (format) {
      case "echo":
        return generateEchoCSV(data);
      case "hamilton":
        return generateHamiltonGWL(data);
      case "opentrons":
        return generateOpentronsPython(data);
    }
  }, [activeMap, format]);

  const previewLines = generated.split("\n").slice(0, 20);
  const totalLines = generated.split("\n").length;

  const handleDownload = async () => {
    if (!activeMap) return;

    // Try backend first
    try {
      const backendFormat = format === "echo" ? "echo-csv" : format === "hamilton" ? "hamilton-gwl" : "opentrons-python";
      const res = await fetch(`${API_URL}/api/v1/plates/${activeMap.id}/worklist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: backendFormat, volume: activeMap.mappings[0]?.volume ?? 100 }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.worklist) {
          const ext = FORMATS[format].ext;
          const blob = new Blob([data.worklist], { type: "text/plain" });
          const blobUrl = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = blobUrl;
          a.download = `${activeMap.name.replace(/\s+/g, "_")}_worklist${ext}`;
          a.click();
          URL.revokeObjectURL(blobUrl);
          return;
        }
      }
    } catch {
      // Fall through to client-side generation
    }

    // Fallback: client-side generation
    if (!generated) return;
    const blob = new Blob([generated], { type: "text/plain" });
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `${activeMap.name.replace(/\s+/g, "_")}_worklist${FORMATS[format].ext}`;
    a.click();
    URL.revokeObjectURL(blobUrl);
  };

  const handleExportPlateMap = (type: "csv" | "json") => {
    if (!activeMap) return;
    let content: string;
    let ext: string;
    let mime: string;

    if (type === "json") {
      content = JSON.stringify(activeMap, null, 2);
      ext = ".json";
      mime = "application/json";
    } else {
      const header = "Source Well,Destination Well,Compound,Concentration (uM),Volume (nL)";
      const rows = activeMap.mappings.map(
        (m) => `${m.sourceWell},${m.destWell},${m.compound},${m.concentration},${m.volume}`
      );
      content = [header, ...rows].join("\n");
      ext = ".csv";
      mime = "text/csv";
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeMap.name.replace(/\s+/g, "_")}_platemap${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = async () => {
    if (!generated) return;
    await navigator.clipboard.writeText(generated);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!activeMap) {
    return (
      <div className="text-center py-8 text-xs text-muted">
        Select or create a plate map to generate worklists.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-charcoal">Worklist Generator</h3>

        {/* Export plate map */}
        <div className="flex gap-2">
          <button
            onClick={() => handleExportPlateMap("csv")}
            className="text-[11px] text-muted hover:text-charcoal flex items-center gap-1 transition-colors"
          >
            <FileSpreadsheet size={12} />
            Export CSV
          </button>
          <button
            onClick={() => handleExportPlateMap("json")}
            className="text-[11px] text-muted hover:text-charcoal flex items-center gap-1 transition-colors"
          >
            <FileText size={12} />
            Export JSON
          </button>
        </div>
      </div>

      {/* Format selector */}
      <div className="flex gap-2">
        {(Object.entries(FORMATS) as [WorklistFormat, (typeof FORMATS)[WorklistFormat]][]).map(
          ([key, cfg]) => (
            <button
              key={key}
              onClick={() => setFormat(key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                format === key
                  ? "bg-charcoal text-white"
                  : "bg-surface border border-border text-muted hover:border-charcoal/30 hover:text-charcoal"
              }`}
            >
              {cfg.icon}
              {cfg.label}
            </button>
          )
        )}
      </div>

      {/* Preview */}
      {activeMap.mappings.length === 0 ? (
        <div className="bg-surface border border-dashed border-border rounded-lg p-6 text-center text-xs text-muted">
          No mappings yet. Create some mappings to preview the worklist.
        </div>
      ) : (
        <div className="relative">
          <div className="bg-charcoal rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10">
              <span className="text-[10px] text-white/50 font-mono">
                {FORMATS[format].label} preview ({Math.min(20, totalLines)}/{totalLines} lines)
              </span>
              <button
                onClick={handleCopy}
                className="text-white/50 hover:text-white transition-colors"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
              </button>
            </div>
            <pre className="p-3 text-[11px] leading-relaxed text-green-300/90 overflow-x-auto max-h-64 overflow-y-auto font-mono">
              {previewLines.join("\n")}
              {totalLines > 20 && (
                <span className="text-white/30">{"\n"}... {totalLines - 20} more lines</span>
              )}
            </pre>
          </div>
        </div>
      )}

      {/* Download button */}
      {activeMap.mappings.length > 0 && (
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onClick={handleDownload}
          className="flex items-center gap-2 bg-amber text-charcoal px-4 py-2 rounded-md text-xs font-semibold shadow-sm hover:bg-amber-light transition-colors"
        >
          <Download size={14} />
          Download Worklist ({FORMATS[format].ext})
        </motion.button>
      )}
    </div>
  );
}

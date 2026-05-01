"use client";

import { useMemo, useState } from "react";
import { Download, FileText, Code, FileSpreadsheet, Copy, Check } from "lucide-react";
import { usePlateStore } from "@/stores/plate-store";
import {
  generateEchoCSV,
  generateHamiltonGWL,
  generateOpentronsPython,
} from "@/lib/plate-utils";
import { API_URL } from "@/lib/api";
import { cn } from "@/lib/utils";

type WorklistFormat = "echo" | "hamilton" | "opentrons";

const FORMATS: Record<
  WorklistFormat,
  { label: string; code: string; ext: string; icon: React.ReactNode }
> = {
  echo: {
    label: "Echo CSV",
    code: "WL/01",
    ext: ".csv",
    icon: <FileSpreadsheet size={13} />,
  },
  hamilton: {
    label: "Hamilton GWL",
    code: "WL/02",
    ext: ".gwl",
    icon: <FileText size={13} />,
  },
  opentrons: {
    label: "Opentrons Python",
    code: "WL/03",
    ext: ".py",
    icon: <Code size={13} />,
  },
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
    try {
      const backendFormat =
        format === "echo"
          ? "echo-csv"
          : format === "hamilton"
          ? "hamilton-gwl"
          : "opentrons-python";
      const res = await fetch(
        `${API_URL}/api/v1/plates/${activeMap.id}/worklist`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            format: backendFormat,
            volume: activeMap.mappings[0]?.volume ?? 100,
          }),
        }
      );
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
      // fall through to client-side
    }

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
      const header =
        "Source Well,Destination Well,Compound,Concentration (uM),Volume (nL)";
      const rows = activeMap.mappings.map(
        (m) =>
          `${m.sourceWell},${m.destWell},${m.compound},${m.concentration},${m.volume}`
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
      <div className="text-center py-8 font-mono text-[11.5px] tracking-[0.02em] uppercase text-ink-subtle">
        select or create a plate map to generate worklists
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-1">
        <div>
          <h3 className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
            Worklist generator
          </h3>
          <p className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-1">
            export to liquid handlers
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => handleExportPlateMap("csv")}
            className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted hover:text-ink transition-colors"
          >
            <FileSpreadsheet size={12} />
            export csv
          </button>
          <button
            onClick={() => handleExportPlateMap("json")}
            className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted hover:text-ink transition-colors"
          >
            <FileText size={12} />
            export json
          </button>
        </div>
      </div>

      {/* Format selector */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(FORMATS) as [WorklistFormat, typeof FORMATS[WorklistFormat]][]).map(
          ([key, cfg]) => {
            const isOn = format === key;
            return (
              <button
                key={key}
                onClick={() => setFormat(key)}
                className={cn(
                  "inline-flex items-center gap-2 px-3 py-1.5 rounded-[3px] text-[12.5px] font-medium transition-colors border",
                  isOn
                    ? "bg-brand-soft text-brand border-brand/30"
                    : "bg-surface text-ink-muted border-line hover:border-line-strong hover:text-ink"
                )}
              >
                <span className="font-mono text-[10px] tracking-[0.04em] opacity-70">
                  {cfg.code}
                </span>
                {cfg.icon}
                {cfg.label}
              </button>
            );
          }
        )}
      </div>

      {/* Preview */}
      {activeMap.mappings.length === 0 ? (
        <div className="bg-bg border border-dashed border-line-strong rounded-[5px] p-6 text-center font-mono text-[11.5px] uppercase tracking-[0.02em] text-ink-subtle">
          no mappings yet · create some to preview the worklist
        </div>
      ) : (
        <div className="bg-ink rounded-[5px] overflow-hidden border border-line-strong">
          <div className="flex items-center justify-between px-3 py-2 border-b border-white/10 bg-ink/95">
            <span className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-bg/50">
              {FORMATS[format].label} · preview {Math.min(20, totalLines)}/{totalLines}
            </span>
            <button
              onClick={handleCopy}
              className="text-bg/50 hover:text-bg transition-colors inline-flex items-center gap-1 font-mono text-[10.5px] uppercase tracking-[0.04em]"
            >
              {copied ? (
                <>
                  <Check size={11} className="text-gfp" /> copied
                </>
              ) : (
                <>
                  <Copy size={11} /> copy
                </>
              )}
            </button>
          </div>
          <pre
            className="p-3 text-[11.5px] leading-relaxed overflow-x-auto max-h-64 overflow-y-auto font-mono"
            style={{ color: "rgb(212, 255, 63)" }}
          >
            {previewLines.join("\n")}
            {totalLines > 20 && (
              <span className="text-bg/30">
                {"\n"}… {totalLines - 20} more lines
              </span>
            )}
          </pre>
        </div>
      )}

      {/* Download button */}
      {activeMap.mappings.length > 0 && (
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-2 bg-brand text-white px-3.5 py-2 rounded-[3px] text-[13px] font-semibold hover:bg-brand-strong transition-colors"
          style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
        >
          <Download size={14} />
          Download worklist
          <span className="font-mono text-[11px] opacity-70">
            ({FORMATS[format].ext})
          </span>
        </button>
      )}
    </div>
  );
}

"use client";

import { useState, useRef } from "react";
import {
  Activity,
  BarChart3,
  BookOpen,
  Dna,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Upload,
  ChevronRight,
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { useELNStore } from "@/stores/eln-store";
import { usePlateStore } from "@/stores/plate-store";
import {
  PageHeader,
} from "@/components/lab/primitives/page-header";
import { KpiStrip, Kpi } from "@/components/lab/primitives/kpi-strip";
import { Chip } from "@/components/lab/primitives/data-table";
import { cn } from "@/lib/utils";

interface ProcessingType {
  id: string;
  code: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const PROCESSING_TYPES: ProcessingType[] = [
  {
    id: "dose-response",
    code: "DR/01",
    title: "Dose-response curve fit",
    description: "4PL/3PL sigmoidal fit. IC₅₀, EC₅₀, Hill, R².",
    icon: <Activity size={16} className="text-brand" />,
  },
  {
    id: "plate-normalization",
    code: "DR/02",
    title: "Plate normalization",
    description: "Z-score, B-score, percent-of-control with control wells.",
    icon: <BarChart3 size={16} className="text-dapi" />,
  },
  {
    id: "qpcr-analysis",
    code: "DR/03",
    title: "qPCR analysis",
    description: "ΔΔCt relative expression with reference gene.",
    icon: <Dna size={16} className="text-gfp" />,
  },
];

type RunStatus = "completed" | "failed";

interface ProcessingRun {
  id: string;
  type: string;
  name: string;
  status: RunStatus;
  startedAt: string;
  duration: string;
  plateMapId?: string;
  runRecordDrafted?: boolean;
  error?: string;
  result?: Record<string, unknown>;
}

const INITIAL_RUNS: ProcessingRun[] = [
  {
    id: "r1",
    type: "dose-response",
    name: "Staurosporine IC50 — HEK293T",
    status: "completed",
    startedAt: "2026-04-11 09:32",
    duration: "12s",
  },
  {
    id: "r2",
    type: "plate-normalization",
    name: "HCS Plate Z-score Normalization",
    status: "completed",
    startedAt: "2026-04-11 08:15",
    duration: "8s",
  },
  {
    id: "r3",
    type: "dose-response",
    name: "Rapamycin IC50 — HeLa",
    status: "failed",
    startedAt: "2026-04-10 16:44",
    duration: "3s",
    error:
      "Curve fitting did not converge — insufficient data points in the transition region. Provide at least 3 concentrations near the IC50.",
  },
];

const STATUS_TONE: Record<RunStatus | "running", "brand" | "dapi" | "mch"> = {
  completed: "brand",
  running: "dapi",
  failed: "mch",
};

const STATUS_LABEL: Record<RunStatus | "running", string> = {
  completed: "completed",
  running: "running",
  failed: "failed",
};

const STATUS_ICON: Record<RunStatus | "running", React.ReactNode> = {
  completed: <CheckCircle2 size={11} />,
  running: <Loader2 size={11} className="animate-spin" />,
  failed: <AlertCircle size={11} />,
};

function summarizeResult(result: Record<string, unknown> | undefined): string {
  if (!result) return "No detailed result available.";
  const parts: string[] = [];
  if (result.ec50 !== undefined) parts.push(`EC50 ${String(result.ec50)}`);
  if (result.ic50 !== undefined) parts.push(`IC50 ${String(result.ic50)}`);
  if (result.r_squared !== undefined) parts.push(`R2 ${Number(result.r_squared).toFixed(4)}`);
  if (result.z_prime !== undefined) parts.push(`Z-prime ${Number(result.z_prime).toFixed(3)}`);
  if (parts.length > 0) return parts.join(" · ");
  return JSON.stringify(result).slice(0, 160);
}

/* ------------------------------------------------------------------ */
/* Validation helpers                                                  */
/* ------------------------------------------------------------------ */

function validateWellList(input: string): string | null {
  if (!input.trim()) return null;
  const wells = input.split(",").map((w) => w.trim());
  const wellPattern = /^[A-P]\d{1,2}$/;
  for (const w of wells) {
    if (!wellPattern.test(w)) {
      return `Invalid well "${w}" — use format like A1, B12, H6`;
    }
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* Form components                                                     */
/* ------------------------------------------------------------------ */

const inputBase =
  "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors";

function FieldLabel({
  required,
  children,
}: {
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
      {required && <span className="text-mch ml-0.5">*</span>}
    </label>
  );
}

function FileUploadButton({
  file,
  onChoose,
  label,
  accept,
}: {
  file: File | null;
  onChoose: (f: File | null) => void;
  label: string;
  accept: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onChoose(e.target.files?.[0] ?? null)}
      />
      <button
        type="button"
        onClick={() => ref.current?.click()}
        className={cn(
          "w-full inline-flex items-center justify-center gap-2 px-3 py-3 rounded-[3px] border border-dashed transition-colors text-[13px]",
          file
            ? "border-brand/40 bg-brand-soft/40 text-ink"
            : "border-line-strong bg-bg text-ink-muted hover:border-brand/40 hover:text-ink"
        )}
      >
        <Upload size={14} />
        <span className="font-mono text-[12px] tracking-[0.01em]">
          {file ? file.name : label}
        </span>
      </button>
    </>
  );
}

function FormError({ msg }: { msg: string }) {
  if (!msg) return null;
  return (
    <p className="font-mono text-[11.5px] tracking-[0.02em] text-mch flex items-center gap-1.5 px-2.5 py-1.5 bg-mch-soft border border-mch/30 rounded-[3px]">
      <AlertCircle size={12} className="shrink-0" /> {msg}
    </p>
  );
}

function RunButton({
  isRunning,
  onClick,
}: {
  isRunning: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={isRunning}
      className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
      style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
    >
      {isRunning ? (
        <>
          <Loader2 size={13} className="animate-spin" /> Running…
        </>
      ) : (
        <>
          <Play size={13} /> Run analysis
        </>
      )}
    </button>
  );
}

function DoseResponseForm({
  onRun,
  isRunning,
}: {
  onRun: (data: Record<string, unknown>) => void;
  isRunning: boolean;
}) {
  const [model, setModel] = useState("4pl");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  return (
    <div className="space-y-3 pt-3 border-t border-line">
      <p className="font-mono text-[11px] tracking-[0.02em] text-ink-muted">
        <span className="text-brand">›</span> upload csv with columns{" "}
        <span className="text-ink">concentration, response</span>
      </p>
      <FileUploadButton
        file={file}
        onChoose={(f) => {
          setFile(f);
          setError("");
        }}
        label="Choose CSV file"
        accept=".csv"
      />
      <div>
        <FieldLabel>curve model</FieldLabel>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className={cn(inputBase, "cursor-pointer")}
        >
          <option value="4pl">4-Parameter Logistic (4PL)</option>
          <option value="3pl">3-Parameter Logistic (3PL)</option>
        </select>
      </div>
      <FormError msg={error} />
      <RunButton
        isRunning={isRunning}
        onClick={() => {
          if (!file) {
            setError("Please upload a CSV with concentration and response data.");
            return;
          }
          setError("");
          onRun({ model, file });
        }}
      />
    </div>
  );
}

function PlateNormForm({
  onRun,
  isRunning,
}: {
  onRun: (data: Record<string, unknown>) => void;
  isRunning: boolean;
}) {
  const [method, setMethod] = useState("z-score");
  const [posCtrl, setPosCtrl] = useState("");
  const [negCtrl, setNegCtrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  return (
    <div className="space-y-3 pt-3 border-t border-line">
      <p className="font-mono text-[11px] tracking-[0.02em] text-ink-muted">
        <span className="text-brand">›</span> upload plate reader data, one value per well
      </p>
      <FileUploadButton
        file={file}
        onChoose={(f) => {
          setFile(f);
          setError("");
        }}
        label="Choose plate data file"
        accept=".csv,.xlsx"
      />
      <div>
        <FieldLabel>method</FieldLabel>
        <select
          value={method}
          onChange={(e) => setMethod(e.target.value)}
          className={cn(inputBase, "cursor-pointer")}
        >
          <option value="z-score">Z-score</option>
          <option value="percent-of-control">Percent of control</option>
          <option value="robust-z">Robust Z-score</option>
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <FieldLabel>positive ctrl wells</FieldLabel>
          <input
            type="text"
            value={posCtrl}
            onChange={(e) => {
              setPosCtrl(e.target.value);
              setError("");
            }}
            placeholder="e.g. A1,A2"
            className={cn(inputBase, "font-mono")}
          />
        </div>
        <div>
          <FieldLabel>negative ctrl wells</FieldLabel>
          <input
            type="text"
            value={negCtrl}
            onChange={(e) => {
              setNegCtrl(e.target.value);
              setError("");
            }}
            placeholder="e.g. H11,H12"
            className={cn(inputBase, "font-mono")}
          />
        </div>
      </div>
      <FormError msg={error} />
      <RunButton
        isRunning={isRunning}
        onClick={() => {
          if (!file) {
            setError("Please upload a plate data file.");
            return;
          }
          const posErr = validateWellList(posCtrl);
          if (posErr) {
            setError(posErr);
            return;
          }
          const negErr = validateWellList(negCtrl);
          if (negErr) {
            setError(negErr);
            return;
          }
          setError("");
          onRun({
            method,
            file,
            positive_control_wells: posCtrl
              ? posCtrl.split(",").map((s) => s.trim())
              : [],
            negative_control_wells: negCtrl
              ? negCtrl.split(",").map((s) => s.trim())
              : [],
          });
        }}
      />
    </div>
  );
}

function QpcrForm({
  onRun,
  isRunning,
}: {
  onRun: (data: Record<string, unknown>) => void;
  isRunning: boolean;
}) {
  const [refGene, setRefGene] = useState("");
  const [controlSample, setControlSample] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  return (
    <div className="space-y-3 pt-3 border-t border-line">
      <p className="font-mono text-[11px] tracking-[0.02em] text-ink-muted">
        <span className="text-brand">›</span> upload csv with columns{" "}
        <span className="text-ink">sample, gene, ct</span>
      </p>
      <FileUploadButton
        file={file}
        onChoose={(f) => {
          setFile(f);
          setError("");
        }}
        label="Choose Ct values CSV"
        accept=".csv"
      />
      <div>
        <FieldLabel required>reference gene</FieldLabel>
        <input
          type="text"
          value={refGene}
          onChange={(e) => {
            setRefGene(e.target.value);
            setError("");
          }}
          placeholder="e.g. GAPDH, ACTB"
          className={inputBase}
        />
      </div>
      <div>
        <FieldLabel required>control sample</FieldLabel>
        <input
          type="text"
          value={controlSample}
          onChange={(e) => {
            setControlSample(e.target.value);
            setError("");
          }}
          placeholder="e.g. Untreated, Vehicle"
          className={inputBase}
        />
      </div>
      <FormError msg={error} />
      <RunButton
        isRunning={isRunning}
        onClick={() => {
          if (!file) {
            setError("Please upload a CSV file with Ct values.");
            return;
          }
          if (!refGene.trim()) {
            setError("Reference gene is required (e.g. GAPDH, ACTB).");
            return;
          }
          if (!controlSample.trim()) {
            setError("Control sample is required (e.g. Untreated, Vehicle).");
            return;
          }
          setError("");
          onRun({
            file,
            reference_gene: refGene.trim(),
            control_sample: controlSample.trim(),
          });
        }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main page                                                           */
/* ------------------------------------------------------------------ */

export default function ProcessingPage() {
  const { plateMaps, updatePlateMap } = usePlateStore();
  const createEntry = useELNStore((s) => s.createEntry);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [runningAnalysis, setRunningAnalysis] = useState<string | null>(null);
  const [runs, setRuns] = useState<ProcessingRun[]>(INITIAL_RUNS);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [selectedPlateMapId, setSelectedPlateMapId] = useState<string>("");
  const runCounterRef = useRef(INITIAL_RUNS.length);

  const completedCount = runs.filter((r) => r.status === "completed").length;
  const failedCount = runs.filter((r) => r.status === "failed").length;
  const lastRun = runs[0];
  const selectedPlateMap = plateMaps.find((pm) => pm.id === selectedPlateMapId);

  const draftRunRecord = async (run: ProcessingRun) => {
    if (!run.result) return;
    const linkedRun = plateMaps.find((pm) => pm.id === run.plateMapId);
    const summary = summarizeResult(run.result);
    const title = `${run.name} — ${linkedRun?.name || "Run"} result`;
    const content = [
      "## Objective",
      `Record analysis output for ${linkedRun?.name || "an unlinked run"}.`,
      "",
      "## Run Context",
      `- Run: ${linkedRun?.name || "unlinked"}`,
      `- Instrument: ${linkedRun?.runConfig?.instrument || "not specified"}`,
      `- Transfer mode: ${linkedRun?.runConfig?.transferMode || "not specified"}`,
      `- Controls: ${linkedRun?.runConfig?.controls || "not specified"}`,
      `- Replicates: ${linkedRun?.runConfig?.replicates || "not specified"}`,
      "",
      "## Result Summary",
      summary,
      "",
      "## Structured Result",
      "```json",
      JSON.stringify(run.result, null, 2),
      "```",
      "",
      "## Audit",
      `- Analysis run: ${run.id}`,
      `- Started: ${run.startedAt}`,
      `- Duration: ${run.duration}`,
      `- Status: ${run.status}`,
    ].join("\n");

    await createEntry({
      title,
      content,
      experiment_title: linkedRun?.name,
      tags: ["run-record", "results", run.type],
    });
    setRuns((prev) =>
      prev.map((item) =>
        item.id === run.id ? { ...item, runRecordDrafted: true } : item
      )
    );
    if (linkedRun) {
      updatePlateMap(linkedRun.id, { runRecordId: `drafted-${run.id}` });
    }
  };

  const handleRunAnalysis = async (
    typeId: string,
    formData: Record<string, unknown>
  ) => {
    setRunningAnalysis(typeId);
    const startTime = Date.now();
    try {
      let fileData: number[] = [];
      const file = formData.file as File | undefined;
      if (file) {
        const text = await file.text();
        const lines = text.trim().split("\n");
        const values = lines.slice(1).flatMap((line) =>
          line
            .split(",")
            .map((v) => parseFloat(v.trim()))
            .filter((n) => !isNaN(n))
        );
        fileData = values;
      }

      let endpoint = "";
      let body: Record<string, unknown> = {};

      if (typeId === "dose-response") {
        if (fileData.length < 4) {
          throw new Error(
            "CSV must contain at least 2 data rows with Concentration and Response columns."
          );
        }
        const concentrations = fileData.filter((_, i) => i % 2 === 0);
        const responses = fileData.filter((_, i) => i % 2 === 1);
        if (concentrations.length < 2 || responses.length < 2) {
          throw new Error(
            "Need at least 2 concentration-response pairs. Check your CSV format."
          );
        }
        endpoint = "/api/v1/processing/dose-response";
        body = { concentrations, responses, model: formData.model || "4pl" };
      } else if (typeId === "plate-normalization") {
        if (fileData.length < 2) {
          throw new Error(
            "Plate data file must contain numeric values. Check your CSV format."
          );
        }
        endpoint = "/api/v1/processing/plate-normalization";
        body = {
          raw_data: fileData,
          method: formData.method || "z-score",
          positive_control_wells: formData.positive_control_wells || [],
          negative_control_wells: formData.negative_control_wells || [],
        };
      } else if (typeId === "qpcr-analysis") {
        endpoint = "/api/v1/processing/qpcr";
        const ctValues: Record<string, number[]> = {};
        if (file) {
          const text = await file.text();
          const lines = text.trim().split("\n").slice(1);
          for (const line of lines) {
            const [sample, gene, ct] = line.split(",").map((s) => s.trim());
            if (sample && gene && ct) {
              const key = gene || sample;
              if (!ctValues[key]) ctValues[key] = [];
              ctValues[key].push(parseFloat(ct));
            }
          }
        }
        if (Object.keys(ctValues).length === 0) {
          throw new Error(
            "CSV must have Sample, Gene, Ct columns with at least one data row."
          );
        }
        body = {
          ct_values: ctValues,
          reference_gene: formData.reference_gene,
          control_sample: formData.control_sample,
        };
      }

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json().catch(() => null);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      runCounterRef.current += 1;

      if (res.ok) {
        const newRun: ProcessingRun = {
          id: `r${runCounterRef.current}`,
          type: typeId,
          name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
          status: "completed",
          startedAt: new Date().toLocaleString(),
          duration: `${elapsed}s`,
          result: data,
          plateMapId: selectedPlateMapId || undefined,
        };
        setRuns((prev) => [
          newRun,
          ...prev,
        ]);
        if (selectedPlateMapId) {
          updatePlateMap(selectedPlateMapId, {
            linkedResult: {
              analysisType: typeId,
              summary: summarizeResult(data),
              result: data,
              linkedAt: new Date().toISOString(),
            },
          });
        }
      } else {
        const detail =
          data?.detail || data?.message || `Server returned HTTP ${res.status}`;
        setRuns((prev) => [
          {
            id: `r${runCounterRef.current}`,
            type: typeId,
            name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
            status: "failed",
            startedAt: new Date().toLocaleString(),
            duration: `${elapsed}s`,
            error: detail,
          },
          ...prev,
        ]);
      }
    } catch (err: unknown) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      runCounterRef.current += 1;
      const message =
        err instanceof Error
          ? err.message
          : "Server unreachable. Check that the backend is running.";
      setRuns((prev) => [
        {
          id: `r${runCounterRef.current}`,
          type: typeId,
          name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
          status: "failed",
          startedAt: new Date().toLocaleString(),
          duration: `${elapsed}s`,
          error: message,
        },
        ...prev,
      ]);
    } finally {
      setRunningAnalysis(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="06"
        markerLabel="Results · analysis pipelines"
        title="Results Analysis"
        meta={
          <>
            {runs.length} runs · <em className="not-italic text-brand">{completedCount} completed</em>{" "}
            · {failedCount} failed
          </>
        }
      />

      <KpiStrip columns={4}>
        <Kpi label="total analyses" value={runs.length} delta="all pipelines" />
        <Kpi
          label="completed"
          value={String(completedCount).padStart(2, "0")}
          delta={lastRun?.status === "completed" ? lastRun.startedAt : "—"}
          tone="brand"
        />
        <Kpi
          label="failed"
          value={String(failedCount).padStart(2, "0")}
          delta={failedCount > 0 ? "review error logs" : "no failures"}
          tone="mch"
        />
        <Kpi
          label="analysis types"
          value="03"
          delta="dose-response · norm · qpcr"
          tone="dapi"
        />
      </KpiStrip>

      <div className="flex-1 overflow-auto px-6 py-8 min-h-0">
        <div className="max-w-4xl mx-auto space-y-8">
          <section className="rounded-[5px] border border-line bg-surface p-4">
            <div className="flex flex-col md:flex-row md:items-end gap-4">
              <div className="flex-1">
                <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-2">
                  <span className="text-brand">›</span> link result to run
                </div>
                <select
                  value={selectedPlateMapId}
                  onChange={(e) => setSelectedPlateMapId(e.target.value)}
                  className="w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors"
                >
                  <option value="">No linked run</option>
                  {plateMaps.map((pm) => (
                    <option key={pm.id} value={pm.id}>
                      {pm.name} · {pm.runConfig?.instrument || "instrument not set"} · {pm.mappings.length} transfers
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:w-72 rounded-[4px] border border-line bg-bg px-3 py-2">
                <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle">
                  selected context
                </div>
                <div className="mt-1 text-[13px] text-ink truncate">
                  {selectedPlateMap
                    ? `${selectedPlateMap.runConfig?.transferMode || "run"} · ${selectedPlateMap.runConfig?.controls || "controls not specified"}`
                    : "analysis will remain unlinked"}
                </div>
              </div>
            </div>
          </section>

          {/* Pipeline cards */}
          <section>
            <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
              <span className="text-brand">›</span> available analyses
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {PROCESSING_TYPES.map((pt) => {
                const isExpanded = expandedCard === pt.id;
                const isRunning = runningAnalysis === pt.id;
                return (
                  <div
                    key={pt.id}
                    className={cn(
                      "rounded-[5px] border bg-surface transition-colors",
                      isExpanded
                        ? "border-brand/40 md:col-span-3"
                        : "border-line hover:border-line-strong"
                    )}
                  >
                    <button
                      onClick={() =>
                        setExpandedCard(isExpanded ? null : pt.id)
                      }
                      className="w-full text-left p-4"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-[3px] bg-bg border border-line flex items-center justify-center shrink-0">
                          {pt.icon}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-ink-subtle">
                              {pt.code}
                            </span>
                            {isExpanded && (
                              <Chip tone="brand">configuring</Chip>
                            )}
                          </div>
                          <h3 className="text-[14px] font-semibold tracking-[-0.01em] text-ink mb-1">
                            {pt.title}
                          </h3>
                          <p className="font-mono text-[11px] text-ink-muted leading-relaxed">
                            {pt.description}
                          </p>
                        </div>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4">
                        {pt.id === "dose-response" && (
                          <DoseResponseForm
                            onRun={(data) => handleRunAnalysis(pt.id, data)}
                            isRunning={isRunning}
                          />
                        )}
                        {pt.id === "plate-normalization" && (
                          <PlateNormForm
                            onRun={(data) => handleRunAnalysis(pt.id, data)}
                            isRunning={isRunning}
                          />
                        )}
                        {pt.id === "qpcr-analysis" && (
                          <QpcrForm
                            onRun={(data) => handleRunAnalysis(pt.id, data)}
                            isRunning={isRunning}
                          />
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          {/* Recent runs */}
          <section>
            <div className="flex items-end justify-between mb-3">
              <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
                <span className="text-brand">›</span> recent runs
              </div>
              <span className="font-mono text-[11px] uppercase tracking-[0.02em] text-ink-subtle">
                {runs.length} analyses
              </span>
            </div>

            <div className="rounded-[5px] border border-line overflow-hidden bg-surface">
              {runs.map((run, idx) => {
                const isExpanded = expandedRun === run.id;
                return (
                  <div
                    key={run.id}
                    className={cn(
                      idx > 0 && "border-t border-line"
                    )}
                  >
                    <button
                      onClick={() =>
                        setExpandedRun(isExpanded ? null : run.id)
                      }
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bg transition-colors text-left"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-[13.5px] font-medium text-ink truncate">
                          {run.name}
                        </div>
                        <div className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-0.5">
                          {PROCESSING_TYPES.find((p) => p.id === run.type)?.code} ·{" "}
                          {run.startedAt} · {run.duration}
                          {run.plateMapId && (
                            <>
                              {" "}· linked run
                            </>
                          )}
                        </div>
                      </div>

                      <Chip tone={STATUS_TONE[run.status]}>
                        {STATUS_ICON[run.status]}
                        {STATUS_LABEL[run.status]}
                      </Chip>

                      <ChevronRight
                        size={14}
                        className={cn(
                          "text-ink-subtle transition-transform shrink-0",
                          isExpanded && "rotate-90"
                        )}
                      />
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-3 pl-4 bg-bg">
                        {run.status === "failed" && run.error && (
                          <div className="flex items-start gap-2 px-3 py-2 bg-mch-soft border border-mch/30 rounded-[3px] font-mono text-[11.5px] text-mch leading-relaxed">
                            <AlertCircle size={13} className="shrink-0 mt-0.5" />
                            <div>
                              <span className="font-semibold uppercase tracking-[0.04em]">
                                error ·
                              </span>{" "}
                              {run.error}
                            </div>
                          </div>
                        )}
                        {run.status === "completed" && run.result && (
                          <div className="px-3 py-2 bg-brand-soft/50 border border-brand/30 rounded-[3px] font-mono text-[11.5px] text-brand">
                            <span className="font-semibold uppercase tracking-[0.04em]">
                              result ·
                            </span>{" "}
                            {run.result.ec50 !== undefined && (
                              <span>EC50 = {String(run.result.ec50)} · </span>
                            )}
                            {run.result.r_squared !== undefined && (
                              <span>
                                R² = {Number(run.result.r_squared).toFixed(4)} ·{" "}
                              </span>
                            )}
                            {run.result.z_prime !== undefined && (
                              <span>
                                Z′ = {Number(run.result.z_prime).toFixed(3)} ·{" "}
                              </span>
                            )}
                            {!run.result.ec50 &&
                              !run.result.r_squared &&
                              !run.result.z_prime && (
                                <span>{JSON.stringify(run.result).slice(0, 200)}</span>
                              )}
                          </div>
                        )}
                        {run.status === "completed" && run.result && (
                          <button
                            onClick={() => void draftRunRecord(run)}
                            disabled={run.runRecordDrafted}
                            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          >
                            <BookOpen size={12} />
                            {run.runRecordDrafted ? "Run record drafted" : "Draft run record"}
                          </button>
                        )}
                        {run.status === "completed" && !run.result && (
                          <p className="font-mono text-[11px] text-ink-subtle">
                            no detailed results available
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              <div className="px-4 py-2.5 border-t border-line bg-bg font-mono text-[11.5px] tracking-[0.02em] text-ink-subtle">
                showing {runs.length} analyses
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState, useRef } from "react";
import {
  Activity,
  BarChart3,
  FlaskConical,
  Dna,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Upload,
  ChevronDown,
  ChevronRight,
  X,
} from "lucide-react";
import { API_URL } from "@/lib/api";

interface ProcessingType {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  details: string;
}

const PROCESSING_TYPES: ProcessingType[] = [
  {
    id: "dose-response",
    title: "Dose-Response Curve Fitting",
    description: "Fit sigmoidal curves to concentration-response data",
    icon: <Activity size={22} className="text-amber" />,
    details:
      "Applies 4-parameter logistic regression to generate IC50/EC50 values, Hill coefficients, and confidence intervals from plate-based dose-response experiments.",
  },
  {
    id: "plate-normalization",
    title: "Plate Normalization",
    description: "Normalize assay plates using control wells",
    icon: <BarChart3 size={22} className="text-blue-500" />,
    details:
      "Performs Z-score, B-score, or percent-of-control normalization using positive and negative control wells.",
  },
  {
    id: "qpcr-analysis",
    title: "qPCR Analysis",
    description: "Analyze quantitative PCR data with delta-delta Ct",
    icon: <Dna size={22} className="text-emerald-500" />,
    details:
      "Calculates relative gene expression using the delta-delta Ct method. Supports multiple reference genes and technical replicate averaging.",
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
  error?: string;
  result?: Record<string, unknown>;
}

const INITIAL_RUNS: ProcessingRun[] = [
  {
    id: "r1",
    type: "dose-response",
    name: "Staurosporine IC50 - HEK293T",
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
    name: "Rapamycin IC50 - HeLa",
    status: "failed",
    startedAt: "2026-04-10 16:44",
    duration: "3s",
    error: "Curve fitting did not converge — insufficient data points in the transition region. Provide at least 3 concentrations near the IC50.",
  },
];

const STATUS_CONFIG: Record<
  RunStatus | "running",
  { label: string; icon: React.ReactNode; color: string; bg: string }
> = {
  completed: {
    label: "Completed",
    icon: <CheckCircle2 size={14} />,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  running: {
    label: "Running",
    icon: <Loader2 size={14} className="animate-spin" />,
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  failed: {
    label: "Failed",
    icon: <AlertCircle size={14} />,
    color: "text-red-600",
    bg: "bg-red-50",
  },
};

/* ------------------------------------------------------------------ */
/* Validation helpers                                                  */
/* ------------------------------------------------------------------ */

function validateWellList(input: string): string | null {
  if (!input.trim()) return null; // optional
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
  const fileRef = useRef<HTMLInputElement>(null);

  function handleRun() {
    if (!file) {
      setError("Please upload a CSV file with concentration and response data.");
      return;
    }
    setError("");
    onRun({ model, file });
  }

  return (
    <div className="space-y-3">
      <div className="h-px bg-border" />
      <p className="text-xs text-muted leading-relaxed">
        Upload a CSV with columns:{" "}
        <span className="font-mono text-charcoal">Concentration, Response</span>
      </p>

      <div>
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setError("");
          }}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className={`w-full flex items-center justify-center gap-2 px-3 py-3 text-sm bg-cream rounded-lg border border-dashed transition-colors ${
            file
              ? "border-emerald-300 text-charcoal"
              : "border-border text-muted hover:border-amber/40 hover:text-charcoal"
          }`}
        >
          <Upload size={14} />
          {file ? file.name : "Choose CSV file"}
        </button>
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Curve model</label>
        <div className="relative">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer"
          >
            <option value="4pl">4-Parameter Logistic (4PL)</option>
            <option value="3pl">3-Parameter Logistic (3PL)</option>
          </select>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle size={12} /> {error}
        </p>
      )}

      <RunButton isRunning={isRunning} onClick={handleRun} />
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
  const fileRef = useRef<HTMLInputElement>(null);

  function handleRun() {
    if (!file) {
      setError("Please upload a plate data file (.csv or .xlsx).");
      return;
    }
    const posErr = validateWellList(posCtrl);
    if (posErr) { setError(posErr); return; }
    const negErr = validateWellList(negCtrl);
    if (negErr) { setError(negErr); return; }

    setError("");
    onRun({
      method,
      file,
      positive_control_wells: posCtrl ? posCtrl.split(",").map((s) => s.trim()) : [],
      negative_control_wells: negCtrl ? negCtrl.split(",").map((s) => s.trim()) : [],
    });
  }

  return (
    <div className="space-y-3">
      <div className="h-px bg-border" />
      <p className="text-xs text-muted leading-relaxed">
        Upload plate reader data with one value per well.
      </p>

      <div>
        <input ref={fileRef} type="file" accept=".csv,.xlsx" className="hidden"
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(""); }} />
        <button type="button" onClick={() => fileRef.current?.click()}
          className={`w-full flex items-center justify-center gap-2 px-3 py-3 text-sm bg-cream rounded-lg border border-dashed transition-colors ${
            file ? "border-emerald-300 text-charcoal" : "border-border text-muted hover:border-amber/40 hover:text-charcoal"
          }`}>
          <Upload size={14} />
          {file ? file.name : "Choose plate data file"}
        </button>
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Normalization method</label>
        <select value={method} onChange={(e) => setMethod(e.target.value)}
          className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer">
          <option value="z-score">Z-score</option>
          <option value="percent-of-control">Percent of Control</option>
          <option value="robust-z">Robust Z-score</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Positive control wells</label>
          <input type="text" value={posCtrl} onChange={(e) => { setPosCtrl(e.target.value); setError(""); }}
            placeholder="e.g. A1,A2"
            className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 font-mono placeholder:font-sans" />
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Negative control wells</label>
          <input type="text" value={negCtrl} onChange={(e) => { setNegCtrl(e.target.value); setError(""); }}
            placeholder="e.g. H11,H12"
            className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 font-mono placeholder:font-sans" />
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle size={12} /> {error}
        </p>
      )}

      <RunButton isRunning={isRunning} onClick={handleRun} />
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
  const fileRef = useRef<HTMLInputElement>(null);

  function handleRun() {
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
    onRun({ file, reference_gene: refGene.trim(), control_sample: controlSample.trim() });
  }

  return (
    <div className="space-y-3">
      <div className="h-px bg-border" />
      <p className="text-xs text-muted leading-relaxed">
        Upload qPCR Ct values as CSV with columns:{" "}
        <span className="font-mono text-charcoal">Sample, Gene, Ct</span>
      </p>

      <div>
        <input ref={fileRef} type="file" accept=".csv" className="hidden"
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(""); }} />
        <button type="button" onClick={() => fileRef.current?.click()}
          className={`w-full flex items-center justify-center gap-2 px-3 py-3 text-sm bg-cream rounded-lg border border-dashed transition-colors ${
            file ? "border-emerald-300 text-charcoal" : "border-border text-muted hover:border-amber/40 hover:text-charcoal"
          }`}>
          <Upload size={14} />
          {file ? file.name : "Choose Ct values CSV"}
        </button>
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Reference gene <span className="text-red-400">*</span></label>
        <input type="text" value={refGene} onChange={(e) => { setRefGene(e.target.value); setError(""); }}
          placeholder="e.g. GAPDH, ACTB"
          className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40" />
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Control sample <span className="text-red-400">*</span></label>
        <input type="text" value={controlSample} onChange={(e) => { setControlSample(e.target.value); setError(""); }}
          placeholder="e.g. Untreated, Vehicle"
          className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40" />
      </div>

      {error && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle size={12} /> {error}
        </p>
      )}

      <RunButton isRunning={isRunning} onClick={handleRun} />
    </div>
  );
}

function RunButton({ isRunning, onClick }: { isRunning: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} disabled={isRunning}
      className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
      {isRunning ? (
        <><Loader2 size={14} className="animate-spin" /> Running...</>
      ) : (
        <><Play size={14} /> Run Analysis</>
      )}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* Main page                                                           */
/* ------------------------------------------------------------------ */

export default function ProcessingPage() {
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [runningAnalysis, setRunningAnalysis] = useState<string | null>(null);
  const [runs, setRuns] = useState<ProcessingRun[]>(INITIAL_RUNS);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const runCounterRef = useRef(INITIAL_RUNS.length);

  const handleRunAnalysis = async (typeId: string, formData: Record<string, unknown>) => {
    setRunningAnalysis(typeId);
    const startTime = Date.now();

    try {
      // Upload file first if present
      let fileData: number[] = [];
      const file = formData.file as File | undefined;
      if (file) {
        const text = await file.text();
        const lines = text.trim().split("\n");
        // Try to parse CSV: skip header, extract numeric values
        const values = lines.slice(1).flatMap((line) =>
          line.split(",").map((v) => parseFloat(v.trim())).filter((n) => !isNaN(n))
        );
        fileData = values;
      }

      let endpoint = "";
      let body: Record<string, unknown> = {};

      if (typeId === "dose-response") {
        if (fileData.length < 4) {
          throw new Error("CSV must contain at least 2 data rows with Concentration and Response columns.");
        }
        // Assume CSV: Concentration,Response
        const half = Math.floor(fileData.length / 2);
        const concentrations = fileData.filter((_, i) => i % 2 === 0);
        const responses = fileData.filter((_, i) => i % 2 === 1);
        if (concentrations.length < 2 || responses.length < 2) {
          throw new Error("Need at least 2 concentration-response pairs. Check your CSV format.");
        }
        endpoint = "/api/v1/processing/dose-response";
        body = { concentrations, responses, model: formData.model || "4pl" };
      } else if (typeId === "plate-normalization") {
        if (fileData.length < 2) {
          throw new Error("Plate data file must contain numeric values. Check your CSV format.");
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
        // Parse CSV into ct_values object: {sample: {gene: [ct_values]}}
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
          throw new Error("CSV must have Sample, Gene, Ct columns with at least one data row.");
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
        setRuns((prev) => [{
          id: `r${runCounterRef.current}`,
          type: typeId,
          name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
          status: "completed",
          startedAt: new Date().toLocaleString(),
          duration: `${elapsed}s`,
          result: data,
        }, ...prev]);
      } else {
        const detail = data?.detail || data?.message || `Server returned HTTP ${res.status}`;
        setRuns((prev) => [{
          id: `r${runCounterRef.current}`,
          type: typeId,
          name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
          status: "failed",
          startedAt: new Date().toLocaleString(),
          duration: `${elapsed}s`,
          error: detail,
        }, ...prev]);
      }
    } catch (err: unknown) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      runCounterRef.current += 1;
      const message = err instanceof Error ? err.message : "Server unreachable. Check that the backend is running.";
      setRuns((prev) => [{
        id: `r${runCounterRef.current}`,
        type: typeId,
        name: `${PROCESSING_TYPES.find((p) => p.id === typeId)?.title}`,
        status: "failed",
        startedAt: new Date().toLocaleString(),
        duration: `${elapsed}s`,
        error: message,
      }, ...prev]);
    } finally {
      setRunningAnalysis(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="shrink-0 px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-amber/15 flex items-center justify-center">
            <FlaskConical size={18} className="text-amber" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-charcoal">Data Processing</h1>
            <p className="text-xs text-muted">Run analysis pipelines on your experimental data</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Processing type cards */}
          <div className="grid grid-cols-3 gap-4">
            {PROCESSING_TYPES.map((pt) => {
              const isExpanded = expandedCard === pt.id;
              const isRunning = runningAnalysis === pt.id;
              return (
                <div key={pt.id}
                  className={`rounded-2xl border transition-all ${
                    isExpanded ? "border-amber/40 shadow-sm col-span-3" : "border-border hover:border-amber/20"
                  }`}>
                  <button onClick={() => setExpandedCard(isExpanded ? null : pt.id)} className="w-full text-left p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-cream flex items-center justify-center shrink-0">{pt.icon}</div>
                      <div className="min-w-0">
                        <h3 className="text-sm font-medium text-charcoal mb-1">{pt.title}</h3>
                        <p className="text-xs text-muted leading-relaxed">{pt.description}</p>
                      </div>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4">
                      {pt.id === "dose-response" && (
                        <DoseResponseForm onRun={(data) => handleRunAnalysis(pt.id, data)} isRunning={isRunning} />
                      )}
                      {pt.id === "plate-normalization" && (
                        <PlateNormForm onRun={(data) => handleRunAnalysis(pt.id, data)} isRunning={isRunning} />
                      )}
                      {pt.id === "qpcr-analysis" && (
                        <QpcrForm onRun={(data) => handleRunAnalysis(pt.id, data)} isRunning={isRunning} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Recent processing runs */}
          <div className="rounded-2xl border border-border overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <h2 className="text-sm font-medium text-charcoal">Recent Processing Runs</h2>
            </div>

            <div className="divide-y divide-border/50">
              {runs.map((run) => {
                const statusCfg = STATUS_CONFIG[run.status];
                const isExpanded = expandedRun === run.id;
                return (
                  <div key={run.id}>
                    <button
                      onClick={() => setExpandedRun(isExpanded ? null : run.id)}
                      className="w-full flex items-center gap-4 px-4 py-3 hover:bg-cream/30 transition-colors text-left"
                    >
                      <div className={`w-8 h-8 rounded-lg ${statusCfg.bg} ${statusCfg.color} flex items-center justify-center shrink-0`}>
                        {statusCfg.icon}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-charcoal truncate">{run.name}</div>
                        <div className="flex items-center gap-2 text-xs text-muted mt-0.5">
                          <span>{PROCESSING_TYPES.find((p) => p.id === run.type)?.title}</span>
                        </div>
                      </div>

                      <div className="text-xs text-muted text-right shrink-0">
                        <div>{run.startedAt}</div>
                        <div className="mt-0.5 font-mono">{run.duration}</div>
                      </div>

                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.bg} ${statusCfg.color} shrink-0`}>
                        {statusCfg.icon}
                        {statusCfg.label}
                      </span>

                      <ChevronRight size={14} className={`text-muted transition-transform shrink-0 ${isExpanded ? "rotate-90" : ""}`} />
                    </button>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="px-4 pb-3 pl-16">
                        {run.status === "failed" && run.error && (
                          <div className="flex items-start gap-2 px-3 py-2 bg-red-50 rounded-lg text-xs text-red-700">
                            <AlertCircle size={14} className="shrink-0 mt-0.5" />
                            <div>
                              <span className="font-medium">Error: </span>
                              {run.error}
                            </div>
                          </div>
                        )}
                        {run.status === "completed" && run.result && (
                          <div className="px-3 py-2 bg-emerald-50 rounded-lg text-xs text-emerald-700">
                            <span className="font-medium">Result: </span>
                            {run.result.ec50 !== undefined && <span>EC50 = {String(run.result.ec50)} | </span>}
                            {run.result.r_squared !== undefined && <span>R² = {Number(run.result.r_squared).toFixed(4)} | </span>}
                            {run.result.z_prime !== undefined && <span>Z&apos; = {Number(run.result.z_prime).toFixed(3)} | </span>}
                            {!run.result.ec50 && !run.result.r_squared && !run.result.z_prime && (
                              <span>{JSON.stringify(run.result).slice(0, 200)}</span>
                            )}
                          </div>
                        )}
                        {run.status === "completed" && !run.result && (
                          <p className="text-xs text-muted">No detailed results available.</p>
                        )}
                        {run.status === "failed" && !run.error && (
                          <p className="text-xs text-muted">No error details available.</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="px-4 py-2.5 border-t border-border text-xs text-muted">
              Showing {runs.length} runs
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

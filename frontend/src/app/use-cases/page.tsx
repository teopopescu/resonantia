"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Mic,
  LayoutGrid,
  BarChart3,
  Clock,
  CheckCircle2,
  Crosshair,
  FlaskConical,
  Search,
  Microscope,
  ArrowDownToLine,
  BookOpen,
  ArrowRight,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";

/* ---------------------------------------------------------------------- */
/*  Use-case taxonomy                                                     */
/* ---------------------------------------------------------------------- */

type Status = "ready" | "preview";

interface UseCase {
  code: string;
  title: string;
  blurb: string;
  steps: string[];
  /** Tools the agent calls — pulled from services/tool_registry.py. */
  tools: string[];
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  status: Status;
  /** Pre-filled prompt the lab chat composer reads on mount. */
  prompt: string;
}

const useCases: UseCase[] = [
  {
    code: "VOC/01",
    title: "Voice → ELN/LIMS capture",
    blurb:
      "Describe an experiment by voice while you work. The agent extracts structured fields and drafts a record your existing ELN can ingest.",
    steps: ["listen", "structure", "review", "sync"],
    tools: ["voice transcription", "create_eln_entry"],
    Icon: Mic,
    status: "ready",
    prompt:
      "Record this experiment: HEK293T viability assay, staurosporine 10-point dilution, three replicates, CellTiter-Glo readout, 0.1% DMSO vehicle control.",
  },
  {
    code: "PLT/01",
    title: "Cherry-pick hits to a 384-well follow-up",
    blurb:
      "Take the hits from a primary screen, lay them out on a confirmation plate with controls, and export an Echo worklist.",
    steps: ["select", "place", "validate", "export"],
    tools: ["cherry_pick", "create_plate_map", "generate_worklist"],
    Icon: LayoutGrid,
    status: "ready",
    prompt:
      "Cherry-pick the 24 hits from screen S-2026-014 onto a 384-well plate with column 1 + 12 controls and triplicate replicates. Generate the Echo worklist with 100 nL per transfer.",
  },
  {
    code: "DAT/01",
    title: "Dose-response → IC50 → ELN draft",
    blurb:
      "Upload reader output, fit a 4-parameter logistic curve, surface Z′ and R² flags, draft an ELN entry citing every plate referenced.",
    steps: ["upload", "fit", "QC", "draft"],
    tools: ["fit_dose_response", "calculate_z_prime", "create_eln_entry"],
    Icon: BarChart3,
    status: "ready",
    prompt:
      "Fit a 4PL dose-response on the staurosporine compound from this plate, report IC50 with the Z′ and R², and draft an ELN entry citing the source plate map.",
  },
  {
    code: "INV/01",
    title: "Reagent expiry triage",
    blurb:
      "What's expiring this month and which of those do you need for tomorrow's protocol? Surface conflicts before you hit the bench.",
    steps: ["scan", "match", "flag"],
    tools: ["get_expiring_samples", "check_inventory"],
    Icon: Clock,
    status: "ready",
    prompt:
      "List every reagent expiring in the next 30 days, then cross-check against the CellTiter-Glo cytotoxicity protocol — which expiring reagents will I need this week?",
  },
  {
    code: "PRO/01",
    title: "Protocol pre-flight + dilution math",
    blurb:
      "Before you start: confirm every reagent the protocol needs is in stock, then solve C₁V₁ = C₂V₂ for the working dilutions.",
    steps: ["lookup", "check", "calculate"],
    tools: ["check_protocol_inventory", "calculate_dilution"],
    Icon: CheckCircle2,
    status: "ready",
    prompt:
      "Run a pre-flight check on the CellTiter-Glo protocol — which reagents are in stock, and what dilutions do I need to make 200 µL of 0.5 µM staurosporine from a 10 mM stock?",
  },
  {
    code: "PLT/02",
    title: "Serial dilution layout",
    blurb:
      "Lay out an N-point serial dilution with replicates and a randomization scheme that controls for plate-position effects.",
    steps: ["seed", "dilute", "randomize", "render"],
    tools: ["serial_dilution", "create_plate_map"],
    Icon: Crosshair,
    status: "ready",
    prompt:
      "Lay out an 8-point serial dilution of staurosporine starting at 10 µM with a 1:3 fold step, three replicates each, randomized to avoid edge effects.",
  },
  {
    code: "DAT/02",
    title: "Plate normalization",
    blurb:
      "Normalize plate-reader output against control wells. Z-score, percent-of-control, or robust Z. Surfaces the Z′ before you trust the headline.",
    steps: ["load", "normalize", "QC"],
    tools: ["normalize_plate", "calculate_z_prime"],
    Icon: FlaskConical,
    status: "ready",
    prompt:
      "Normalize this plate's raw values using Z-score with positive controls in column 1 and negative controls in column 12. Report Z′ and flag any outlier wells.",
  },
  {
    code: "DAT/03",
    title: "qPCR ΔΔCt analysis",
    blurb:
      "Run delta-delta Ct against your housekeeping reference. Flag CV > 5% on technical replicates before you log the fold change.",
    steps: ["load", "ΔΔCt", "fold-change"],
    tools: ["qpcr_analysis"],
    Icon: BarChart3,
    status: "ready",
    prompt:
      "Run delta-delta Ct on this qPCR data using GAPDH as the reference and the untreated sample as the control. Flag any technical replicates with CV above 5%.",
  },
  {
    code: "SAM/01",
    title: "Hands-free sample lookup",
    blurb:
      "Gloved at the cabinet, you ask out loud. The agent returns lot, location, expiry, and remaining volume — read back so you don't have to look at a screen.",
    steps: ["speak", "lookup", "speak back"],
    tools: ["lookup_sample", "voice transcription + TTS"],
    Icon: Search,
    status: "ready",
    prompt:
      "Look up the staurosporine stock — what's the lot, location, current concentration, and remaining volume?",
  },
  {
    code: "MIC/01",
    title: "Microscopy run triage",
    blurb:
      "Surface every well from last night's imaging that needs a redo. The agent reasons over plate metadata; the UI shows the recommendation, not a viewer.",
    steps: ["scan", "flag", "recommend"],
    tools: ["browse_microscopy", "Scope-Scout agent"],
    Icon: Microscope,
    status: "ready",
    prompt:
      "Triage last night's microscopy run — which wells look like focus drift or seal failure, and which channels should we re-acquire?",
  },
  {
    code: "WL/01",
    title: "Worklist export · Echo / Hamilton / Opentrons",
    blurb:
      "From an existing plate map, produce the instrument-native worklist. Echo CSV, Hamilton GWL, or Opentrons Python — volume range validated up front.",
    steps: ["read map", "validate", "format", "download"],
    tools: ["generate_worklist"],
    Icon: ArrowDownToLine,
    status: "ready",
    prompt:
      "Generate an Echo-CSV worklist from plate map PLT-2026-019 with 100 nL per transfer. Validate the volume against the Echo-550 range before export.",
  },
  {
    code: "ELN/01",
    title: "ELN entry from artifacts",
    blurb:
      "Auto-draft an ELN entry from real artifacts (plate maps, fits, microscopy metadata). Cited inline. Submit only after explicit approval.",
    steps: ["gather", "draft", "cite", "approve"],
    tools: ["create_eln_entry", "submit_eln_entry"],
    Icon: BookOpen,
    status: "ready",
    prompt:
      "Draft an ELN entry for the staurosporine IC50 experiment, citing the source plate map, the fit results, and the QC flags. Don't submit — wait for review.",
  },
  {
    code: "BNL/01",
    title: "Benchling write-back",
    blurb:
      "Push a Resonantia ELN entry into your existing Benchling notebook with provenance attached: transcript, tool calls, and source artifacts.",
    steps: ["compose", "validate", "push", "audit"],
    tools: ["benchling_push (preview)"],
    Icon: ArrowUpRight,
    status: "preview",
    prompt: "Push this draft to Benchling under the Q2 screening project.",
  },
  {
    code: "PLN/01",
    title: "Closed-loop campaign · Plan Mode",
    blurb:
      "Multi-day campaigns with explicit gates: design plate → microscopy → analysis → next-experiment proposal. The agent pauses at every gate and waits for you.",
    steps: ["plan", "approve", "execute", "review", "iterate"],
    tools: ["Plan Mode (preview)", "Temporal workflow"],
    Icon: Sparkles,
    status: "preview",
    prompt:
      "Plan a hit-confirmation campaign for screen S-2026-014: cherry-pick the top 24, lay them out on a 384-well, image overnight, fit IC50, draft the ELN entry, and propose the next round.",
  },
];

/* ---------------------------------------------------------------------- */
/*  Page                                                                  */
/* ---------------------------------------------------------------------- */

function StatusPill({ status }: { status: Status }) {
  if (status === "ready") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-soft border border-brand/30 font-mono text-[10px] uppercase tracking-[0.06em] text-brand">
        <span className="w-1.5 h-1.5 rounded-full bg-brand" />
        Ready
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-bg-sunk border border-line font-mono text-[10px] uppercase tracking-[0.06em] text-ink-muted">
      <span className="w-1.5 h-1.5 rounded-full bg-ink-subtle" />
      Preview
    </span>
  );
}

function UseCaseCard({ c, index }: { c: UseCase; index: number }) {
  const href = `/lab?prompt=${encodeURIComponent(c.prompt)}`;
  const Icon = c.Icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.03, 0.25) }}
    >
      <Link
        href={href}
        className="group block h-full rounded-[6px] border border-line bg-surface hover:border-brand/40 hover:shadow-[0_4px_20px_-8px_rgba(31,77,58,0.15)] transition-all duration-200 p-5"
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex items-center justify-center w-8 h-8 rounded-[4px] bg-brand-soft text-brand">
              <Icon width={16} height={16} aria-hidden />
            </span>
            <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-ink-subtle">
              {c.code}
            </span>
          </div>
          <StatusPill status={c.status} />
        </div>

        <h3 className="text-[16px] font-semibold leading-snug text-ink mb-1.5 tracking-[-0.01em]">
          {c.title}
        </h3>
        <p className="text-[13px] leading-relaxed text-ink-muted mb-4">
          {c.blurb}
        </p>

        <div className="flex flex-wrap gap-1.5 mb-4">
          {c.steps.map((s, i) => (
            <span
              key={s}
              className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.05em] text-ink-muted"
            >
              {i > 0 && <span className="text-ink-subtle">·</span>}
              {s}
            </span>
          ))}
        </div>

        <div className="pt-3 border-t border-line flex items-center justify-between">
          <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle truncate">
            {c.tools.join(" · ")}
          </div>
          <span className="inline-flex items-center gap-1 text-[12px] text-ink-muted group-hover:text-brand transition-colors shrink-0">
            Try in lab
            <ArrowRight
              width={12}
              height={12}
              className="transition-transform group-hover:translate-x-0.5"
              aria-hidden
            />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

export default function UseCasesPage() {
  const ready = useCases.filter((c) => c.status === "ready");
  const preview = useCases.filter((c) => c.status === "preview");

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <Navbar />

      <main className="flex-1 pt-24 pb-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-center mb-14"
          >
            <span className="inline-block font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-subtle mb-4">
              Use cases
            </span>
            <h1 className="font-serif text-[44px] leading-[1.05] tracking-[-0.015em] text-ink mb-4">
              What scientists do{" "}
              <span className="text-brand italic">with the agent</span>
            </h1>
            <p className="max-w-2xl mx-auto text-[15px] leading-relaxed text-ink-muted">
              Wet-lab workflows the agent runs against your real plates, samples,
              and protocols. Every action is a typed tool call with an audit
              trail. Ready cases work today; preview cases land in upcoming
              releases.
            </p>
          </motion.div>

          {/* Ready section */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-mono text-[11px] uppercase tracking-[0.1em] text-ink-muted">
                Ready · {ready.length}
              </h2>
              <Link
                href="/lab"
                className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted hover:text-brand transition-colors inline-flex items-center gap-1"
              >
                Open the lab
                <ArrowRight width={11} height={11} aria-hidden />
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {ready.map((c, i) => (
                <UseCaseCard key={c.code} c={c} index={i} />
              ))}
            </div>
          </section>

          {/* Preview section */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-mono text-[11px] uppercase tracking-[0.1em] text-ink-muted">
                Preview · {preview.length}
              </h2>
              <span className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                shipping next
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {preview.map((c, i) => (
                <UseCaseCard key={c.code} c={c} index={i} />
              ))}
            </div>
          </section>

          {/* Honest scope footer */}
          <section className="rounded-[6px] border border-line bg-surface px-6 py-5 text-[13px] leading-relaxed text-ink-muted">
            <h3 className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-ink mb-2">
              What this page does NOT cover
            </h3>
            <p className="mb-2">
              Resonantia is a wet-lab operations layer. It does not run
              bioinformatics analyses (RNA-seq, variant annotation, structure
              prediction, microbiome). Pair it with a computational tool of
              your choice — the structured outputs of those tools (primer
              sets, hit lists, target panels) become Resonantia inputs at the{" "}
              <span className="font-mono text-[12px] text-ink">
                cherry-pick
              </span>{" "}
              and{" "}
              <span className="font-mono text-[12px] text-ink">
                serial dilution
              </span>{" "}
              steps above.
            </p>
            <p>
              Substrate-only features (raw microscopy viewer, full ELN editor)
              are deliberately scoped down — see{" "}
              <a
                href="https://github.com/teopopescu/resonantia/blob/main/docs/decommission-list.md"
                className="text-brand hover:underline"
              >
                docs/decommission-list.md
              </a>
              .
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}

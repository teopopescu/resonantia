"use client";

import { motion } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { CtaSection } from "@/components/cta-section";
import {
  PlateMapperMock,
  InventoryMock,
  MicroscopyMock,
  ProcessingMock,
  AgentMock,
  AuditMock,
} from "@/components/feature-mocks";
import { cn } from "@/lib/utils";

interface Feature {
  code: string;
  marker: string; // e.g. "03 · plate map · designer"
  title: React.ReactNode;
  body: React.ReactNode;
  specs: string[];
  visual: React.ReactNode;
  reverse?: boolean;
}

const features: Feature[] = [
  {
    code: "PLT/01",
    marker: "01 · plate map · designer",
    title: (
      <>
        Design plate maps in seconds,
        <br />
        not <span className="text-brand">afternoons.</span>
      </>
    ),
    body: (
      <>
        Cherry-pick, serial dilute, replicate, randomize. Build the layout once
        and the worklist drops out — formatted for{" "}
        <strong className="text-ink font-medium">
          Echo, Hamilton STAR, or Opentrons OT-2
        </strong>{" "}
        — without spreadsheet wrangling.
      </>
    ),
    specs: ["96 · 384 · 1536", "5 modes · cherry-pick to randomize", "3 worklist targets"],
    visual: <PlateMapperMock />,
  },
  {
    code: "MIC/02",
    marker: "02 · microscopy · browser",
    title: (
      <>
        Browse a thousand FOVs the way
        <br />
        the <span className="text-brand">scope sees them.</span>
      </>
    ),
    body: (
      <>
        Plate · well · channel navigation, smart fluorescence overlays, lazy
        loading at terabyte scale.{" "}
        <strong className="text-ink font-medium">
          DAPI, GFP, mCherry, brightfield
        </strong>{" "}
        compose live — no waiting on a 4&nbsp;GB folder to open.
      </>
    ),
    specs: ["DAPI · GFP · mCh · BF", "Composite + per-channel", "TIFF · OME-Zarr"],
    visual: <MicroscopyMock />,
    reverse: true,
  },
  {
    code: "DAT/03",
    marker: "03 · data processing · pipelines",
    title: (
      <>
        Raw reads in. <span className="text-brand">Publication-ready</span>
        <br />
        figures out.
      </>
    ),
    body: (
      <>
        4PL and 3PL dose-response fits, plate normalization (Z-score, B-score,
        percent-of-control), ΔΔCt qPCR.{" "}
        <strong className="text-ink font-medium">
          Cited results write back to the ELN
        </strong>{" "}
        with full provenance.
      </>
    ),
    specs: ["4PL · ΔΔCt · Z-prime", "IC₅₀ · EC₅₀ · Hill", "Cited tool calls"],
    visual: <ProcessingMock />,
  },
  {
    code: "INV/04",
    marker: "04 · inventory · samples & reagents",
    title: (
      <>
        Inventory that knows when
        <br />
        things <span className="text-brand">expire.</span>
      </>
    ),
    body: (
      <>
        Every lot, every aliquot, every freeze-thaw — barcode-first. Expiry
        alerts route to the right scientist;{" "}
        <strong className="text-ink font-medium">
          lineage written back to the ELN
        </strong>{" "}
        on every transfer.
      </>
    ),
    specs: ["Barcode · RFID", "Expiry · lot · location", "CSV import + export"],
    visual: <InventoryMock />,
    reverse: true,
  },
  {
    code: "AGT/05",
    marker: "05 · agent · console",
    title: (
      <>
        Talk to the bench
        <br />
        in <span className="text-brand">plain English.</span>
      </>
    ),
    body: (
      <>
        30+ tools across plate mapping, microscopy, processing, and inventory —
        all wired into a chat-and-voice console. Every reply{" "}
        <strong className="text-ink font-medium">
          cites the tool calls it made
        </strong>{" "}
        so you can audit the agent like a colleague.
      </>
    ),
    specs: ["30+ tools · 7 categories", "Voice + chat + plan", "Cited traces"],
    visual: <AgentMock />,
  },
  {
    code: "AUD/06",
    marker: "06 · activity log",
    title: (
      <>
        Every action <span className="text-brand">timestamped,</span>
        <br />
        every parameter logged.
      </>
    ),
    body: (
      <>
        Tool calls, parameters, results, and human approvals all timestamped
        and exportable.{" "}
        <strong className="text-ink font-medium">
          Submitted ELN entries are immutable
        </strong>{" "}
        — audit the bench like a clean code review.
      </>
    ),
    specs: ["Timestamped trace", "CSV / JSON export", "Immutable on submit"],
    visual: <AuditMock />,
    reverse: true,
  },
];

function FeatureRow({ feature, index }: { feature: Feature; index: number }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      className="border-t border-line py-20 lg:py-24"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div
          className={cn(
            "grid grid-cols-1 lg:grid-cols-[5fr_7fr] gap-10 lg:gap-14 items-start",
            feature.reverse && "lg:[direction:rtl]"
          )}
        >
          <div className={cn(feature.reverse && "lg:[direction:ltr]")}>
            <div className="inline-flex items-center gap-2.5 mb-5 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span>{feature.marker.split(" · ").slice(1).join(" · ")}</span>
              <span className="text-line-strong">·</span>
              <span className="font-semibold text-ink">{feature.code}</span>
            </div>
            <h2 className="text-[34px] sm:text-[42px] font-semibold tracking-[-0.03em] leading-[1.05] text-ink">
              {feature.title}
            </h2>
            <p className="mt-5 text-[15.5px] text-ink-muted leading-relaxed max-w-[44ch]">
              {feature.body}
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {feature.specs.map((s) => (
                <span
                  key={s}
                  className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted bg-bg border border-line rounded-[2px] px-2 py-1"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div className={cn("min-w-0", feature.reverse && "lg:[direction:ltr]")}>
            {feature.visual}
          </div>
        </div>
      </div>
    </motion.section>
  );
}

export default function FeaturesPage() {
  return (
    <>
      <Navbar />
      <div className="h-16" />
      <main>
        {/* Page hero */}
        <section className="pt-24 pb-12 lg:pt-28 lg:pb-16 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10 items-end"
            >
              <div>
                <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                  <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                    FT
                  </span>
                  <span>Features · system tour</span>
                </div>
                <h1 className="text-[48px] sm:text-[64px] lg:text-[80px] leading-[0.96] tracking-[-0.04em] text-ink">
                  <span className="font-light">Six modules,</span>
                  <br />
                  <span className="font-bold">
                    one <span className="text-brand">surface.</span>
                  </span>
                </h1>
              </div>
              <p className="text-[16px] text-ink-muted leading-relaxed max-w-[44ch] md:justify-self-end">
                Each module is wired into the agent and into the others — your
                plate map knows the inventory, the curve fitter writes back to
                the ELN, every action is logged and cited.
              </p>
            </motion.div>
          </div>
        </section>

        {features.map((f, i) => (
          <FeatureRow key={f.code} feature={f} index={i} />
        ))}

        <CtaSection />
      </main>
      <Footer />
    </>
  );
}

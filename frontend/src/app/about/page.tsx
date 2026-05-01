"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { motion } from "framer-motion";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface ProblemItem {
  code: string;
  title: string;
  cost: string;
  description: React.ReactNode;
  answer: React.ReactNode;
}

const problems: ProblemItem[] = [
  {
    code: "01",
    title: "Plate maps in Excel",
    cost: "~3 hrs per 384-well design",
    description: (
      <>
        Copy-paste errors. No validation. The senior scientist&rsquo;s macro
        from 2019 that no one wants to touch. Cherry-picking 24 hits across
        three plates is an afternoon job, every time.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">Plate maps in 90 seconds.</strong>{" "}
        Cherry-pick, serial-dilute, replicate, randomize — the agent applies
        edge-effect controls and balances replicates without being asked. One
        sentence in chat instead of an afternoon in Excel.
      </>
    ),
  },
  {
    code: "02",
    title: "Worklists for liquid handlers",
    cost: "30–60 min per export · format errors",
    description: (
      <>
        Echo wants Source/Destination CSV. Hamilton wants{" "}
        <span className="font-mono text-ink">.gwl</span>. Opentrons wants Python.
        Same plate map, three formats, three chances for an off-by-one well to
        ruin a 384-plate transfer.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">One plate map, three exports.</strong>{" "}
        Echo &middot; Hamilton STAR &middot; Opentrons OT-2 — generated from
        the same source of truth. Format-validated before it leaves the agent.
      </>
    ),
  },
  {
    code: "03",
    title: "Curve fitting, one plate at a time",
    cost: "~40 min/plate × 50 plates = a lost weekend",
    description: (
      <>
        Open file. Configure 4PL. Click fit. Eyeball IC₅₀. Copy to Excel.
        Repeat 50 times. By Sunday night the IC₅₀s are in a spreadsheet,
        disconnected from the source data and the compound metadata.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">Batch fits, written back in place.</strong>{" "}
        50 plates fitted in parallel. IC₅₀, Hill slope, and Z′ linked to the
        source plate, the compound, and your ELN entry. Outliers flagged
        before you see them.
      </>
    ),
  },
  {
    code: "04",
    title: "ELN entries written after the fact",
    cost: "2–4 hrs per experiment · fading detail",
    description: (
      <>
        You meant to write up Friday&rsquo;s experiment. By Tuesday the
        parameters are fuzzy, the plate IDs are gone, and three figures are
        missing the legends you remember making.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">Drafts from your actual data.</strong>{" "}
        The agent reads the plate map, the fit results, the microscopy, and
        writes a structured draft. You review, edit, sign. The detail is
        captured while it&rsquo;s still real.
      </>
    ),
  },
  {
    code: "05",
    title: "Hunting for reagents and lots",
    cost: "~20 min/day · constant interruption",
    description: (
      <>
        &ldquo;Where&rsquo;s the puromycin?&rdquo; &middot; &ldquo;Is lot
        RG-2024-8860 still good?&rdquo; &middot; &ldquo;Did we order more
        DMEM?&rdquo; A flow killer, every time.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">Inventory the agent knows.</strong>{" "}
        Barcode lookup, expiry alerts, low-stock auto-flags. The agent uses
        this knowledge when it designs your plate maps — won&rsquo;t suggest
        a reagent that&rsquo;s out or expiring next week.
      </>
    ),
  },
  {
    code: "06",
    title: "Tribal knowledge in DMs and senior heads",
    cost: "Weeks of ramp-up for every new scientist",
    description: (
      <>
        &ldquo;Always run staurosporine at 1 µM.&rdquo; &middot; &ldquo;HEK
        lot 7720 had a contamination issue.&rdquo; &middot; &ldquo;Plate seal
        from supplier X gives evaporation on edges.&rdquo; All of this lives
        in Slack threads and senior scientists&rsquo; memory.
      </>
    ),
    answer: (
      <>
        <strong className="text-ink font-medium">Lab memory that compounds.</strong>{" "}
        Every correction you give the agent becomes a fact it remembers — per
        project, per lab. New hires inherit the institutional knowledge
        instead of rediscovering it.
      </>
    ),
  },
];

const audiences = [
  {
    code: "AC",
    label: "Academic screening cores",
    body: "Broad-class imaging platforms, university HTS facilities, and translational research centers running phenotypic and target-based assays at academic scale.",
    examples: "Broad, ICR Cancer Therapeutics, Karolinska KINDS, Princeton HTRC",
  },
  {
    code: "BT",
    label: "Mid-stage biotech R&D",
    body: "Series A–C drug discovery teams (10–80 scientists) with real screening pipelines and the autonomy to choose their own tooling — before they&rsquo;re locked into enterprise stacks.",
    examples: "Dewpoint, Spring Discovery, Cellarity, Strand, Bicycle",
  },
  {
    code: "PH",
    label: "Pharma R&D functional teams",
    body: "A specific team inside a large pharma — a high-content imaging core, a phenotypic screening unit, a kinase profiling group — adopting modern tooling for one workflow without enterprise procurement.",
    examples: "AstraZeneca cellular imaging · Sanofi mRNA · Roche / Genentech specific groups",
  },
];

function ProblemRow({ p, index }: { p: ProblemItem; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.05 }}
      className="grid grid-cols-1 lg:grid-cols-[60px_1fr_1fr] gap-x-8 gap-y-4 px-6 lg:px-8 py-7 border-t border-line"
    >
      {/* Code */}
      <div>
        <span className="font-mono text-[10.5px] tracking-[0.06em] uppercase font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
          {p.code}
        </span>
      </div>

      {/* Problem */}
      <div className="min-w-0">
        <h3 className="text-[19px] font-semibold tracking-[-0.02em] text-ink mb-2">
          {p.title}
        </h3>
        <div className="font-mono text-[11px] tracking-[0.04em] uppercase text-ink-subtle mb-3">
          <span className="text-brand">›</span> {p.cost}
        </div>
        <p className="text-[14.5px] leading-relaxed text-ink-muted">
          {p.description}
        </p>
      </div>

      {/* Answer */}
      <div className="min-w-0 lg:pl-6 lg:border-l lg:border-line">
        <div className="font-mono text-[10.5px] tracking-[0.06em] uppercase text-ink-subtle mb-2">
          <span className="text-brand">›</span> what Resonantia does
        </div>
        <p className="text-[14.5px] leading-relaxed text-ink-muted">{p.answer}</p>
      </div>
    </motion.div>
  );
}

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <div className="h-16" />

      <main>
        {/* Hero */}
        <section className="pt-20 pb-12 lg:pt-24 lg:pb-16 border-b border-line">
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
                    AB
                  </span>
                  <span>About · why we&rsquo;re building this</span>
                </div>
                <h1 className="text-[44px] sm:text-[60px] lg:text-[72px] leading-[0.98] tracking-[-0.04em] text-ink">
                  <span className="font-light">Scientists shouldn&rsquo;t</span>
                  <br />
                  <span className="font-light">spend afternoons</span>
                  <br />
                  <span className="font-bold">
                    writing <span className="text-brand">Excel macros.</span>
                  </span>
                </h1>
              </div>
              <p className="text-[16px] text-ink-muted leading-relaxed max-w-[44ch] md:justify-self-end">
                We&rsquo;re building the{" "}
                <strong className="text-ink font-medium">agentic co-scientist</strong>{" "}
                for the wet lab — an agent that designs your plate maps,
                runs your fits, drafts your notebook entries, and asks before
                it does anything destructive.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Section 01 — Problems */}
        <section className="py-20 lg:py-24 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8 mb-12">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10 items-end"
            >
              <div>
                <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                  <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                    01
                  </span>
                  <span>The problems · what wet-lab scientists waste time on</span>
                </div>
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink">
                  Six things every scientist
                  <br />
                  fights with{" "}
                  <span className="text-brand">every week.</span>
                </h2>
              </div>
              <p className="text-[15px] text-ink-muted leading-relaxed max-w-[42ch] md:justify-self-end">
                These aren&rsquo;t hypothetical pains. Each one represents
                hours per week, per scientist, in every screening lab and biotech R&amp;D
                team we&rsquo;ve talked to.
              </p>
            </motion.div>
          </div>

          <div className="max-w-7xl mx-auto border-b border-line">
            {/* Header strip */}
            <div className="hidden lg:grid grid-cols-[60px_1fr_1fr] gap-x-8 px-6 lg:px-8 py-3 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle border-t border-line bg-bg">
              <span></span>
              <span>the problem</span>
              <span className="lg:pl-6">how we answer</span>
            </div>
            {problems.map((p, i) => (
              <ProblemRow key={p.code} p={p} index={i} />
            ))}
          </div>
        </section>

        {/* Section 02 — Why now */}
        <section className="py-20 lg:py-24 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10"
            >
              <div>
                <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                  <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                    02
                  </span>
                  <span>Why now · the inflection</span>
                </div>
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink mb-6">
                  AI agents are good enough.
                  <br />
                  Lab tools{" "}
                  <span className="text-brand">haven&rsquo;t caught up.</span>
                </h2>
              </div>

              <div className="space-y-5 text-[15px] text-ink-muted leading-relaxed">
                <p>
                  Two years ago, agents couldn&rsquo;t reliably chain tool
                  calls or reason about scientific results. Today, frontier
                  models{" "}
                  <strong className="text-ink font-medium">
                    plan multi-step experiments, interpret Z-prime, and cite
                    every action they take.
                  </strong>
                </p>
                <p>
                  The LIMS / ELN / instrument-software stack hasn&rsquo;t
                  meaningfully changed since 2015. Benchling, IDBS, Genedata,
                  Dotmatics — all of them ship adequate ELN editors and
                  registries from a pre-agent era. Adding chat to those
                  surfaces gives you a search box, not a co-scientist.
                </p>
                <p>
                  The window for an agent-native lab informatics platform is
                  open right now —{" "}
                  <strong className="text-ink font-medium">
                    built around the agent, not bolted onto an ELN.
                  </strong>{" "}
                  We&rsquo;re building it.
                </p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Section 03 — Who it's for */}
        <section className="py-20 lg:py-24 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-12"
            >
              <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                  03
                </span>
                <span>Who this is for · today</span>
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink">
                Three audiences,
                <br />
                <span className="text-brand">one product fit.</span>
              </h2>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-5">
              {audiences.map((a, i) => (
                <motion.div
                  key={a.code}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.45, delay: i * 0.06 }}
                  className="rounded-[5px] border border-line bg-surface p-6"
                >
                  <span className="font-mono text-[10.5px] tracking-[0.06em] uppercase font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                    {a.code}
                  </span>
                  <h3 className="mt-4 text-[18px] font-semibold tracking-[-0.015em] text-ink mb-3">
                    {a.label}
                  </h3>
                  <p className="text-[13.5px] text-ink-muted leading-relaxed mb-4">
                    {a.body}
                  </p>
                  <div className="font-mono text-[10.5px] tracking-[0.04em] uppercase text-ink-subtle pt-3 border-t border-dashed border-line">
                    <span className="text-brand">›</span> e.g. {a.examples}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Section 04 — Founding ethos */}
        <section className="py-20 lg:py-24 border-b border-line">
          <div className="max-w-3xl mx-auto px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                  04
                </span>
                <span>The team · who we are</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-semibold leading-[1.1] tracking-[-0.025em] text-ink mb-6">
                We&rsquo;ve watched scientists
                <br />
                lose afternoons to{" "}
                <span className="text-brand">spreadsheets.</span>
              </h2>

              <div className="space-y-5 text-[15px] text-ink-muted leading-relaxed">
                <p>
                  Resonantia is built by engineers and scientists who&rsquo;ve
                  watched senior PIs and postdocs spend Friday afternoons
                  formatting plate maps in Excel and Sunday nights fitting
                  curves one plate at a time. We thought it should be better
                  than that.
                </p>
                <p>
                  We&rsquo;re not trying to replace Benchling. We&rsquo;re
                  building the agent layer on top — the part that does the
                  busywork, learns your lab&rsquo;s preferences, and writes
                  back to whatever ELN you already use.
                </p>
              </div>

              <div className="mt-12 flex items-start gap-5">
                <span
                  className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[5px] rounded-[5px] bg-surface border border-line-strong shrink-0"
                  style={{ width: 48, height: 48 }}
                  aria-hidden="true"
                >
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-brand" />
                </span>
                <div>
                  <div className="text-[15px] font-semibold text-ink tracking-[-0.01em]">
                    Teodor Popescu
                  </div>
                  <div className="font-mono text-[11px] tracking-[0.02em] uppercase text-ink-subtle mt-0.5">
                    Founder
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 lg:py-24">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-3xl mx-auto px-6 lg:px-8 text-center"
          >
            <div className="inline-flex items-center gap-2.5 mb-5 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                DP
              </span>
              <span>Design partner program · 3 slots open</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink mb-5">
              Ready to{" "}
              <span className="text-brand">stop wrestling</span>
              <br />
              with spreadsheets?
            </h2>
            <p className="text-[15.5px] text-ink-muted leading-relaxed max-w-xl mx-auto mb-10">
              We&rsquo;re looking for three design partners. Free for 12 months
              in exchange for weekly feedback, anonymized usage data, and a
              co-branded case study.
            </p>
            <Link
              href="mailto:hello@resonantia.io?subject=Resonantia · Design partner inquiry"
              className="inline-flex items-center gap-2 px-5 py-3 bg-brand text-white text-[14px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
              style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
            >
              Contact us
              <span className="font-mono text-[14px] leading-none">→</span>
            </Link>
          </motion.div>
        </section>
      </main>
      <Footer />
    </>
  );
}

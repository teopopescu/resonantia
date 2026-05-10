"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { motion } from "framer-motion";
import { useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface Tier {
  code: string;
  name: string;
  price: string;
  period?: string;
  blurb: string;
  cta: string;
  ctaHref: string;
  featured?: boolean;
  allowance?: string[];
  features: string[];
}

const tiers: Tier[] = [
  {
    code: "DP",
    name: "Design partner",
    price: "Free",
    period: "for 12 months",
    blurb: "In exchange: weekly feedback sessions, anonymized usage data, and a co-branded case study after 6 months.",
    cta: "Apply for a slot",
    ctaHref: "mailto:hello@resonantia.io?subject=Design%20partner%20application",
    featured: true,
    allowance: ["Full platform access", "Direct line to co-founders", "Slack channel + weekly call"],
    features: [
      "Everything in Team tier",
      "Hands-on onboarding",
      "Direct input into the roadmap",
      "Locked-in 50% discount post-program",
    ],
  },
  {
    code: "PRO",
    name: "Pro",
    price: "Contact us",
    blurb: "For active researchers using the agent daily.",
    cta: "Contact us",
    ctaHref: "mailto:hello@resonantia.io?subject=Pro%20tier%20inquiry",
    features: [
      "Plate map designer + worklist export",
      "All data processing pipelines",
      "ELN auto-drafting from experiments",
      "Cited tool-call traces",
      "Voice mode",
      "Email support",
    ],
  },
  {
    code: "TEAM",
    name: "Team",
    price: "Contact us",
    blurb: "For 5-50 person teams running shared projects.",
    cta: "Contact us",
    ctaHref: "mailto:hello@resonantia.io?subject=Team%20tier%20inquiry",
    features: [
      "Everything in Pro",
      "Roles: scientist / reviewer / admin",
      "Shared projects + entity linking",
      "Audit log + activity export",
      "eLabFTW integration",
      "Slack support",
    ],
  },
  {
    code: "ENT",
    name: "Enterprise",
    price: "Contact us",
    blurb: "For 50+ user teams in pharma + regulated environments.",
    cta: "Contact us",
    ctaHref: "mailto:hello@resonantia.io?subject=Enterprise%20inquiry",
    features: [
      "Everything in Team",
      "Private VPC deployment",
      "Full SSO / SAML / SCIM",
      "21 CFR Part 11 path",
      "Dedicated success manager + SLA",
    ],
  },
];

const faqs = [
  {
    question: "What's an \"agent turn\" and why is it metered?",
    answer:
      "A turn is one round-trip with the agent — your input, the planner's reasoning, the specialist that runs your task, and the critic's review. A typical light query is one turn; a complex multi-step plan can chain into 3-5 turns as the agent works through it. We meter because LLM inference is a real per-call cost; allowances let you forecast bills and overage covers heavy use without surprises.",
  },
  {
    question: "Where is my data hosted?",
    answer:
      "Cloud customers run on encrypted Postgres in EU or US regions, your choice. Microscopy and large file storage on S3-compatible object storage with at-rest encryption. Enterprise customers can deploy the entire stack — gateway, agent, vLLM, database — into their own VPC with no data egress.",
  },
  {
    question: "Is this SOC 2 / 21 CFR Part 11 compliant?",
    answer:
      "Not yet. SOC 2 Type II is in progress and required before enterprise GA — design partners run on segregated tenants with full audit logging today. The 21 CFR Part 11 path is part of the Enterprise engagement: tamper-evident audit logs, witness/co-sign workflows, and validated environment support.",
  },
  {
    question: "What instruments do you support?",
    answer:
      "Worklist export to Beckman Echo, Hamilton STAR, and Opentrons OT-2 today. Tecan Fluent and Beckman Biomek are on the roadmap. For microscopy, we read OME-Zarr and TIFF; importers for Phenix, Operetta, ImageXpress, and Cytation are part of the Enterprise integration scope. If you need a specific instrument, ask — we can usually add an exporter in a sprint.",
  },
  {
    question: "How does the design-partner program work?",
    answer:
      "Three slots, free for 12 months. We ask for: a weekly 30-minute call with the lead scientist, anonymized usage telemetry to improve agent quality, and permission to publish a case study after 6 months. In exchange you get the full product, hands-on onboarding, direct input into the roadmap, and a locked-in 50% discount once the program ends.",
  },
];

function FaqItem({ faq, index }: { faq: { question: string; answer: string }; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.04 }}
      className="border-b border-line"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left py-5 flex items-start justify-between gap-4 hover:bg-surface transition-colors px-2 -mx-2 rounded-[3px]"
      >
        <h3 className="text-[15px] font-medium text-ink leading-snug">{faq.question}</h3>
        <ChevronDown
          size={16}
          className={cn(
            "text-ink-subtle shrink-0 mt-0.5 transition-transform duration-200",
            open && "rotate-180"
          )}
        />
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25 }}
        className="overflow-hidden"
      >
        <p className="text-[14px] text-ink-muted leading-relaxed pb-5 max-w-[68ch]">
          {faq.answer}
        </p>
      </motion.div>
    </motion.div>
  );
}

function TierCard({ tier, index }: { tier: Tier; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.05 }}
      className={cn(
        "relative flex flex-col h-full rounded-[5px] border bg-surface transition-colors",
        tier.featured ? "border-brand" : "border-line"
      )}
    >
      {tier.featured && (
        <div className="absolute -top-2.5 left-5">
          <span className="font-mono text-[10px] tracking-[0.06em] uppercase font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
            Most popular
          </span>
        </div>
      )}

      <div className="p-6 flex-1 flex flex-col">
        <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
          <span className="text-brand">›</span> {tier.code} · {tier.name}
        </div>

        <div className="mb-5">
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-[36px] tracking-[-0.035em] text-ink leading-none">
              {tier.price}
            </span>
            {tier.period && (
              <span className="font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted">
                {tier.period}
              </span>
            )}
          </div>
        </div>

        <p className="text-[13.5px] text-ink-muted leading-relaxed mb-5 max-w-[34ch]">
          {tier.blurb}
        </p>

        {tier.allowance && (
          <div className="mb-5 pb-5 border-b border-line">
            <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle mb-2">
              Allowance
            </div>
            <ul className="space-y-1.5">
              {tier.allowance.map((a) => (
                <li
                  key={a}
                  className="font-mono text-[11.5px] tracking-[0.01em] text-ink-muted leading-relaxed"
                >
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}

        <ul className="space-y-2.5 flex-1 mb-6">
          {tier.features.map((f) => (
            <li key={f} className="flex items-start gap-2.5">
              <Check size={14} className="text-brand shrink-0 mt-0.5" />
              <span className="text-[13px] text-ink leading-snug">{f}</span>
            </li>
          ))}
        </ul>

        <Link
          href={tier.ctaHref}
          className={cn(
            "inline-flex items-center justify-center gap-2 px-4 py-2.5 text-[13.5px] font-medium rounded-[3px] transition-colors",
            tier.featured
              ? "bg-brand text-white hover:bg-brand-strong"
              : "border border-line-strong text-ink hover:border-ink hover:bg-bg"
          )}
          style={
            tier.featured
              ? { boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }
              : undefined
          }
        >
          {tier.cta}
          <span className="font-mono text-[14px] leading-none">→</span>
        </Link>
      </div>
    </motion.div>
  );
}

export default function PricingPage() {
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
                    PR
                  </span>
                  <span>Pricing · usage-aware</span>
                </div>
                <h1 className="text-[44px] sm:text-[58px] lg:text-[72px] leading-[0.98] tracking-[-0.04em] text-ink">
                  <span className="font-light">Pricing that scales</span>
                  <br />
                  <span className="font-bold">
                    with the <span className="text-brand">agent.</span>
                  </span>
                </h1>
              </div>
              <p className="text-[15.5px] text-ink-muted leading-relaxed max-w-[44ch] md:justify-self-end">
                Each tier comes with an <strong className="text-ink font-medium">agent-turn allowance</strong> — predictable
                bills, no surprises. Power users pay for overage; design partners
                run free for a year.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Tiers */}
        <section className="py-16 lg:py-20 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 lg:gap-5">
              {tiers.map((tier, i) => (
                <TierCard key={tier.code} tier={tier} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* What's an agent turn */}
        <section className="py-16 lg:py-20 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10">
              <div>
                <div className="inline-flex items-center gap-2.5 mb-5 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                  <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                    AT
                  </span>
                  <span>Agent turns · how the meter works</span>
                </div>
                <h2 className="text-[28px] sm:text-[34px] font-semibold leading-[1.1] tracking-[-0.025em] text-ink mb-4">
                  An <span className="text-brand">honest meter,</span> sized for real workflows.
                </h2>
                <p className="text-[15px] text-ink-muted leading-relaxed max-w-[60ch]">
                  One turn = one round-trip with the agent. You ask, the planner
                  reasons, the specialist runs your task, the critic reviews.
                  Light queries are one turn; complex multi-step plans chain into
                  3–5 turns as the agent works.
                </p>
              </div>

              <div className="space-y-2">
                {[
                  {
                    k: "light",
                    v: "lookups, sample queries, status checks",
                    turns: "~1 turn",
                  },
                  {
                    k: "medium",
                    v: "design a plate map, fit one curve, draft a notebook entry",
                    turns: "~2–3 turns",
                  },
                  {
                    k: "heavy",
                    v: "multi-day plan with microscopy review and full ELN",
                    turns: "~5+ turns",
                  },
                ].map((row) => (
                  <div
                    key={row.k}
                    className="flex items-baseline justify-between gap-4 px-4 py-3 bg-surface border border-line rounded-[5px]"
                  >
                    <div className="min-w-0">
                      <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-brand">
                        {row.k}
                      </div>
                      <div className="text-[13.5px] text-ink mt-0.5">{row.v}</div>
                    </div>
                    <div className="font-mono text-[12px] text-ink-muted whitespace-nowrap">
                      {row.turns}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-16 lg:py-20">
          <div className="max-w-3xl mx-auto px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-10"
            >
              <div className="inline-flex items-center gap-2.5 mb-5 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                  FAQ
                </span>
                <span>Frequently asked</span>
              </div>
              <h2 className="text-[28px] sm:text-[34px] font-semibold leading-[1.1] tracking-[-0.025em] text-ink">
                Common questions.
              </h2>
            </motion.div>

            <div className="border-t border-line">
              {faqs.map((faq, i) => (
                <FaqItem key={faq.question} faq={faq} index={i} />
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}

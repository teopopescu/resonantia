"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import Link from "next/link";

function AnimatedSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    description: "For individual researchers getting started.",
    cta: "Get started free",
    ctaHref: "/lab",
    featured: false,
    features: [
      "1 user",
      "5 plate maps per month",
      "Basic data processing (dose-response, normalization)",
      "Sample tracking (up to 100 items)",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$99",
    period: "/user/month",
    description: "For active researchers who need full capabilities.",
    cta: "Start free trial",
    ctaHref: "/lab",
    featured: true,
    features: [
      "Unlimited plate maps",
      "All data processing pipelines",
      "Microscopy image browser",
      "Unlimited sample tracking",
      "File upload & download",
      "Priority support",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For teams that need control, compliance, and scale.",
    cta: "Contact sales",
    ctaHref: "mailto:hello@resonantia.io",
    featured: false,
    features: [
      "Everything in Pro",
      "Multi-user teams with roles",
      "Audit logging & compliance reports",
      "SSO / SAML",
      "Custom instrument integrations",
      "Dedicated support & SLA",
    ],
  },
];

const faqs = [
  {
    question: "Can I use my own Anthropic API key?",
    answer:
      "Yes, bring your own key for the free tier. This lets you use the full AI capabilities without any per-query charges from us.",
  },
  {
    question: "What file formats do you support?",
    answer:
      "CSV, XLSX, TSV, FCS, TIFF, PNG, PDF and more. We're continuously adding support for additional instrument-specific formats.",
  },
  {
    question: "Do you support my liquid handler?",
    answer:
      "We generate worklists for Echo, Hamilton, and Opentrons. More integrations are coming soon. Contact us if you need a specific instrument.",
  },
  {
    question: "Is my data secure?",
    answer:
      "All data stays local in the demo. Cloud deployment uses encrypted storage with SOC 2-compliant infrastructure. Your experimental data is never used for model training.",
  },
];

function FaqItem({
  question,
  answer,
  delay,
}: {
  question: string;
  answer: string;
  delay: number;
}) {
  const [open, setOpen] = useState(false);

  return (
    <AnimatedSection delay={delay}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left p-6 rounded-2xl bg-surface border border-border hover:border-amber/30 transition-all duration-300"
      >
        <div className="flex items-start justify-between gap-4">
          <h3 className="font-medium text-charcoal">{question}</h3>
          <ChevronDown
            size={18}
            className={`text-muted shrink-0 mt-0.5 transition-transform duration-300 ${
              open ? "rotate-180" : ""
            }`}
          />
        </div>
        <motion.div
          initial={false}
          animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <p className="text-sm text-muted leading-relaxed mt-3">{answer}</p>
        </motion.div>
      </button>
    </AnimatedSection>
  );
}

export default function PricingPage() {
  return (
    <>
      <Navbar />
      <main className="pt-24">
        {/* Header */}
        <section className="relative max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-amber/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-1/3 right-0 w-80 h-80 bg-amber/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-3xl mx-auto text-center">
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="font-serif text-4xl sm:text-5xl lg:text-6xl font-semibold leading-[1.1] tracking-tight mb-6"
            >
              Simple, transparent
              <br />
              <span className="text-gradient">pricing</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.35 }}
              className="text-lg sm:text-xl text-muted leading-relaxed"
            >
              Start free. Scale as you grow.
            </motion.p>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 pb-20 lg:pb-28">
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {tiers.map((tier, i) => (
              <AnimatedSection key={tier.name} delay={i * 0.12}>
                <div
                  className={`relative flex flex-col h-full p-8 rounded-2xl border transition-all duration-500 ${
                    tier.featured
                      ? "bg-surface border-amber/50 shadow-lg shadow-amber/5"
                      : "bg-surface border-border hover:border-amber/30"
                  }`}
                >
                  {tier.featured && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="inline-flex items-center px-4 py-1 rounded-full bg-amber text-white text-xs font-medium tracking-wide">
                        Most popular
                      </span>
                    </div>
                  )}

                  <div className="mb-6">
                    <h3 className="font-serif text-xl font-semibold mb-2">
                      {tier.name}
                    </h3>
                    <p className="text-sm text-muted mb-4">{tier.description}</p>
                    <div className="flex items-baseline gap-1">
                      <span className="font-serif text-4xl font-semibold tracking-tight">
                        {tier.price}
                      </span>
                      {tier.period && (
                        <span className="text-sm text-muted">{tier.period}</span>
                      )}
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check
                          size={16}
                          className="text-amber shrink-0 mt-0.5"
                        />
                        <span className="text-sm text-muted">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={tier.ctaHref}
                    className={`inline-flex items-center justify-center px-6 py-3 text-sm font-medium rounded-full transition-all duration-300 ${
                      tier.featured
                        ? "bg-charcoal text-cream hover:bg-charcoal-light shadow-lg shadow-charcoal/10"
                        : "border border-border text-charcoal hover:border-amber hover:bg-amber/5"
                    }`}
                  >
                    {tier.cta}
                  </Link>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </section>

        {/* Decorative divider */}
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        {/* FAQ Section */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <AnimatedSection className="text-center mb-14">
            <h2 className="font-serif text-3xl sm:text-4xl font-semibold tracking-tight mb-4">
              Frequently asked questions
            </h2>
            <p className="text-lg text-muted">
              Everything you need to know about Resonantia.
            </p>
          </AnimatedSection>

          <div className="max-w-2xl mx-auto space-y-4">
            {faqs.map((faq, i) => (
              <FaqItem
                key={faq.question}
                question={faq.question}
                answer={faq.answer}
                delay={i * 0.1}
              />
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

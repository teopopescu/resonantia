"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Repeat, Database, TrendingUp } from "lucide-react";

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

const capabilities = [
  {
    icon: Repeat,
    title: "Automate repetitive lab workflows",
    description:
      "Generate plate maps, create worklists for liquid handlers, and map source-to-destination plates in seconds instead of hours. No more copy-pasting between spreadsheets.",
  },
  {
    icon: Database,
    title: "Integrate instruments and data in one place",
    description:
      "Connect microscopy images, plate reader output, sample inventories, and qPCR data into a single intelligent workspace. Stop switching between six different tools.",
  },
  {
    icon: TrendingUp,
    title: "Accelerate analysis",
    description:
      "Fit dose-response curves, normalize plate data, analyze qPCR results, and generate publication-ready figures with AI-assisted pipelines that understand your experiments.",
  },
];

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main className="pt-24">
        {/* Hero Section */}
        <section className="relative max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-amber/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-1/3 right-0 w-80 h-80 bg-amber/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-3xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface border border-border text-sm text-muted mb-8"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber" />
              Our story
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="font-serif text-4xl sm:text-5xl lg:text-6xl font-semibold leading-[1.1] tracking-tight mb-6"
            >
              Built by scientists,
              <br />
              <span className="text-gradient">for scientists</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.45 }}
              className="text-lg sm:text-xl text-muted leading-relaxed max-w-2xl mx-auto"
            >
              Resonantia replaces the fragmented toolchain that every wet-lab
              scientist knows too well — the Excel plate maps, the disconnected
              LIMS, the separate instrument software — with a single AI-powered
              platform that actually understands your experiments.
            </motion.p>
          </div>
        </section>

        {/* Decorative divider */}
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        {/* Mission Section */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-3xl mx-auto">
            <AnimatedSection>
              <h2 className="font-serif text-3xl sm:text-4xl font-semibold tracking-tight mb-8">
                Our mission
              </h2>
            </AnimatedSection>

            <AnimatedSection delay={0.1}>
              <p className="text-lg text-muted leading-relaxed mb-6">
                Resonantia was founded on a simple observation: wet-lab scientists
                spend more time wrangling data than doing science. Between
                formatting plate maps in Excel, manually transferring results
                between instruments, and stitching together analysis scripts,
                researchers lose hours every day to work that should be automated.
              </p>
            </AnimatedSection>

            <AnimatedSection delay={0.2}>
              <p className="text-lg text-muted leading-relaxed mb-6">
                We believe every lab scientist deserves an intelligent
                collaborator — one that remembers your plate layouts, understands
                your assay protocols, connects directly to your instruments, and
                handles the repetitive data processing so you can focus on the
                science that matters.
              </p>
            </AnimatedSection>

            <AnimatedSection delay={0.3}>
              <div className="mt-10 p-6 rounded-2xl bg-surface border border-border">
                <p className="text-base text-muted leading-relaxed italic">
                  &ldquo;The best tool is the one that disappears. Resonantia should
                  feel less like software and more like having a brilliant lab
                  manager who never sleeps, never forgets a sample, and always
                  has the right analysis ready.&rdquo;
                </p>
              </div>
            </AnimatedSection>
          </div>
        </section>

        {/* Decorative divider */}
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        {/* What We Do Section */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <AnimatedSection className="text-center mb-16">
            <h2 className="font-serif text-3xl sm:text-4xl font-semibold tracking-tight mb-4">
              What we do
            </h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Three core capabilities that transform how lab scientists work.
            </p>
          </AnimatedSection>

          <div className="grid md:grid-cols-3 gap-8">
            {capabilities.map((cap, i) => (
              <AnimatedSection key={cap.title} delay={i * 0.15}>
                <div className="group p-8 rounded-2xl bg-surface border border-border hover:border-amber/40 transition-all duration-500 h-full">
                  <div className="w-12 h-12 rounded-xl bg-amber/10 flex items-center justify-center mb-6 group-hover:bg-amber/20 transition-colors duration-300">
                    <cap.icon size={22} className="text-amber" />
                  </div>
                  <h3 className="font-serif text-xl font-semibold mb-3">
                    {cap.title}
                  </h3>
                  <p className="text-sm text-muted leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </section>

        {/* Decorative divider */}
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        {/* Team Section */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-3xl mx-auto text-center">
            <AnimatedSection>
              <h2 className="font-serif text-3xl sm:text-4xl font-semibold tracking-tight mb-12">
                The team
              </h2>
            </AnimatedSection>

            <AnimatedSection delay={0.1}>
              <div className="inline-flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-amber/10 border-2 border-amber/30 flex items-center justify-center mb-5">
                  <span className="font-serif text-2xl font-semibold text-amber">
                    TP
                  </span>
                </div>
                <h3 className="font-serif text-xl font-semibold mb-1">
                  Teodor Popescu
                </h3>
                <p className="text-sm text-muted mb-4">Founder</p>
                <p className="text-base text-muted leading-relaxed max-w-lg">
                  Scientist and engineer with a passion for building tools that
                  help researchers spend less time on data plumbing and more time
                  on discovery.
                </p>
              </div>
            </AnimatedSection>

            <AnimatedSection delay={0.2}>
              <div className="mt-14 p-6 rounded-2xl bg-surface border border-border inline-block">
                <p className="text-base font-medium text-charcoal mb-2">
                  We&apos;re hiring
                </p>
                <p className="text-sm text-muted mb-4">
                  Interested in building the future of lab informatics?
                </p>
                <a
                  href="mailto:hello@resonantia.io"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-charcoal text-cream text-sm font-medium rounded-full hover:bg-charcoal-light transition-colors duration-300"
                >
                  Get in touch
                </a>
              </div>
            </AnimatedSection>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

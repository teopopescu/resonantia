"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export function CtaSection() {
  return (
    <section className="relative py-24 lg:py-32 border-t border-line overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative max-w-4xl mx-auto px-6 lg:px-8 text-center"
      >
        {/* Decorative line */}
        <div className="w-12 h-px bg-brand mx-auto mb-10" />

        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] mb-6">
          Generate the worklist<br />scientists trust to run.
        </h2>

        <p className="text-lg text-ink-muted leading-relaxed max-w-xl mx-auto mb-10">
          Turn assay intent into validated, approval-gated worklists for Echo,
          Hamilton, and Opentrons, then connect results back to your records.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <a
            href="mailto:hello@resonantia.io?subject=Resonantia · Design partner inquiry"
            className="group inline-flex items-center gap-2 px-6 py-3 bg-brand text-white text-sm font-medium rounded-[3px] hover:bg-brand-strong transition-colors duration-200"
            style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
          >
            Contact us
            <ArrowRight
              size={15}
              className="group-hover:translate-x-0.5 transition-transform"
            />
          </a>
          <Link
            href="/use-cases"
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors duration-200"
          >
            See use cases
          </Link>
        </div>
      </motion.div>
    </section>
  );
}

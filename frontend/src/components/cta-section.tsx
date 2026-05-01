"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight } from "lucide-react";

export function CtaSection() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section className="relative py-28 lg:py-36 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber/5 rounded-full blur-3xl" />
      </div>

      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 40 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.7 }}
        className="relative max-w-4xl mx-auto px-6 lg:px-8 text-center"
      >
        {/* Decorative line */}
        <div className="w-12 h-px bg-amber mx-auto mb-10" />

        <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight mb-6">
          The New Way Labs Work
        </h2>

        <p className="text-lg text-muted leading-relaxed max-w-xl mx-auto mb-10">
          Design plate maps, fit dose-response curves, browse microscopy data,
          and track samples — all from one AI-powered interface. Start free today.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/lab"
            className="group inline-flex items-center gap-2 px-8 py-4 bg-charcoal text-cream text-sm font-medium rounded-full hover:bg-charcoal-light transition-all duration-300 shadow-lg shadow-charcoal/10"
          >
            Get started for free
            <ArrowRight
              size={16}
              className="group-hover:translate-x-0.5 transition-transform"
            />
          </Link>
          <a
            href="mailto:hello@resonantia.io"
            className="inline-flex items-center gap-2 px-8 py-4 text-sm font-medium text-charcoal border border-border rounded-full hover:border-amber hover:bg-amber/5 transition-all duration-300"
          >
            Contact sales
          </a>
        </div>
      </motion.div>
    </section>
  );
}

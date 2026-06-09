"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const footerLinks = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "Use cases", href: "/use-cases" },
    { label: "Pricing", href: "/pricing" },
  ],
  Connect: [
    { label: "Contact us", href: "mailto:hello@resonantia.io?subject=Resonantia · contact" },
    { label: "Feedback", href: "https://forms.gle/resonantia-feedback" },
  ],
};

export function Footer() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <motion.footer
      ref={ref}
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : {}}
      transition={{ duration: 0.8 }}
      className="border-t border-border bg-surface"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-10 lg:gap-12">
          {/* Brand column */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2.5 mb-4">
              <span
                className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[4px] rounded-[4px] bg-surface border border-line-strong"
                style={{ width: 26, height: 26 }}
                aria-hidden="true"
              >
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-brand" />
              </span>
              <span className="text-lg font-semibold tracking-[-0.02em] text-ink">
                Resonantia
              </span>
            </Link>
            <p className="text-sm text-muted leading-relaxed max-w-xs mb-6">
              Execution layer for validated plate maps, liquid-handler
              worklists, result ingestion, and auditable run records.
            </p>
            <p className="text-xs text-muted/60">
              &copy; {new Date().getFullYear()} Resonantia. All rights reserved.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-xs font-medium uppercase tracking-[0.15em] text-charcoal mb-4">
                {category}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-muted hover:text-charcoal transition-colors duration-300"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </motion.footer>
  );
}

"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const footerLinks = {
  Product: [
    { label: "About", href: "/about" },
    { label: "Features", href: "#features" },
    { label: "Pricing", href: "/pricing" },
    { label: "Request a Feature", href: "/feature-request" },
  ],
  Research: [
    { label: "Blog", href: "/blog" },
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
              <div className="relative w-7 h-7">
                <svg
                  viewBox="0 0 32 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-full h-full"
                >
                  <path
                    d="M8 4C8 4 12 10 16 16C20 22 24 28 24 28"
                    stroke="#D4A843"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M24 4C24 4 20 10 16 16C12 22 8 28 8 28"
                    stroke="#1A1A1A"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <circle cx="16" cy="16" r="2" fill="#D4A843" opacity="0.6" />
                </svg>
              </div>
              <span className="font-serif text-lg font-semibold text-charcoal">
                Resonantia
              </span>
            </Link>
            <p className="text-sm text-muted leading-relaxed max-w-xs mb-6">
              AI-powered plate mapping, dose-response fitting, microscopy
              browsing, and sample tracking. Built by scientists, for scientists.
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

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

function HeroBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Gradient orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-amber/10 rounded-full blur-3xl" />
      <div className="absolute top-1/3 right-0 w-80 h-80 bg-amber/5 rounded-full blur-3xl" />

      {/* Grid pattern */}
      <div className="absolute inset-0 grid-pattern opacity-60" />

      {/* Decorative circles */}
      <svg
        className="absolute top-20 right-[15%] w-64 h-64 text-amber/10"
        viewBox="0 0 200 200"
        fill="none"
      >
        <circle cx="100" cy="100" r="80" stroke="currentColor" strokeWidth="0.5" />
        <circle cx="100" cy="100" r="60" stroke="currentColor" strokeWidth="0.5" />
        <circle cx="100" cy="100" r="40" stroke="currentColor" strokeWidth="0.5" />
        <circle cx="100" cy="100" r="20" stroke="currentColor" strokeWidth="0.5" />
      </svg>

      {/* DNA strand decorative */}
      <svg
        className="absolute bottom-20 left-[10%] w-48 h-96 text-amber/8 hidden lg:block"
        viewBox="0 0 80 300"
        fill="none"
      >
        {[0, 40, 80, 120, 160, 200, 240].map((y) => (
          <g key={y}>
            <path
              d={`M20 ${y} Q40 ${y + 10} 60 ${y + 20}`}
              stroke="currentColor"
              strokeWidth="0.8"
            />
            <path
              d={`M60 ${y} Q40 ${y + 10} 20 ${y + 20}`}
              stroke="currentColor"
              strokeWidth="0.8"
            />
            <circle cx="20" cy={y} r="2" fill="currentColor" opacity="0.4" />
            <circle cx="60" cy={y} r="2" fill="currentColor" opacity="0.4" />
          </g>
        ))}
      </svg>

      {/* Microwell plate decorative */}
      <svg
        className="absolute top-40 right-[8%] w-40 h-32 text-border hidden xl:block"
        viewBox="0 0 160 120"
        fill="none"
      >
        <rect x="0" y="0" width="160" height="120" rx="4" stroke="currentColor" strokeWidth="0.5" />
        {Array.from({ length: 8 }, (_, row) =>
          Array.from({ length: 12 }, (_, col) => (
            <circle
              key={`${row}-${col}`}
              cx={10 + col * 12.5}
              cy={10 + row * 13}
              r="3.5"
              stroke="currentColor"
              strokeWidth="0.3"
              fill={
                (row + col) % 7 === 0
                  ? "rgba(212,168,67,0.15)"
                  : "none"
              }
            />
          ))
        )}
      </svg>
    </div>
  );
}

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-18">
      <HeroBackground />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8 py-24 lg:py-32">
        <div className="max-w-3xl mx-auto text-center">
          {/* Pill badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface border border-border text-sm text-muted mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse" />
            Now in early access
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="font-serif text-5xl sm:text-6xl lg:text-7xl font-semibold leading-[1.1] tracking-tight mb-6"
          >
            Agentic OS for
            <br />
            <span className="text-gradient">Lab Informatics</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45 }}
            className="text-lg sm:text-xl text-muted leading-relaxed max-w-2xl mx-auto mb-10"
          >
            AI-powered plate mapping, dose-response analysis, and sample
            tracking for lab scientists. Design worklists, browse microscopy
            data, and manage reagent inventory — from one intelligent interface.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/lab"
              className="group inline-flex items-center gap-2 px-7 py-3.5 bg-charcoal text-cream text-sm font-medium rounded-full hover:bg-charcoal-light transition-all duration-300 shadow-lg shadow-charcoal/10"
            >
              Try Resonantia Lab
              <ArrowRight
                size={16}
                className="group-hover:translate-x-0.5 transition-transform"
              />
            </Link>
            <a
              href="/about"
              className="group inline-flex items-center gap-2 px-7 py-3.5 text-sm font-medium text-charcoal border border-border rounded-full hover:border-amber hover:bg-amber/5 transition-all duration-300"
            >
              Read our vision
              <ArrowRight
                size={16}
                className="group-hover:translate-x-0.5 transition-transform text-amber"
              />
            </a>
          </motion.div>
        </div>

        {/* Decorative line */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.2, delay: 1 }}
          className="mt-24 h-px bg-gradient-to-r from-transparent via-border to-transparent"
        />
      </div>
    </section>
  );
}

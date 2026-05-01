"use client";

import { motion } from "framer-motion";
import { Quote } from "lucide-react";

const testimonials = [
  {
    quote:
      "We design 384-well plate maps and generate Echo worklists in minutes now. What used to be a full afternoon of spreadsheet wrangling is a single chat prompt.",
    author: "Principal Scientist",
    role: "Drug Discovery",
    org: "Top 20 Pharma",
    initials: "PS",
  },
  {
    quote:
      "The dose-response fitting is spot on. I paste in my raw reads, get IC50 curves back with Z-prime scores and percent-of-control normalization — no more juggling GraphPad and Excel.",
    author: "Head of Screening",
    role: "HTS & Assay Development",
    org: "Series B Biotech",
    initials: "HS",
  },
  {
    quote:
      "Browsing microscopy FOVs by well, plate, and channel in one place replaced three separate tools for us. The barcode-linked sample inventory is the cherry on top.",
    author: "Imaging Core Lead",
    role: "High-Content Screening",
    org: "Academic Research Institute",
    initials: "IC",
  },
];

function TestimonialCard({
  testimonial,
  index,
}: {
  testimonial: (typeof testimonials)[number];
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      className="relative p-8 lg:p-9 rounded-md bg-surface border border-line"
    >
      {/* Quote icon */}
      <Quote size={20} className="text-brand/40 mb-5" />

      {/* Quote text */}
      <p className="text-[15px] leading-relaxed text-ink mb-7">
        &ldquo;{testimonial.quote}&rdquo;
      </p>

      {/* Author */}
      <div className="flex items-center gap-3 pt-5 border-t border-dashed border-line">
        <div className="w-9 h-9 rounded-full bg-bg border border-line flex items-center justify-center text-[11px] font-mono font-medium text-ink-muted">
          {testimonial.initials}
        </div>
        <div>
          <p className="text-[13.5px] font-medium text-ink">
            {testimonial.author}
          </p>
          <p className="text-[11.5px] font-mono uppercase tracking-[0.04em] text-ink-subtle mt-0.5">
            {testimonial.role} &middot; {testimonial.org}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function Testimonials() {
  return (
    <section className="relative py-24 lg:py-32 border-t border-line">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl mb-14"
        >
          <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
            <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
              04
            </span>
            <span>From the bench</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink">
            What scientists say<br />about the <span className="text-brand">console.</span>
          </h2>
        </motion.div>

        {/* Testimonial cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, i) => (
            <TestimonialCard
              key={testimonial.author}
              testimonial={testimonial}
              index={i}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

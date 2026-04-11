"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Quote } from "lucide-react";

const testimonials = [
  {
    quote:
      "We design 384-well plate maps and generate Echo worklists in minutes now. What used to be a full afternoon of spreadsheet wrangling is a single chat prompt.",
    author: "Dr. Sarah Chen",
    role: "Principal Scientist",
    org: "Vertex Therapeutics",
    initials: "SC",
  },
  {
    quote:
      "The dose-response fitting is spot on. I paste in my raw reads, get IC50 curves back with Z-prime scores and percent-of-control normalization — no more juggling GraphPad and Excel.",
    author: "Dr. Marcus Rivera",
    role: "Head of Screening",
    org: "Novaris Biotech",
    initials: "MR",
  },
  {
    quote:
      "Browsing microscopy FOVs by well, plate, and channel in one place replaced three separate tools for us. The barcode-linked sample inventory is the cherry on top.",
    author: "Dr. Anya Petrov",
    role: "Imaging Core Lead",
    org: "Cambridge Research Institute",
    initials: "AP",
  },
];

function TestimonialCard({
  testimonial,
  index,
}: {
  testimonial: (typeof testimonials)[number];
  index: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.15 }}
      className="relative p-8 lg:p-10 rounded-2xl bg-surface border border-border/60"
    >
      {/* Quote icon */}
      <Quote size={24} className="text-amber/30 mb-6" />

      {/* Quote text */}
      <p className="text-base leading-relaxed text-charcoal-light mb-8 font-light italic">
        &ldquo;{testimonial.quote}&rdquo;
      </p>

      {/* Author */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-cream-dark border border-border flex items-center justify-center text-xs font-medium text-muted">
          {testimonial.initials}
        </div>
        <div>
          <p className="text-sm font-medium text-charcoal">
            {testimonial.author}
          </p>
          <p className="text-xs text-muted">
            {testimonial.role}, {testimonial.org}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function Testimonials() {
  const headingRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(headingRef, { once: true, margin: "-80px" });

  return (
    <section className="relative py-28 lg:py-36 bg-cream-dark/30">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          ref={headingRef}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="max-w-2xl mx-auto text-center mb-16"
        >
          <span className="inline-block text-xs font-medium uppercase tracking-[0.2em] text-amber mb-4">
            Testimonials
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight">
            Trusted by researchers
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

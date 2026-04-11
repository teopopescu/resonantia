"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  LayoutGrid,
  Microscope,
  LineChart,
  FlaskConical,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";

const features = [
  {
    icon: LayoutGrid,
    title: "Intelligent Plate Mapping",
    description:
      "Source-destination plate design with worklist generation for any liquid handler. Drag, drop, and let AI optimize your layouts.",
  },
  {
    icon: Microscope,
    title: "Microscopy Image Browser",
    description:
      "Browse FOV images by well, plate, and channel with smart overlays. Navigate terabytes of imaging data effortlessly.",
  },
  {
    icon: LineChart,
    title: "Automated Data Processing",
    description:
      "Dose-response curves, plate normalization, qPCR analysis — all automated. From raw data to publication-ready figures in seconds.",
  },
  {
    icon: FlaskConical,
    title: "Sample & Reagent Tracking",
    description:
      "Track every lot, every freeze-thaw, every storage location. Full chain of custody with barcode and RFID integration.",
  },
  {
    icon: MessageSquare,
    title: "Natural Language Queries",
    description:
      "Ask your data anything. Get tables, figures, and insights conversationally. No SQL required — just plain English.",
  },
  {
    icon: ShieldCheck,
    title: "Full Activity Logging",
    description:
      "Every action, upload, and analysis is timestamped and logged. Transparent history of who did what, when, and with which parameters.",
  },
];

function FeatureCard({
  feature,
  index,
}: {
  feature: (typeof features)[number];
  index: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      className="group relative p-8 rounded-2xl bg-surface border border-border/60 hover:border-amber/40 transition-all duration-500 hover:shadow-lg hover:shadow-amber/5"
    >
      {/* Subtle gradient on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-amber/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative">
        {/* Icon */}
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-cream-dark border border-border/60 mb-5 group-hover:border-amber/30 group-hover:bg-amber/10 transition-all duration-500">
          <feature.icon
            size={22}
            className="text-muted group-hover:text-amber transition-colors duration-500"
          />
        </div>

        {/* Title */}
        <h3 className="font-serif text-lg font-semibold mb-3 text-charcoal">
          {feature.title}
        </h3>

        {/* Description */}
        <p className="text-sm leading-relaxed text-muted">
          {feature.description}
        </p>
      </div>
    </motion.div>
  );
}

export function Features() {
  const headingRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(headingRef, { once: true, margin: "-80px" });

  return (
    <section id="features" className="relative py-28 lg:py-36">
      {/* Background */}
      <div className="absolute inset-0 dot-pattern opacity-40 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          ref={headingRef}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="max-w-2xl mx-auto text-center mb-16 lg:mb-20"
        >
          <span className="inline-block text-xs font-medium uppercase tracking-[0.2em] text-amber mb-4">
            Platform
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight mb-6">
            The first Agentic Lab
            <br />
            Informatics Platform
          </h2>
          <p className="text-lg text-muted leading-relaxed">
            A unified workspace where AI agents and scientists collaborate.
            Every tool you need, intelligently connected, in one interface.
          </p>
        </motion.div>

        {/* Feature cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <FeatureCard key={feature.title} feature={feature} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

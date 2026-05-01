"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * KpiStrip + Kpi — instrument-readout KPI tiles.
 * Pattern from the v4 mockup: tabular display number, mono uppercase
 * label, mono delta. Optional href turns the tile into a filter link.
 */

type Tone = "default" | "brand" | "bf" | "mch" | "gfp" | "dapi";

const toneClass: Record<Tone, string> = {
  default: "text-ink",
  brand: "text-brand",
  bf: "text-bf",
  mch: "text-mch",
  gfp: "text-gfp",
  dapi: "text-dapi",
};

interface KpiProps {
  label: string;
  value: React.ReactNode;
  delta?: React.ReactNode;
  tone?: Tone;
  href?: string;
}

export function Kpi({ label, value, delta, tone = "default", href }: KpiProps) {
  const inner = (
    <div className="px-6 py-5 h-full transition-colors group-hover:bg-bg-sunk">
      <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
        {label}
      </div>
      <div
        className={cn(
          "mt-2 font-semibold text-[36px] leading-none tracking-[-0.04em] tabular-nums",
          toneClass[tone]
        )}
      >
        {value}
      </div>
      {delta && (
        <div className="mt-2 font-mono text-[11px] tracking-[0.02em] text-ink-muted">
          {delta}
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="group block border-r border-line last:border-r-0">
        {inner}
      </Link>
    );
  }
  return <div className="group border-r border-line last:border-r-0">{inner}</div>;
}

interface KpiStripProps {
  /** Number of columns at lg breakpoint. Defaults to children count. */
  columns?: 2 | 3 | 4 | 5;
  children: React.ReactNode;
  className?: string;
}

const colsClass: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4",
  5: "lg:grid-cols-5",
};

export function KpiStrip({ columns = 4, children, className }: KpiStripProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-2",
        colsClass[columns],
        "border-b border-line bg-surface",
        className
      )}
    >
      {children}
    </div>
  );
}

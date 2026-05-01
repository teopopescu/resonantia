"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * PageHeader — top of every lab tool page.
 * Pattern from the v4 mockup: marker eyebrow, title, mono meta line,
 * actions slot on the right, hairline border below.
 */

interface PageHeaderProps {
  /** Optional 2-digit marker like "03" rendered in a forest badge. */
  marker?: string;
  /** Eyebrow label rendered after the marker, e.g. "Plates · designer". */
  markerLabel?: string;
  /** Page title (no serif, semibold, tight tracking). */
  title: React.ReactNode;
  /** Mono meta line under the title. Wrap accent values in <em> with class `text-brand`. */
  meta?: React.ReactNode;
  /** Right-aligned actions slot — buttons, segmented control, etc. */
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  marker,
  markerLabel,
  title,
  meta,
  children,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex items-end justify-between gap-6 px-6 lg:px-8 py-6 border-b border-line bg-bg",
        className
      )}
    >
      <div className="min-w-0">
        {(marker || markerLabel) && (
          <div className="inline-flex items-center gap-2.5 mb-3 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
            {marker && (
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                {marker}
              </span>
            )}
            {markerLabel && <span>{markerLabel}</span>}
          </div>
        )}
        <h1 className="text-[22px] sm:text-[24px] font-semibold tracking-[-0.02em] leading-[1.15] text-ink">
          {title}
        </h1>
        {meta && (
          <div className="mt-1.5 font-mono text-[11.5px] tracking-[0.04em] uppercase text-ink-muted">
            {meta}
          </div>
        )}
      </div>

      {children && (
        <div className="flex items-center gap-2 shrink-0">{children}</div>
      )}
    </header>
  );
}

/* ── Sharable button styles for action slots ── */

export function PageHeaderPrimary({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center gap-2 px-3.5 py-2 bg-brand text-white text-[13px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors",
        props.className
      )}
      style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)", ...props.style }}
    >
      {children}
    </button>
  );
}

export function PageHeaderGhost({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center gap-2 px-3 py-2 text-[13px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors",
        props.className
      )}
    >
      {children}
    </button>
  );
}

/* ── Segmented control (e.g. plate-size toggle) ── */

interface SegmentedControlProps<T extends string> {
  options: Array<{ label: string; value: T }>;
  value: T;
  onChange: (value: T) => void;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="inline-flex p-0.5 border border-line bg-bg rounded-[3px]">
      {options.map((opt) => {
        const isOn = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              "px-2.5 py-1 font-mono text-[11.5px] tracking-[0.02em] rounded-[2px] transition-colors",
              isOn
                ? "bg-surface text-brand"
                : "text-ink-muted hover:text-ink"
            )}
            style={
              isOn ? { boxShadow: "0 0 0 1px var(--color-brand-soft)" } : undefined
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

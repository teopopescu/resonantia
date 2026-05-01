"use client";

import * as React from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, Check, Search } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * DataTable — generic v4 table primitive.
 * Hairline rules, sticky mono header, monoposable columns,
 * optional selection, optional sort, optional row click.
 *
 * Used by Samples · Plates · Microscopy · Processing.
 */

export type Column<T> = {
  key: string;
  label: string;
  /** column width — px, fr, percentage, "auto", etc. */
  width?: string;
  align?: "left" | "right";
  /** render the cell value in JetBrains Mono */
  mono?: boolean;
  sortable?: boolean;
  render?: (row: T, index: number) => React.ReactNode;
  /** fallback when render is not provided — pluck this field name */
  field?: keyof T;
};

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  selectable?: boolean;
  selectedKeys?: string[];
  onSelectionChange?: (keys: string[]) => void;
  onRowClick?: (row: T, index: number) => void;
  sortKey?: string;
  sortDir?: "asc" | "desc";
  onSortChange?: (key: string, dir: "asc" | "desc") => void;
  toolbar?: React.ReactNode;
  footer?: React.ReactNode;
  emptyState?: React.ReactNode;
  className?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  selectable,
  selectedKeys = [],
  onSelectionChange,
  onRowClick,
  sortKey,
  sortDir,
  onSortChange,
  toolbar,
  footer,
  emptyState,
  className,
}: DataTableProps<T>) {
  const allKeys = rows.map(rowKey);
  const allSelected = rows.length > 0 && allKeys.every((k) => selectedKeys.includes(k));
  const someSelected = !allSelected && selectedKeys.some((k) => allKeys.includes(k));

  const toggleAll = () => {
    if (!onSelectionChange) return;
    if (allSelected) onSelectionChange([]);
    else onSelectionChange(allKeys);
  };

  const toggleOne = (k: string) => {
    if (!onSelectionChange) return;
    if (selectedKeys.includes(k)) onSelectionChange(selectedKeys.filter((x) => x !== k));
    else onSelectionChange([...selectedKeys, k]);
  };

  const handleSort = (col: Column<T>) => {
    if (!col.sortable || !onSortChange) return;
    if (sortKey === col.key) {
      onSortChange(col.key, sortDir === "asc" ? "desc" : "asc");
    } else {
      onSortChange(col.key, "asc");
    }
  };

  return (
    <div
      className={cn(
        "border border-line rounded-[5px] overflow-hidden bg-surface flex flex-col min-h-0",
        className
      )}
    >
      {toolbar && (
        <div className="flex items-center gap-2 px-3 py-2 border-b border-line bg-bg">
          {toolbar}
        </div>
      )}

      <div className="flex-1 overflow-auto min-h-0">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-bg z-10">
            <tr>
              {selectable && (
                <th className="w-9 pl-4 pr-1 py-2.5 border-b border-line text-left">
                  <Checkbox
                    checked={allSelected}
                    indeterminate={someSelected}
                    onChange={toggleAll}
                  />
                </th>
              )}
              {columns.map((col) => {
                const active = sortKey === col.key;
                return (
                  <th
                    key={col.key}
                    className={cn(
                      "px-3 py-2.5 border-b border-line font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle",
                      col.align === "right" ? "text-right" : "text-left"
                    )}
                    style={col.width ? { width: col.width } : undefined}
                  >
                    {col.sortable ? (
                      <button
                        onClick={() => handleSort(col)}
                        className="inline-flex items-center gap-1 hover:text-ink transition-colors group"
                      >
                        <span className={active ? "text-ink" : ""}>{col.label}</span>
                        {active ? (
                          sortDir === "asc" ? (
                            <ChevronUp size={12} className="text-brand" />
                          ) : (
                            <ChevronDown size={12} className="text-brand" />
                          )
                        ) : (
                          <ChevronsUpDown
                            size={12}
                            className="opacity-0 group-hover:opacity-60"
                          />
                        )}
                      </button>
                    ) : (
                      <span>{col.label}</span>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="text-center py-12 text-ink-muted"
                >
                  {emptyState || (
                    <span className="font-mono text-[12px] tracking-[0.02em]">
                      no rows
                    </span>
                  )}
                </td>
              </tr>
            ) : (
              rows.map((row, rowIndex) => {
                const k = rowKey(row);
                const isSelected = selectedKeys.includes(k);
                return (
                  <tr
                    key={k}
                    onClick={() => onRowClick?.(row, rowIndex)}
                    className={cn(
                      "border-b border-line last:border-b-0 transition-colors",
                      isSelected ? "bg-brand-soft/40" : "hover:bg-bg",
                      onRowClick && "cursor-pointer"
                    )}
                  >
                    {selectable && (
                      <td className="w-9 pl-4 pr-1 py-3" onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={isSelected}
                          onChange={() => toggleOne(k)}
                        />
                      </td>
                    )}
                    {columns.map((col) => {
                      const value =
                        col.render
                          ? col.render(row, rowIndex)
                          : col.field
                          ? (row[col.field] as React.ReactNode)
                          : null;
                      return (
                        <td
                          key={col.key}
                          className={cn(
                            "px-3 py-3 text-[13px] text-ink align-middle",
                            col.align === "right" && "text-right",
                            col.mono &&
                              "font-mono text-[12px] tracking-[0.01em] text-ink-muted"
                          )}
                        >
                          {value}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {footer && (
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-t border-line bg-bg font-mono text-[11.5px] tracking-[0.02em] text-ink-subtle">
          {footer}
        </div>
      )}
    </div>
  );
}

/* ── Helpers ───────────────────────────────────────────────── */

function Checkbox({
  checked,
  indeterminate,
  onChange,
}: {
  checked: boolean;
  indeterminate?: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onChange}
      aria-checked={checked}
      role="checkbox"
      className={cn(
        "w-4 h-4 rounded-[3px] border flex items-center justify-center transition-colors",
        checked || indeterminate
          ? "bg-brand border-brand text-white"
          : "border-line-strong hover:border-ink bg-surface"
      )}
    >
      {checked && <Check size={11} />}
      {!checked && indeterminate && <span className="block w-2 h-px bg-white" />}
    </button>
  );
}

/* ── Cell helpers ──────────────────────────────────────────── */

export function NameCell({
  primary,
  secondary,
}: {
  primary: React.ReactNode;
  secondary?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col">
      <span className="text-[13.5px] font-medium text-ink leading-snug">{primary}</span>
      {secondary && (
        <span className="font-mono text-[11px] text-ink-subtle mt-0.5 tracking-[0.02em]">
          {secondary}
        </span>
      )}
    </div>
  );
}

type ChipTone = "default" | "brand" | "gfp" | "dapi" | "mch" | "bf";

const chipToneClass: Record<ChipTone, string> = {
  default: "bg-bg border border-line text-ink-muted",
  brand: "bg-brand-soft border border-brand/30 text-brand",
  gfp: "bg-gfp-soft border border-gfp/40 text-[#4D7600]",
  dapi: "bg-dapi-soft border border-dapi/30 text-dapi",
  mch: "bg-mch-soft border border-mch/30 text-mch",
  bf: "bg-bf-soft border border-bf/30 text-bf",
};

export function Chip({
  children,
  tone = "default",
  className,
}: {
  children: React.ReactNode;
  tone?: ChipTone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded-[2px] font-mono text-[10.5px] tracking-[0.02em] uppercase",
        chipToneClass[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

/* ── Toolbar helpers ──────────────────────────────────────── */

export function TableSearch({
  value,
  onChange,
  placeholder = "search…",
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <div className={cn("relative", className)}>
      <Search
        size={13}
        className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-subtle"
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-[280px] max-w-full pl-7 pr-3 py-1.5 font-mono text-[12px] rounded-[3px] border border-line bg-surface text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle"
      />
    </div>
  );
}

export function TableSelect<T extends string>({
  value,
  onChange,
  options,
  className,
}: {
  value: T;
  onChange: (v: T) => void;
  options: Array<{ label: string; value: T }>;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className={cn(
        "px-2.5 py-1.5 font-mono text-[11.5px] tracking-[0.02em] rounded-[3px] border border-line bg-surface text-ink-muted cursor-pointer hover:border-line-strong focus:outline-none focus:border-brand/40 transition-colors",
        className
      )}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function IconAction({
  icon: Icon,
  label,
  onClick,
}: {
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-2.5 py-1.5 font-mono text-[11.5px] tracking-[0.02em] uppercase rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
    >
      <Icon size={13} />
      {label}
    </button>
  );
}

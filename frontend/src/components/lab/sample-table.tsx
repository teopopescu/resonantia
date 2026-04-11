"use client";

import { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  Search,
  Download,
  Printer,
  Check,
} from "lucide-react";
import { useSampleStore } from "@/stores/sample-store";
import {
  SAMPLE_TYPE_LABELS,
  STATUS_CONFIG,
  type Sample,
  type SampleStatus,
  type SampleType,
} from "@/lib/demo-data";

type SortField = "name" | "type" | "expiryDate" | "quantity" | "status" | "addedDate";
type SortDir = "asc" | "desc";

export default function SampleTable() {
  const {
    samples,
    filters,
    selectedSamples,
    setFilters,
    toggleSelected,
    selectAll,
    clearSelection,
  } = useSampleStore();

  const [sortField, setSortField] = useState<SortField>("addedDate");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const filtered = useMemo(() => {
    let result = [...samples];

    if (filters.type !== "all") {
      result = result.filter((s) => s.type === filters.type);
    }
    if (filters.status !== "all") {
      result = result.filter((s) => s.status === filters.status);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.barcode.toLowerCase().includes(q) ||
          s.location.toLowerCase().includes(q) ||
          (s.supplier && s.supplier.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      switch (sortField) {
        case "name":
          return a.name.localeCompare(b.name) * dir;
        case "type":
          return a.type.localeCompare(b.type) * dir;
        case "expiryDate":
          return (new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()) * dir;
        case "quantity":
          return (a.quantity - b.quantity) * dir;
        case "status":
          return a.status.localeCompare(b.status) * dir;
        case "addedDate":
          return (new Date(a.addedDate).getTime() - new Date(b.addedDate).getTime()) * dir;
        default:
          return 0;
      }
    });

    return result;
  }, [samples, filters, sortField, sortDir]);

  const allSelected = filtered.length > 0 && filtered.every((s) => selectedSamples.includes(s.id));

  const handleSelectAll = () => {
    if (allSelected) {
      clearSelection();
    } else {
      selectAll(filtered.map((s) => s.id));
    }
  };

  const exportCSV = () => {
    const headers = ["Name", "Barcode", "Type", "Location", "Storage Temp", "Lot #", "Expiry", "Quantity", "Unit", "Status"];
    const rows = filtered.map((s) => [
      s.name, s.barcode, s.type, s.location, s.storageTemp, s.lotNumber, s.expiryDate, s.quantity, s.unit, s.status,
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "samples_export.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  function SortHeader({ field, children }: { field: SortField; children: React.ReactNode }) {
    const active = sortField === field;
    return (
      <button
        onClick={() => handleSort(field)}
        className="flex items-center gap-1 group"
      >
        <span className={active ? "text-charcoal font-semibold" : ""}>{children}</span>
        {active ? (
          sortDir === "asc" ? (
            <ChevronUp size={14} className="text-amber" />
          ) : (
            <ChevronDown size={14} className="text-amber" />
          )
        ) : (
          <ChevronsUpDown size={14} className="text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
        )}
      </button>
    );
  }

  function StatusBadge({ status }: { status: SampleStatus }) {
    const cfg = STATUS_CONFIG[status];
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
        {cfg.label}
      </span>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Filters & Actions bar */}
      <div className="flex items-center gap-3 px-5 py-3 bg-surface border-b border-border">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search samples, barcodes, suppliers..."
            value={filters.search}
            onChange={(e) => setFilters({ search: e.target.value })}
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors placeholder:text-muted"
          />
        </div>

        <select
          value={filters.type}
          onChange={(e) => setFilters({ type: e.target.value as SampleType | "all" })}
          className="px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
        >
          <option value="all">All Types</option>
          {Object.entries(SAMPLE_TYPE_LABELS).map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) => setFilters({ status: e.target.value as SampleStatus | "all" })}
          className="px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="expiring">Expiring</option>
          <option value="expired">Expired</option>
          <option value="low_stock">Low Stock</option>
        </select>

        <div className="flex-1" />

        {selectedSamples.length > 0 && (
          <span className="text-xs text-muted">
            {selectedSamples.length} selected
          </span>
        )}

        <button
          onClick={exportCSV}
          className="flex items-center gap-1.5 px-3 py-2 text-sm text-muted hover:text-charcoal rounded-lg hover:bg-cream-dark transition-colors"
        >
          <Download size={15} />
          Export
        </button>
        <button
          onClick={() => window.print()}
          className="flex items-center gap-1.5 px-3 py-2 text-sm text-muted hover:text-charcoal rounded-lg hover:bg-cream-dark transition-colors"
        >
          <Printer size={15} />
          Print
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-cream-dark/80 backdrop-blur-sm z-10">
            <tr className="text-left text-xs text-muted uppercase tracking-wider">
              <th className="pl-5 pr-2 py-3 w-10">
                <button
                  onClick={handleSelectAll}
                  className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                    allSelected
                      ? "bg-amber border-amber text-white"
                      : "border-border hover:border-muted"
                  }`}
                >
                  {allSelected && <Check size={12} />}
                </button>
              </th>
              <th className="px-3 py-3">
                <SortHeader field="name">Name</SortHeader>
              </th>
              <th className="px-3 py-3">Barcode</th>
              <th className="px-3 py-3">
                <SortHeader field="type">Type</SortHeader>
              </th>
              <th className="px-3 py-3">Location</th>
              <th className="px-3 py-3">Temp</th>
              <th className="px-3 py-3">Lot #</th>
              <th className="px-3 py-3">
                <SortHeader field="expiryDate">Expiry</SortHeader>
              </th>
              <th className="px-3 py-3">
                <SortHeader field="quantity">Qty</SortHeader>
              </th>
              <th className="px-3 py-3">
                <SortHeader field="status">Status</SortHeader>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {filtered.map((sample) => {
              const isSelected = selectedSamples.includes(sample.id);
              const isExpanded = expandedRow === sample.id;
              return (
                <RowGroup
                  key={sample.id}
                  sample={sample}
                  isSelected={isSelected}
                  isExpanded={isExpanded}
                  onToggleSelect={() => toggleSelected(sample.id)}
                  onToggleExpand={() =>
                    setExpandedRow(isExpanded ? null : sample.id)
                  }
                />
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={10} className="text-center py-12 text-muted">
                  No samples found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-5 py-2.5 bg-surface border-t border-border text-xs text-muted">
        Showing {filtered.length} of {samples.length} items
      </div>
    </div>
  );
}

function RowGroup({
  sample,
  isSelected,
  isExpanded,
  onToggleSelect,
  onToggleExpand,
}: {
  sample: Sample;
  isSelected: boolean;
  isExpanded: boolean;
  onToggleSelect: () => void;
  onToggleExpand: () => void;
}) {
  const cfg = STATUS_CONFIG[sample.status];
  return (
    <>
      <tr
        onClick={onToggleExpand}
        className={`cursor-pointer transition-colors ${
          isSelected
            ? "bg-amber/5"
            : isExpanded
            ? "bg-surface"
            : "hover:bg-surface"
        }`}
      >
        <td className="pl-5 pr-2 py-3">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleSelect();
            }}
            className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
              isSelected
                ? "bg-amber border-amber text-white"
                : "border-border hover:border-muted"
            }`}
          >
            {isSelected && <Check size={12} />}
          </button>
        </td>
        <td className="px-3 py-3 font-medium text-charcoal">{sample.name}</td>
        <td className="px-3 py-3 font-mono text-xs text-muted">{sample.barcode}</td>
        <td className="px-3 py-3 capitalize text-muted">
          {SAMPLE_TYPE_LABELS[sample.type]}
        </td>
        <td className="px-3 py-3 text-xs text-muted max-w-[200px] truncate">
          {sample.location}
        </td>
        <td className="px-3 py-3 text-xs text-muted">{sample.storageTemp}</td>
        <td className="px-3 py-3 font-mono text-xs text-muted">{sample.lotNumber}</td>
        <td className="px-3 py-3 text-xs text-muted">{sample.expiryDate}</td>
        <td className="px-3 py-3 text-xs text-muted">
          {sample.quantity} {sample.unit}
        </td>
        <td className="px-3 py-3">
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-surface">
          <td colSpan={10} className="px-5 py-4">
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-muted block mb-0.5">Supplier</span>
                <span className="text-charcoal font-medium">
                  {sample.supplier || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Catalog #</span>
                <span className="text-charcoal font-medium">
                  {sample.catalogNumber || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Date Added</span>
                <span className="text-charcoal font-medium">
                  {sample.addedDate}
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Full Location</span>
                <span className="text-charcoal font-medium">
                  {sample.location}
                </span>
              </div>
              {sample.notes && (
                <div className="col-span-2">
                  <span className="text-muted block mb-0.5">Notes</span>
                  <span className="text-charcoal font-medium font-mono">
                    {sample.notes}
                  </span>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

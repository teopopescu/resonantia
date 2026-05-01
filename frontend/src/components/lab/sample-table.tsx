"use client";

import { useState, useMemo } from "react";
import { Download, Printer } from "lucide-react";
import { useSampleStore } from "@/stores/sample-store";
import {
  SAMPLE_TYPE_LABELS,
  type Sample,
  type SampleStatus,
  type SampleType,
} from "@/lib/demo-data";
import {
  DataTable,
  Chip,
  NameCell,
  TableSearch,
  TableSelect,
  IconAction,
  type Column,
} from "./primitives/data-table";

type SortField = "name" | "type" | "expiryDate" | "quantity" | "status" | "addedDate";
type SortDir = "asc" | "desc";

const TYPE_TONE: Partial<Record<SampleType, "brand" | "gfp" | "dapi" | "mch" | "bf" | "default">> = {
  media: "dapi",
  buffer: "default",
  reagent: "gfp",
  compound: "brand",
  antibody: "mch",
  cell_line: "brand",
  enzyme: "gfp",
  primer: "default",
  plasmid: "dapi",
};

const STATUS_TONE: Record<SampleStatus, "brand" | "bf" | "mch" | "default"> = {
  active: "brand",
  expiring: "bf",
  low_stock: "mch",
  expired: "mch",
};

const STATUS_LABEL: Record<SampleStatus, string> = {
  active: "active",
  expiring: "expiring",
  expired: "expired",
  low_stock: "low stock",
};

export default function SampleTable() {
  const {
    samples,
    filters,
    selectedSamples,
    setFilters,
    selectAll,
    clearSelection,
  } = useSampleStore();

  const [sortField, setSortField] = useState<SortField>("addedDate");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

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
          return (
            (new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()) *
            dir
          );
        case "quantity":
          return (a.quantity - b.quantity) * dir;
        case "status":
          return a.status.localeCompare(b.status) * dir;
        case "addedDate":
          return (
            (new Date(a.addedDate).getTime() - new Date(b.addedDate).getTime()) *
            dir
          );
        default:
          return 0;
      }
    });

    return result;
  }, [samples, filters, sortField, sortDir]);

  const exportCSV = () => {
    const headers = [
      "Name",
      "Barcode",
      "Type",
      "Location",
      "Storage Temp",
      "Lot #",
      "Expiry",
      "Quantity",
      "Unit",
      "Status",
    ];
    const rows = filtered.map((s) => [
      s.name,
      s.barcode,
      s.type,
      s.location,
      s.storageTemp,
      s.lotNumber,
      s.expiryDate,
      s.quantity,
      s.unit,
      s.status,
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

  const columns: Column<Sample>[] = [
    {
      key: "name",
      label: "name",
      sortable: true,
      render: (s) => (
        <NameCell
          primary={s.name}
          secondary={
            <>
              {SAMPLE_TYPE_LABELS[s.type].toLowerCase()} · {s.quantity} {s.unit}
              {s.supplier && <> · {s.supplier}</>}
            </>
          }
        />
      ),
    },
    { key: "barcode", label: "barcode", mono: true, field: "barcode" },
    {
      key: "type",
      label: "type",
      sortable: true,
      render: (s) => (
        <Chip tone={TYPE_TONE[s.type] || "default"}>
          {SAMPLE_TYPE_LABELS[s.type].toLowerCase()}
        </Chip>
      ),
    },
    { key: "location", label: "location", mono: true, field: "location" },
    { key: "storageTemp", label: "temp", mono: true, field: "storageTemp" },
    { key: "lotNumber", label: "lot", mono: true, field: "lotNumber" },
    {
      key: "expiryDate",
      label: "expiry",
      sortable: true,
      render: (s) => {
        const ms =
          new Date(s.expiryDate).getTime() - Date.now();
        const days = ms / (1000 * 60 * 60 * 24);
        if (days < 0) return <Chip tone="mch">{s.expiryDate}</Chip>;
        if (days < 30) return <Chip tone="bf">{s.expiryDate}</Chip>;
        return (
          <span className="font-mono text-[12px] text-ink">{s.expiryDate}</span>
        );
      },
    },
    {
      key: "status",
      label: "status",
      sortable: true,
      render: (s) => (
        <Chip tone={STATUS_TONE[s.status]}>
          <span
            className="inline-block w-[5px] h-[5px] rounded-full bg-current"
            aria-hidden="true"
          />
          {STATUS_LABEL[s.status]}
        </Chip>
      ),
    },
  ];

  return (
    <DataTable<Sample>
      columns={columns}
      rows={filtered}
      rowKey={(s) => s.id}
      selectable
      selectedKeys={selectedSamples}
      onSelectionChange={(keys) => {
        if (keys.length === 0) clearSelection();
        else selectAll(keys);
      }}
      sortKey={sortField}
      sortDir={sortDir}
      onSortChange={(key, dir) => {
        setSortField(key as SortField);
        setSortDir(dir);
      }}
      toolbar={
        <>
          <TableSearch
            value={filters.search}
            onChange={(v) => setFilters({ search: v })}
            placeholder="search by name, barcode, lot…"
          />
          <TableSelect
            value={filters.type as SampleType | "all"}
            onChange={(v) => setFilters({ type: v as SampleType | "all" })}
            options={[
              { label: "type · all", value: "all" as const },
              ...(Object.entries(SAMPLE_TYPE_LABELS) as [SampleType, string][]).map(
                ([val, label]) => ({
                  label: `type · ${label.toLowerCase()}`,
                  value: val,
                })
              ),
            ]}
          />
          <TableSelect
            value={filters.status as SampleStatus | "all"}
            onChange={(v) => setFilters({ status: v as SampleStatus | "all" })}
            options={[
              { label: "status · all", value: "all" as const },
              { label: "status · active", value: "active" as const },
              { label: "status · expiring", value: "expiring" as const },
              { label: "status · expired", value: "expired" as const },
              { label: "status · low stock", value: "low_stock" as const },
            ]}
          />
          <div className="flex-1" />
          {selectedSamples.length > 0 && (
            <span className="font-mono text-[11px] tracking-[0.02em] text-ink-muted">
              {selectedSamples.length} selected
            </span>
          )}
          <IconAction icon={Download} label="export" onClick={exportCSV} />
          <IconAction icon={Printer} label="print" onClick={() => window.print()} />
        </>
      }
      footer={
        <>
          <span>
            showing {filtered.length} / {samples.length} samples
          </span>
          {selectedSamples.length > 0 && (
            <span>
              {selectedSamples.length} selected · <a href="#" className="text-brand">bulk actions →</a>
            </span>
          )}
        </>
      }
      emptyState={
        <span className="font-mono text-[12px] tracking-[0.02em]">
          no samples match your filters
        </span>
      }
    />
  );
}

"use client";

import { useMemo } from "react";
import { Plus, ScanLine, Upload } from "lucide-react";
import SampleTable from "@/components/lab/sample-table";
import SampleModal from "@/components/lab/sample-modal";
import BarcodeScanner from "@/components/lab/barcode-scanner";
import { useSampleStore } from "@/stores/sample-store";
import {
  PageHeader,
  PageHeaderPrimary,
  PageHeaderGhost,
} from "@/components/lab/primitives/page-header";
import { KpiStrip, Kpi } from "@/components/lab/primitives/kpi-strip";

export default function SamplesPage() {
  const { samples, openModal, setScannerMode } = useSampleStore();

  const stats = useMemo(() => {
    const now = Date.now();
    const thirtyDays = 30 * 24 * 60 * 60 * 1000;
    const sevenDays = 7 * 24 * 60 * 60 * 1000;

    const expiringSoon = samples.filter((s) => {
      const diff = new Date(s.expiryDate).getTime() - now;
      return diff > 0 && diff < thirtyDays;
    });

    const lowStock = samples.filter((s) => s.status === "low_stock");

    const recent = samples.filter(
      (s) => now - new Date(s.addedDate).getTime() < sevenDays
    );

    const expiringSummary =
      expiringSoon
        .slice(0, 3)
        .map((s) => s.name.split(" ")[0])
        .join(" · ") || "none";

    return {
      total: samples.length,
      expiringCount: expiringSoon.length,
      expiringSummary,
      lowCount: lowStock.length,
      recentCount: recent.length,
      recentName: recent[0]?.name,
    };
  }, [samples]);

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="04"
        markerLabel="Inventory · samples & reagents"
        title="Inventory"
        meta={
          <>
            {stats.total} samples ·{" "}
            <em
              className="not-italic"
              style={{ color: stats.expiringCount > 0 ? "var(--color-bf)" : undefined }}
            >
              {stats.expiringCount} expiring in 30d
            </em>{" "}
            · sync 02:14 ago
          </>
        }
      >
        <PageHeaderGhost onClick={() => setScannerMode("find")}>
          <ScanLine size={14} />
          Scanner
        </PageHeaderGhost>
        <PageHeaderGhost>
          <Upload size={14} />
          Import CSV
        </PageHeaderGhost>
        <PageHeaderPrimary onClick={() => openModal()}>
          <Plus size={14} />
          Add sample
        </PageHeaderPrimary>
      </PageHeader>

      <KpiStrip columns={4}>
        <Kpi label="total" value={stats.total} delta="all samples" />
        <Kpi
          label="expiring < 30d"
          value={String(stats.expiringCount).padStart(2, "0")}
          delta={stats.expiringSummary}
          tone="bf"
        />
        <Kpi
          label="low stock"
          value={String(stats.lowCount).padStart(2, "0")}
          delta={stats.lowCount > 0 ? `${stats.lowCount} reorders queued` : "stock healthy"}
          tone="mch"
        />
        <Kpi
          label="added this wk"
          value={String(stats.recentCount).padStart(2, "0")}
          delta={stats.recentName || "none added"}
          tone="brand"
        />
      </KpiStrip>

      <div className="flex-1 mx-6 my-6 min-h-0 flex flex-col">
        <SampleTable />
      </div>

      <SampleModal />
      <BarcodeScanner />
    </div>
  );
}

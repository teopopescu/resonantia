"use client";

import { useMemo } from "react";
import {
  FlaskConical,
  Plus,
  Package,
  AlertTriangle,
  TrendingDown,
  Clock,
  Search,
} from "lucide-react";
import SampleTable from "@/components/lab/sample-table";
import SampleModal from "@/components/lab/sample-modal";
import BarcodeScanner from "@/components/lab/barcode-scanner";
import { useSampleStore } from "@/stores/sample-store";

export default function SamplesPage() {
  const { samples, openModal, setScannerMode } = useSampleStore();

  const stats = useMemo(() => {
    const now = Date.now();
    const thirtyDays = 30 * 24 * 60 * 60 * 1000;

    const expiringSoon = samples.filter((s) => {
      const diff = new Date(s.expiryDate).getTime() - now;
      return diff > 0 && diff < thirtyDays;
    }).length;

    const lowStock = samples.filter(
      (s) => s.status === "low_stock"
    ).length;

    const recentCount = samples.filter((s) => {
      const diff = now - new Date(s.addedDate).getTime();
      return diff < 7 * 24 * 60 * 60 * 1000;
    }).length;

    return {
      total: samples.length,
      expiringSoon,
      lowStock,
      recentCount,
    };
  }, [samples]);

  return (
    <div className="flex flex-col h-full bg-cream">
      {/* Header */}
      <div className="px-6 py-4 bg-surface border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber/15 flex items-center justify-center">
              <FlaskConical size={18} className="text-amber" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-charcoal">
                Sample & Reagent Tracker
              </h1>
              <p className="text-xs text-muted">
                Manage inventory, track expiry dates, and scan barcodes
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setScannerMode("find")}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted bg-cream hover:bg-cream-dark transition-colors"
            >
              <Search size={15} />
              Lookup
            </button>
            <button
              onClick={() => openModal()}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
            >
              <Plus size={15} />
              Add Sample
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard cards */}
      <div className="px-6 py-4 grid grid-cols-4 gap-4">
        <DashCard
          icon={<Package size={18} className="text-amber" />}
          label="Total Samples"
          value={stats.total}
          bg="bg-amber/10"
        />
        <DashCard
          icon={<AlertTriangle size={18} className="text-yellow-600" />}
          label="Expiring Soon"
          value={stats.expiringSoon}
          bg="bg-yellow-50"
          highlight={stats.expiringSoon > 0 ? "text-yellow-700" : undefined}
        />
        <DashCard
          icon={<TrendingDown size={18} className="text-orange-600" />}
          label="Low Stock"
          value={stats.lowStock}
          bg="bg-orange-50"
          highlight={stats.lowStock > 0 ? "text-orange-700" : undefined}
        />
        <DashCard
          icon={<Clock size={18} className="text-blue-600" />}
          label="Added This Week"
          value={stats.recentCount}
          bg="bg-blue-50"
        />
      </div>

      {/* Main table area */}
      <div className="flex-1 mx-6 mb-6 bg-surface rounded-xl border border-border overflow-hidden flex flex-col">
        <SampleTable />
      </div>

      {/* Modals */}
      <SampleModal />
      <BarcodeScanner />
    </div>
  );
}

function DashCard({
  icon,
  label,
  value,
  bg,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  bg: string;
  highlight?: string;
}) {
  return (
    <div className="bg-surface rounded-xl border border-border p-4 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center shrink-0`}>
        {icon}
      </div>
      <div>
        <div className={`text-2xl font-semibold ${highlight || "text-charcoal"}`}>
          {value}
        </div>
        <div className="text-xs text-muted">{label}</div>
      </div>
    </div>
  );
}

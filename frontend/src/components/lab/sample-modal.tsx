"use client";

import { useState, useEffect } from "react";
import { X, ScanLine } from "lucide-react";
import { useSampleStore } from "@/stores/sample-store";
import { SAMPLE_TYPE_LABELS, type Sample, type SampleType, type SampleStatus } from "@/lib/demo-data";

function generateId() {
  return "s" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

function generateBarcode() {
  const n = Math.floor(Math.random() * 9000) + 1000;
  return `RES-2024-${n}`;
}

const STORAGE_TEMPS = ["-196°C", "-80°C", "-20°C", "4°C", "RT"];

export default function SampleModal() {
  const { modalOpen, editingSample, closeModal, addSample, updateSample } = useSampleStore();

  const [form, setForm] = useState({
    name: "",
    barcode: "",
    type: "reagent" as SampleType,
    location: "",
    storageTemp: "4°C",
    lotNumber: "",
    expiryDate: "",
    quantity: 0,
    unit: "mL",
    notes: "",
    supplier: "",
    catalogNumber: "",
  });

  useEffect(() => {
    if (editingSample) {
      setForm({
        name: editingSample.name,
        barcode: editingSample.barcode,
        type: editingSample.type,
        location: editingSample.location,
        storageTemp: editingSample.storageTemp,
        lotNumber: editingSample.lotNumber,
        expiryDate: editingSample.expiryDate,
        quantity: editingSample.quantity,
        unit: editingSample.unit,
        notes: editingSample.notes || "",
        supplier: editingSample.supplier || "",
        catalogNumber: editingSample.catalogNumber || "",
      });
    } else {
      setForm({
        name: "",
        barcode: generateBarcode(),
        type: "reagent",
        location: "",
        storageTemp: "4°C",
        lotNumber: "",
        expiryDate: "",
        quantity: 0,
        unit: "mL",
        notes: "",
        supplier: "",
        catalogNumber: "",
      });
    }
  }, [editingSample, modalOpen]);

  if (!modalOpen) return null;

  const computeStatus = (): SampleStatus => {
    if (form.expiryDate) {
      const diff = new Date(form.expiryDate).getTime() - Date.now();
      const days = diff / (1000 * 60 * 60 * 24);
      if (days < 0) return "expired";
      if (days < 30) return "expiring";
    }
    if (form.quantity <= 0) return "low_stock";
    return "active";
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sample: Sample = {
      id: editingSample?.id || generateId(),
      ...form,
      status: computeStatus(),
      addedDate: editingSample?.addedDate || new Date().toISOString().split("T")[0],
    };
    if (editingSample) {
      updateSample(editingSample.id, sample);
    } else {
      addSample(sample);
    }
    closeModal();
  };

  const update = (field: string, value: string | number) =>
    setForm((f) => ({ ...f, [field]: value }));

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={closeModal}
      />

      {/* Modal */}
      <div className="relative bg-surface rounded-xl shadow-2xl w-full max-w-xl max-h-[85vh] overflow-auto border border-border">
        {/* Header */}
        <div className="sticky top-0 bg-surface flex items-center justify-between px-6 py-4 border-b border-border z-10">
          <h2 className="text-lg font-semibold text-charcoal">
            {editingSample ? "Edit Sample" : "Add New Sample"}
          </h2>
          <button
            onClick={closeModal}
            className="p-1.5 rounded-lg hover:bg-cream-dark text-muted hover:text-charcoal transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1.5">
              Name *
            </label>
            <input
              required
              type="text"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
              placeholder="e.g. Anti-GFP Rabbit pAb"
            />
          </div>

          {/* Barcode + Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Barcode
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={form.barcode}
                  onChange={(e) => update("barcode", e.target.value)}
                  className="w-full pl-3 pr-9 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors font-mono"
                />
                <ScanLine
                  size={16}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Type *
              </label>
              <select
                value={form.type}
                onChange={(e) => update("type", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
              >
                {Object.entries(SAMPLE_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1.5">
              Location
            </label>
            <input
              type="text"
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
              placeholder="Freezer-A / Shelf-2 / Box-3 / A1"
            />
          </div>

          {/* Storage Temp + Lot */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Storage Temp
              </label>
              <select
                value={form.storageTemp}
                onChange={(e) => update("storageTemp", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%238A8478%22%20viewBox%3D%220%200%2016%2016%22%3E%3Cpath%20d%3D%22M4.646%206.646a.5.5%200%200%201%20.708%200L8%209.293l2.646-2.647a.5.5%200%200%201%20.708.708l-3%203a.5.5%200%200%201-.708%200l-3-3a.5.5%200%200%201%200-.708z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_0.75rem_center] pr-8 focus:outline-none focus:border-amber/40 cursor-pointer hover:border-amber/20 transition-colors"
              >
                {STORAGE_TEMPS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Lot Number
              </label>
              <input
                type="text"
                value={form.lotNumber}
                onChange={(e) => update("lotNumber", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors font-mono"
              />
            </div>
          </div>

          {/* Expiry + Qty + Unit */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Expiry Date
              </label>
              <input
                type="date"
                value={form.expiryDate}
                onChange={(e) => update("expiryDate", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Quantity
              </label>
              <input
                type="number"
                step="any"
                min="0"
                value={form.quantity}
                onChange={(e) => update("quantity", parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Unit
              </label>
              <input
                type="text"
                value={form.unit}
                onChange={(e) => update("unit", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
                placeholder="mL, uL, mg, vials..."
              />
            </div>
          </div>

          {/* Supplier + Catalog */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Supplier
              </label>
              <input
                type="text"
                value={form.supplier}
                onChange={(e) => update("supplier", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Catalog #
              </label>
              <input
                type="text"
                value={form.catalogNumber}
                onChange={(e) => update("catalogNumber", e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors font-mono"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1.5">
              Notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              rows={2}
              className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40 transition-colors resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 text-sm text-muted hover:text-charcoal rounded-lg hover:bg-cream-dark transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors"
            >
              {editingSample ? "Save Changes" : "Add Sample"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

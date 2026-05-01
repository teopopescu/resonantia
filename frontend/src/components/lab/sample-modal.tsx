"use client";

import { useState, useEffect } from "react";
import { X, ScanLine } from "lucide-react";
import { useSampleStore } from "@/stores/sample-store";
import {
  SAMPLE_TYPE_LABELS,
  type Sample,
  type SampleType,
  type SampleStatus,
} from "@/lib/demo-data";
import { cn } from "@/lib/utils";

function generateId() {
  return "s" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

function generateBarcode() {
  const n = Math.floor(Math.random() * 9000) + 1000;
  return `RES-2024-${n}`;
}

const STORAGE_TEMPS = ["-196°C", "-80°C", "-20°C", "4°C", "RT"];

const inputBase =
  "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-ink text-[13px] focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle";

function FieldLabel({
  required,
  children,
}: {
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
      {required && <span className="text-mch ml-0.5">*</span>}
    </label>
  );
}

export default function SampleModal() {
  const { modalOpen, editingSample, closeModal, addSample, updateSample } =
    useSampleStore();

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
      <div
        className="absolute inset-0 bg-ink/40 backdrop-blur-sm"
        onClick={closeModal}
      />

      <div className="relative bg-surface rounded-[5px] shadow-xl w-full max-w-xl max-h-[85vh] overflow-auto border border-line">
        {/* Header */}
        <div className="sticky top-0 bg-surface flex items-center justify-between px-6 py-4 border-b border-line z-10">
          <div>
            <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle mb-1">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5 mr-2">
                {editingSample ? "EDIT" : "NEW"}
              </span>
              inventory · sample
            </div>
            <h2 className="text-[18px] font-semibold tracking-[-0.02em] text-ink">
              {editingSample ? "Edit sample" : "Add new sample"}
            </h2>
          </div>
          <button
            onClick={closeModal}
            className="p-1.5 rounded-[3px] hover:bg-bg text-ink-muted hover:text-ink transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <FieldLabel required>name</FieldLabel>
            <input
              required
              type="text"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              className={inputBase}
              placeholder="e.g. Anti-GFP Rabbit pAb"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <FieldLabel>barcode</FieldLabel>
              <div className="relative">
                <input
                  type="text"
                  value={form.barcode}
                  onChange={(e) => update("barcode", e.target.value)}
                  className={cn(inputBase, "font-mono pr-9")}
                />
                <ScanLine
                  size={14}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-subtle"
                />
              </div>
            </div>
            <div>
              <FieldLabel required>type</FieldLabel>
              <select
                value={form.type}
                onChange={(e) => update("type", e.target.value)}
                className={cn(inputBase, "cursor-pointer")}
              >
                {Object.entries(SAMPLE_TYPE_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <FieldLabel>location</FieldLabel>
            <input
              type="text"
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              className={cn(inputBase, "font-mono")}
              placeholder="freezer-A / shelf-2 / box-3 / A1"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <FieldLabel>storage temp</FieldLabel>
              <select
                value={form.storageTemp}
                onChange={(e) => update("storageTemp", e.target.value)}
                className={cn(inputBase, "font-mono cursor-pointer")}
              >
                {STORAGE_TEMPS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <FieldLabel>lot number</FieldLabel>
              <input
                type="text"
                value={form.lotNumber}
                onChange={(e) => update("lotNumber", e.target.value)}
                className={cn(inputBase, "font-mono")}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <FieldLabel>expiry date</FieldLabel>
              <input
                type="date"
                value={form.expiryDate}
                onChange={(e) => update("expiryDate", e.target.value)}
                className={cn(inputBase, "font-mono")}
              />
            </div>
            <div>
              <FieldLabel>quantity</FieldLabel>
              <input
                type="number"
                step="any"
                min="0"
                value={form.quantity}
                onChange={(e) =>
                  update("quantity", parseFloat(e.target.value) || 0)
                }
                className={cn(inputBase, "font-mono")}
              />
            </div>
            <div>
              <FieldLabel>unit</FieldLabel>
              <input
                type="text"
                value={form.unit}
                onChange={(e) => update("unit", e.target.value)}
                className={cn(inputBase, "font-mono")}
                placeholder="mL · uL · mg · vials"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <FieldLabel>supplier</FieldLabel>
              <input
                type="text"
                value={form.supplier}
                onChange={(e) => update("supplier", e.target.value)}
                className={inputBase}
              />
            </div>
            <div>
              <FieldLabel>catalog #</FieldLabel>
              <input
                type="text"
                value={form.catalogNumber}
                onChange={(e) => update("catalogNumber", e.target.value)}
                className={cn(inputBase, "font-mono")}
              />
            </div>
          </div>

          <div>
            <FieldLabel>notes</FieldLabel>
            <textarea
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              rows={2}
              className={cn(inputBase, "resize-none")}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-line">
            <button
              type="button"
              onClick={closeModal}
              className="px-3 py-2 text-[13px] text-ink-muted hover:text-ink transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-3.5 py-2 bg-brand text-white text-[13px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
              style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
            >
              {editingSample ? "Save changes" : "Add sample"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

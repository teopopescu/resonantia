"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Clock,
  Thermometer,
  Wrench,
  FlaskConical,
  GripVertical,
  ChevronRight,
} from "lucide-react";
import { useProtocolStore, type ProtocolStep, type Reagent } from "@/stores/protocol-store";

interface ProtocolStepBuilderProps {
  protocolId: string;
  steps: ProtocolStep[];
}

export default function ProtocolStepBuilder({ protocolId, steps }: ProtocolStepBuilderProps) {
  const { addStep, updateStep, removeStep, reorderSteps } = useProtocolStore();
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {steps.map((step, index) => {
        const isExpanded = expandedStep === step.id;
        return (
          <div
            key={step.id}
            className={`rounded-xl border transition-all ${
              isExpanded ? "border-amber/40 shadow-sm" : "border-border hover:border-amber/20"
            }`}
          >
            {/* Step header */}
            <div className="flex items-center gap-3 px-4 py-3">
              <div className="flex flex-col gap-0.5 shrink-0">
                <button
                  onClick={() => index > 0 && reorderSteps(protocolId, index, index - 1)}
                  disabled={index === 0}
                  className="p-0.5 text-muted hover:text-charcoal disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronUp size={12} />
                </button>
                <button
                  onClick={() => index < steps.length - 1 && reorderSteps(protocolId, index, index + 1)}
                  disabled={index === steps.length - 1}
                  className="p-0.5 text-muted hover:text-charcoal disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronDown size={12} />
                </button>
              </div>

              <div className="w-7 h-7 rounded-lg bg-amber/15 flex items-center justify-center shrink-0">
                <span className="text-xs font-semibold text-amber">{step.step_number}</span>
              </div>

              <button
                onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                className="flex-1 text-left min-w-0"
              >
                <div className="text-sm font-medium text-charcoal truncate">
                  {step.title || "Untitled Step"}
                </div>
                <div className="flex items-center gap-3 mt-0.5">
                  {step.duration_minutes && (
                    <span className="flex items-center gap-1 text-xs text-muted">
                      <Clock size={10} /> {step.duration_minutes} min
                    </span>
                  )}
                  {step.temperature_celsius !== undefined && (
                    <span className="flex items-center gap-1 text-xs text-muted">
                      <Thermometer size={10} /> {step.temperature_celsius}°C
                    </span>
                  )}
                  {step.equipment && (
                    <span className="flex items-center gap-1 text-xs text-muted">
                      <Wrench size={10} /> {step.equipment}
                    </span>
                  )}
                  {step.reagents.length > 0 && (
                    <span className="flex items-center gap-1 text-xs text-muted">
                      <FlaskConical size={10} /> {step.reagents.length} reagent{step.reagents.length !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </button>

              <button
                onClick={() => removeStep(protocolId, step.id)}
                className="p-1.5 text-muted hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors shrink-0"
              >
                <Trash2 size={14} />
              </button>

              <ChevronRight
                size={14}
                className={`text-muted transition-transform shrink-0 ${isExpanded ? "rotate-90" : ""}`}
              />
            </div>

            {/* Expanded edit form */}
            {isExpanded && (
              <StepEditForm
                protocolId={protocolId}
                step={step}
                onUpdate={(updates) => updateStep(protocolId, step.id, updates)}
              />
            )}
          </div>
        );
      })}

      {/* Add step button */}
      <button
        onClick={() => addStep(protocolId)}
        className="flex items-center gap-2 w-full px-4 py-3 text-sm text-muted hover:text-charcoal rounded-xl border border-dashed border-border hover:border-amber/40 transition-colors"
      >
        <Plus size={14} />
        Add Step
      </button>
    </div>
  );
}

function StepEditForm({
  protocolId,
  step,
  onUpdate,
}: {
  protocolId: string;
  step: ProtocolStep;
  onUpdate: (updates: Partial<ProtocolStep>) => void;
}) {
  const inputClass =
    "w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40";

  function addReagent() {
    onUpdate({ reagents: [...step.reagents, { name: "", volume: 0, unit: "uL" }] });
  }

  function updateReagent(index: number, updates: Partial<Reagent>) {
    const reagents = step.reagents.map((r, i) => (i === index ? { ...r, ...updates } : r));
    onUpdate({ reagents });
  }

  function removeReagent(index: number) {
    onUpdate({ reagents: step.reagents.filter((_, i) => i !== index) });
  }

  return (
    <div className="px-4 pb-4 space-y-3 border-t border-border/50">
      <div className="pt-3">
        <label className="block text-xs font-medium text-charcoal mb-1">Title</label>
        <input
          type="text"
          value={step.title}
          onChange={(e) => onUpdate({ title: e.target.value })}
          placeholder="Step title"
          className={inputClass}
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Description</label>
        <textarea
          value={step.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          placeholder="Step description..."
          rows={3}
          className={`${inputClass} resize-none`}
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Duration (min)</label>
          <input
            type="number"
            value={step.duration_minutes ?? ""}
            onChange={(e) => onUpdate({ duration_minutes: e.target.value ? Number(e.target.value) : undefined })}
            placeholder="30"
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Temperature (°C)</label>
          <input
            type="number"
            value={step.temperature_celsius ?? ""}
            onChange={(e) =>
              onUpdate({ temperature_celsius: e.target.value ? Number(e.target.value) : undefined })
            }
            placeholder="37"
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Equipment</label>
          <input
            type="text"
            value={step.equipment ?? ""}
            onChange={(e) => onUpdate({ equipment: e.target.value })}
            placeholder="e.g. Centrifuge"
            className={inputClass}
          />
        </div>
      </div>

      {/* Reagents */}
      <div>
        <label className="block text-xs font-medium text-charcoal mb-2">Reagents</label>
        <div className="space-y-2">
          {step.reagents.map((r, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="text"
                value={r.name}
                onChange={(e) => updateReagent(i, { name: e.target.value })}
                placeholder="Reagent name"
                className="flex-1 px-3 py-1.5 rounded-lg border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              />
              <input
                type="number"
                value={r.volume || ""}
                onChange={(e) => updateReagent(i, { volume: Number(e.target.value) })}
                placeholder="Vol"
                className="w-20 px-2 py-1.5 rounded-lg border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              />
              <select
                value={r.unit}
                onChange={(e) => updateReagent(i, { unit: e.target.value })}
                className="w-20 px-2 py-1.5 rounded-lg border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40"
              >
                <option value="uL">uL</option>
                <option value="mL">mL</option>
                <option value="L">L</option>
                <option value="ug">ug</option>
                <option value="mg">mg</option>
                <option value="g">g</option>
              </select>
              <button
                onClick={() => removeReagent(i)}
                className="p-1 text-muted hover:text-red-500 transition-colors"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          <button
            onClick={addReagent}
            className="flex items-center gap-1 text-xs text-muted hover:text-charcoal transition-colors"
          >
            <Plus size={12} /> Add reagent
          </button>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-charcoal mb-1">Notes</label>
        <input
          type="text"
          value={step.notes ?? ""}
          onChange={(e) => onUpdate({ notes: e.target.value })}
          placeholder="Optional notes..."
          className={inputClass}
        />
      </div>
    </div>
  );
}

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
            className={`rounded-[5px] border transition-colors ${
              isExpanded ? "border-brand/40" : "border-line hover:border-line-strong"
            }`}
          >
            {/* Step header */}
            <div className="flex items-center gap-3 px-4 py-3">
              <div className="flex flex-col gap-0.5 shrink-0">
                <button
                  onClick={() => index > 0 && reorderSteps(protocolId, index, index - 1)}
                  disabled={index === 0}
                  className="p-0.5 text-ink-subtle hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronUp size={12} />
                </button>
                <button
                  onClick={() => index < steps.length - 1 && reorderSteps(protocolId, index, index + 1)}
                  disabled={index === steps.length - 1}
                  className="p-0.5 text-ink-subtle hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronDown size={12} />
                </button>
              </div>

              <div className="w-7 h-7 rounded-[3px] bg-brand-soft border border-brand/30 flex items-center justify-center shrink-0">
                <span className="font-mono text-[11px] font-semibold text-brand">
                  {step.step_number}
                </span>
              </div>

              <button
                onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                className="flex-1 text-left min-w-0"
              >
                <div className="text-[13.5px] font-medium text-ink truncate">
                  {step.title || "Untitled step"}
                </div>
                <div className="flex flex-wrap items-center gap-3 mt-1 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle">
                  {step.duration_minutes && (
                    <span className="flex items-center gap-1">
                      <Clock size={10} /> {step.duration_minutes} min
                    </span>
                  )}
                  {step.temperature_celsius !== undefined && (
                    <span className="flex items-center gap-1">
                      <Thermometer size={10} /> {step.temperature_celsius}°C
                    </span>
                  )}
                  {step.equipment && (
                    <span className="flex items-center gap-1">
                      <Wrench size={10} /> {step.equipment}
                    </span>
                  )}
                  {step.reagents.length > 0 && (
                    <span className="flex items-center gap-1">
                      <FlaskConical size={10} /> {step.reagents.length} reagent
                      {step.reagents.length !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </button>

              <button
                onClick={() => removeStep(protocolId, step.id)}
                className="p-1.5 text-ink-subtle hover:text-mch rounded-[3px] hover:bg-mch-soft transition-colors shrink-0"
              >
                <Trash2 size={13} />
              </button>

              <ChevronRight
                size={14}
                className={`text-ink-subtle transition-transform shrink-0 ${
                  isExpanded ? "rotate-90" : ""
                }`}
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
        className="flex items-center justify-center gap-2 w-full px-4 py-3 font-mono text-[11.5px] uppercase tracking-[0.04em] text-ink-muted hover:text-ink rounded-[5px] border border-dashed border-line-strong hover:border-brand transition-colors"
      >
        <Plus size={13} />
        add step
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
    "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle";
  const labelClass =
    "block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5";

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
    <div className="px-4 pb-4 space-y-3 border-t border-line bg-bg">
      <div className="pt-3">
        <label className={labelClass}>title</label>
        <input
          type="text"
          value={step.title}
          onChange={(e) => onUpdate({ title: e.target.value })}
          placeholder="step title"
          className={inputClass}
        />
      </div>

      <div>
        <label className={labelClass}>description</label>
        <textarea
          value={step.description}
          onChange={(e) => onUpdate({ description: e.target.value })}
          placeholder="step description…"
          rows={3}
          className={`${inputClass} resize-none`}
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className={labelClass}>duration · min</label>
          <input
            type="number"
            value={step.duration_minutes ?? ""}
            onChange={(e) =>
              onUpdate({
                duration_minutes: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            placeholder="30"
            className={`${inputClass} font-mono`}
          />
        </div>
        <div>
          <label className={labelClass}>temperature · °C</label>
          <input
            type="number"
            value={step.temperature_celsius ?? ""}
            onChange={(e) =>
              onUpdate({
                temperature_celsius: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            placeholder="37"
            className={`${inputClass} font-mono`}
          />
        </div>
        <div>
          <label className={labelClass}>equipment</label>
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
        <label className={labelClass}>reagents</label>
        <div className="space-y-1.5">
          {step.reagents.map((r, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="text"
                value={r.name}
                onChange={(e) => updateReagent(i, { name: e.target.value })}
                placeholder="reagent name"
                className="flex-1 px-3 py-1.5 rounded-[3px] border border-line bg-surface text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors"
              />
              <input
                type="number"
                value={r.volume || ""}
                onChange={(e) => updateReagent(i, { volume: Number(e.target.value) })}
                placeholder="vol"
                className="w-20 px-2 py-1.5 rounded-[3px] border border-line bg-surface font-mono text-[12px] text-ink focus:outline-none focus:border-brand/40 transition-colors"
              />
              <select
                value={r.unit}
                onChange={(e) => updateReagent(i, { unit: e.target.value })}
                className="w-20 px-2 py-1.5 rounded-[3px] border border-line bg-surface font-mono text-[12px] text-ink focus:outline-none focus:border-brand/40 transition-colors cursor-pointer"
              >
                <option value="uL">µL</option>
                <option value="mL">mL</option>
                <option value="L">L</option>
                <option value="ug">µg</option>
                <option value="mg">mg</option>
                <option value="g">g</option>
              </select>
              <button
                onClick={() => removeReagent(i)}
                className="p-1 text-ink-subtle hover:text-mch transition-colors"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          <button
            onClick={addReagent}
            className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted hover:text-brand transition-colors mt-1"
          >
            <Plus size={11} /> add reagent
          </button>
        </div>
      </div>

      <div>
        <label className={labelClass}>notes</label>
        <input
          type="text"
          value={step.notes ?? ""}
          onChange={(e) => onUpdate({ notes: e.target.value })}
          placeholder="optional notes…"
          className={inputClass}
        />
      </div>
    </div>
  );
}

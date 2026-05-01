"use client";

/**
 * Instrument ticker — runs across the top of marketing pages just under the nav.
 * For now the values are static; later this can subscribe to real telemetry
 * (scope state, plate progress, queue depth, sync time).
 */

const items = [
  { kind: "live" as const,  label: "Scope-1", value: "acquiring" },
  { kind: "text" as const,  label: "Plate A · row B · FOV 4 / 6" },
  { kind: "idle" as const,  label: "Echo-2", value: "idle" },
  { kind: "warn" as const,  label: "DMEM",   value: "12% remaining" },
  { kind: "text" as const,  label: "Room 4°C · CO₂ 5.2%" },
  { kind: "text" as const,  label: "Queue 3 jobs" },
  { kind: "text" as const,  label: "Last sync 00:42 ago" },
];

function Led({ tone }: { tone: "live" | "idle" | "warn" }) {
  const cls =
    tone === "live"
      ? "bg-brand pulse-led"
      : tone === "warn"
      ? "bg-bf"
      : "bg-ink-subtle";
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${cls}`} />;
}

export function Ticker() {
  return (
    <div className="border-b border-line bg-bg">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center gap-6 py-2 overflow-hidden whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted">
          {items.map((it, i) => (
            <span key={i} className="flex items-center gap-2 shrink-0">
              {(it.kind === "live" || it.kind === "idle" || it.kind === "warn") && (
                <Led tone={it.kind} />
              )}
              <span>
                {it.label}
                {"value" in it && it.value && (
                  <>
                    {" "}
                    <b className="text-ink font-medium normal-case tracking-normal">
                      {it.value}
                    </b>
                  </>
                )}
              </span>
              {i < items.length - 1 && (
                <span className="text-line-strong ml-6">·</span>
              )}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

/* ── Agentic conversation panel ──
 * Two real lab cycles, animated to reveal turn-by-turn with a brief
 * "thinking" indicator before each agent reply. Auto-cycles between
 * the two examples; tabs switch manually.
 */

type Mode = "chat" | "voice";

interface Turn {
  role: "user" | "agent";
  mode?: Mode;
  time: string;
  text: React.ReactNode;
  chips?: string[];
}

interface Example {
  id: string;
  label: string;
  meta: React.ReactNode;
  stages: Array<{ label: string; done: boolean }>;
  turns: Turn[];
}

const examples: Example[] = [
  {
    id: "kinase",
    label: "Kinase screen · overnight",
    meta: (
      <>
        Agent · <b className="text-ink font-semibold">round 1 · kinase screen</b>
      </>
    ),
    stages: [
      { label: "plan", done: true },
      { label: "run", done: true },
      { label: "image", done: true },
      { label: "analyze", done: true },
      { label: "notebook", done: false },
    ],
    turns: [
      {
        role: "user",
        mode: "voice",
        time: "tue · 14:32",
        text: "Plan me a kinase screen for the new compound set.",
      },
      {
        role: "agent",
        time: "14:32:08",
        text: (
          <>
            24 compounds in <em className="not-italic text-brand">Lib-A</em>. Standard
            layout — three replicates, 100 nL transfers, two controls per row?
          </>
        ),
      },
      {
        role: "user",
        mode: "voice",
        time: "14:33",
        text: "Yes, and add a staurosporine titration in column 11.",
      },
      {
        role: "agent",
        time: "14:33:04",
        text: (
          <>
            Done. <em className="not-italic text-brand">88 wells</em> used. Z′ should hit
            ~0.78 with the added titration.
          </>
        ),
        chips: ["PLT/01 · cherry-pick", "echo-550 · 100 nL"],
      },
      {
        role: "user",
        mode: "voice",
        time: "14:34",
        text: "Run it Wednesday night, image at 06:00.",
      },
      {
        role: "agent",
        time: "14:34:02",
        text: (
          <>
            Scheduled. I&apos;ll fit IC₅₀ and draft an ELN entry by Thursday morning.
          </>
        ),
        chips: ["WL/01 · scheduled WED", "MIC/02 · 06:00"],
      },
      {
        role: "user",
        mode: "chat",
        time: "thu · 09:14",
        text: "How did round 1 go?",
      },
      {
        role: "agent",
        time: "09:14:11",
        text: (
          <>
            IC₅₀ <em className="not-italic text-brand">42.3 nM</em> · Hill −1.18 · Z′ 0.71. One
            outlier in C4 flagged. Draft is ready for review.
          </>
        ),
        chips: ["DAT/03 · fit done", "ELN-2026-0428"],
      },
    ],
  },
  {
    id: "voice-capture",
    label: "Voice capture · ELN/LIMS",
    meta: (
      <>
        Agent · <b className="text-ink font-semibold">hands-free experiment capture</b>
      </>
    ),
    stages: [
      { label: "listen", done: true },
      { label: "structure", done: true },
      { label: "review", done: true },
      { label: "sync", done: true },
      { label: "audit", done: false },
    ],
    turns: [
      {
        role: "user",
        mode: "voice",
        time: "wed · 10:18",
        text:
          "Record this experiment: HEK293T viability assay, staurosporine ten-point dilution, three replicates, CellTiter-Glo readout.",
      },
      {
        role: "agent",
        time: "10:18:06",
        text: (
          <>
            Captured <em className="not-italic text-brand">7 structured fields</em>:
            model, assay, compound, dilution, replicates, readout, and objective.
            Which vehicle control should I use?
          </>
        ),
        chips: ["VOICE/01 · transcribed", "EXP/02 · parsed"],
      },
      {
        role: "user",
        mode: "voice",
        time: "10:19",
        text: "Use 0.1 percent DMSO vehicle and add staurosporine as the positive control.",
      },
      {
        role: "agent",
        time: "10:19:04",
        text: (
          <>
            Draft is ready. I mapped controls, linked the compound lot, and
            validated the ELN/LIMS payload. Review before I sync?
          </>
        ),
        chips: ["ELN/03 · draft", "LIMS/04 · payload valid"],
      },
      {
        role: "user",
        mode: "chat",
        time: "10:20",
        text: "Looks right. Sync it to eLabFTW and keep the LIMS payload queued.",
      },
      {
        role: "agent",
        time: "10:20:03",
        text: (
          <>
            Synced to <em className="not-italic text-brand">eLabFTW</em>. LIMS
            payload is queued for approval, and the transcript is attached to
            the audit trail.
          </>
        ),
        chips: ["ELN-2026-0430", "AUD/06 · transcript saved"],
      },
    ],
  },
];

const PAUSE_BEFORE_NEXT = 2800;

/* ── Reveal hook ─────────────────────────────────────────────────── */

function useReveal(example: Example, onComplete: () => void) {
  const onCompleteRef = useRef(onComplete);
  const [reveal, setReveal] = useState({
    exampleId: example.id,
    step: 0,
    thinking: false,
  });

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    let t = 500;

    example.turns.forEach((turn, i) => {
      if (turn.role === "agent") {
        timers.push(
          setTimeout(() => {
            setReveal((current) => ({
              exampleId: example.id,
              step: current.exampleId === example.id ? current.step : 0,
              thinking: true,
            }));
          }, t)
        );
        t += 750;
        timers.push(
          setTimeout(() => {
            setReveal({ exampleId: example.id, step: i + 1, thinking: false });
          }, t)
        );
        t += 1900;
      } else {
        timers.push(
          setTimeout(() => {
            setReveal({ exampleId: example.id, step: i + 1, thinking: false });
          }, t)
        );
        t += 1450;
      }
    });

    timers.push(
      setTimeout(() => onCompleteRef.current(), t + PAUSE_BEFORE_NEXT)
    );

    return () => timers.forEach(clearTimeout);
  }, [example]);

  if (reveal.exampleId !== example.id) {
    return { step: 0, thinking: false };
  }

  const { step, thinking } = reveal;
  return { step, thinking };
}

/* ── Sub-components ──────────────────────────────────────────────── */

function BrandMark({ size = 22 }: { size?: number }) {
  return (
    <span
      className="inline-grid grid-cols-2 grid-rows-2 gap-[2px] p-[3px] rounded-[4px] bg-surface border border-line-strong shrink-0"
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-brand" />
    </span>
  );
}

function ModeIcon({ mode }: { mode: Mode }) {
  if (mode === "voice") {
    return (
      <span className="inline-flex items-center justify-center w-[22px] h-[22px] rounded-[4px] bg-brand-soft border border-brand/30 text-brand shrink-0">
        <Mic size={12} />
      </span>
    );
  }
  return (
    <span className="inline-flex items-center justify-center w-[22px] h-[22px] rounded-[4px] bg-bg-sunk border border-line text-ink-muted shrink-0">
      <MessageSquare size={12} />
    </span>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <motion.span
      animate={{ opacity: [0.25, 1, 0.25] }}
      transition={{
        duration: 1.1,
        repeat: Infinity,
        delay: delay / 1000,
        ease: "easeInOut",
      }}
      className="inline-block w-[5px] h-[5px] rounded-full bg-ink-muted"
    />
  );
}

function ThinkingRow() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      className="flex items-start gap-2.5"
    >
      <BrandMark />
      <div className="min-w-0 flex-1">
        <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle mb-1">
          agent · thinking
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md bg-bg border border-line">
          <Dot delay={0} />
          <Dot delay={180} />
          <Dot delay={360} />
        </div>
      </div>
    </motion.div>
  );
}

function TurnRow({ turn }: { turn: Turn }) {
  const isAgent = turn.role === "agent";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: "easeOut" }}
      className="flex items-start gap-2.5"
    >
      {isAgent ? <BrandMark /> : <ModeIcon mode={turn.mode || "chat"} />}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-0.5 font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle">
          <span>
            {isAgent
              ? "agent"
              : turn.mode === "voice"
              ? "you · voice"
              : "you · chat"}
          </span>
          <span className="text-line-strong">·</span>
          <span>{turn.time}</span>
        </div>
        <div
          className={cn(
            "text-[13px] leading-[1.5]",
            isAgent ? "text-ink" : "text-ink-muted"
          )}
        >
          {turn.text}
        </div>
        {turn.chips && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.18, duration: 0.25 }}
            className="mt-1.5 flex flex-wrap gap-1.5"
          >
            {turn.chips.map((c) => (
              <span
                key={c}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] font-mono text-[10px] tracking-[0.02em] uppercase bg-brand-soft border border-brand/30 text-brand"
              >
                <span className="inline-block w-[5px] h-[5px] rounded-full bg-brand" />
                {c}
              </span>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

function StageRail({ stages }: { stages: Example["stages"] }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 mb-5 font-mono text-[10px] uppercase tracking-[0.06em]">
      {stages.map((s, i) => (
        <span key={s.label} className="flex items-center gap-1.5">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded-[2px] border",
              s.done
                ? "bg-brand-soft text-brand border-brand/30"
                : "bg-bg-sunk text-ink-subtle border-line"
            )}
          >
            <span
              className={cn(
                "inline-block w-[5px] h-[5px] rounded-full",
                s.done ? "bg-brand" : "bg-ink-subtle"
              )}
            />
            {s.label}
          </span>
          {i < stages.length - 1 && (
            <span className="text-line-strong" aria-hidden="true">
              →
            </span>
          )}
        </span>
      ))}
    </div>
  );
}

function LifecyclePanel() {
  const [idx, setIdx] = useState(0);
  const example = examples[idx];

  const handleComplete = useCallback(() => {
    setIdx((p) => (p + 1) % examples.length);
  }, []);

  const { step, thinking } = useReveal(example, handleComplete);
  const visible = example.turns.slice(0, step);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.45 }}
      className="relative bg-surface border border-line rounded-md p-5 lg:p-6 flex flex-col"
      style={{ minHeight: 600 }}
    >
      <span className="reg" style={{ top: -7, left: -7 }} />
      <span className="reg" style={{ top: -7, right: -7 }} />
      <span className="reg" style={{ bottom: -7, left: -7 }} />
      <span className="reg" style={{ bottom: -7, right: -7 }} />

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-3">
        {examples.map((ex, i) => {
          const active = i === idx;
          return (
            <button
              key={ex.id}
              onClick={() => setIdx(i)}
              className={cn(
                "px-2.5 py-1 rounded-[3px] font-mono text-[10.5px] uppercase tracking-[0.04em] transition-colors",
                active
                  ? "bg-bg text-ink border border-line"
                  : "text-ink-subtle hover:text-ink"
              )}
            >
              {ex.label}
            </button>
          );
        })}
        <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.06em] text-brand">
          <span className="inline-block w-[7px] h-[7px] rounded-full bg-brand pulse-led" />
          live
        </span>
      </div>

      {/* Head */}
      <div className="flex items-center justify-between pb-3 border-b border-dashed border-line mb-4 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
        <span>{example.meta}</span>
        <span className="text-ink-subtle">
          {step}/{example.turns.length}
        </span>
      </div>

      {/* Stage rail */}
      <StageRail stages={example.stages} />

      {/* Turns */}
      <div className="flex-1 space-y-3.5">
        <AnimatePresence initial={false}>
          {visible.map((turn, i) => (
            <TurnRow key={`${idx}-${i}`} turn={turn} />
          ))}
          {thinking && <ThinkingRow key={`${idx}-thinking`} />}
        </AnimatePresence>
      </div>

      {/* Foot */}
      <div className="mt-5 pt-3 border-t border-dashed border-line flex items-center justify-between font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle">
        <span className="inline-flex items-center gap-1.5">
          <Mic size={11} className="text-brand" />
          voice ·
          <MessageSquare size={11} className="text-ink-muted ml-0.5" />
          chat ·
          <span className="text-ink-muted">⌘ K</span>
        </span>
        <span>30+ tools · cited traces</span>
      </div>
    </motion.div>
  );
}

/* ── Hero ────────────────────────────────────────────────────────── */

export function Hero() {
  return (
    <section className="relative pt-28 lg:pt-32 pb-16 lg:pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-12 lg:gap-14 items-stretch relative">
          <span className="reg hidden lg:block" style={{ top: 56, left: -22 }} />
          <span className="reg hidden lg:block" style={{ top: 56, right: -22 }} />

          {/* Left — copy */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="inline-flex items-center gap-2.5 mb-9 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted"
            >
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                01
              </span>
              <span>Built for screening labs and biotech R&amp;D</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.2 }}
              className="text-[48px] sm:text-[64px] lg:text-[80px] xl:text-[88px] leading-[0.98] tracking-[-0.04em] text-ink"
            >
              <span className="font-light">An agentic</span>
              <br />
              <span className="font-light">co-scientist</span>
              <br />
              <span className="relative inline-block font-bold text-brand">
                <span className="relative z-10">for the wet lab.</span>
                <span
                  aria-hidden="true"
                  className="absolute left-0 right-0 bottom-[2px] h-[6px] bg-brand-soft -z-0"
                />
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.35 }}
              className="mt-8 max-w-xl text-[16.5px] leading-[1.55] text-ink-muted"
            >
              Resonantia plans your experiments, designs your plate maps, fits
              your curves, and drafts your notebook entries. Talk to it by{" "}
              <strong className="text-ink font-medium">chat or voice</strong> —
              every action cited, every decision yours to approve.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.5 }}
              className="mt-9 flex flex-col sm:flex-row gap-3"
            >
              <a
                href="mailto:hello@resonantia.io?subject=Resonantia · Design partner inquiry"
                className="inline-flex items-center justify-center gap-2.5 px-[18px] py-3 bg-brand text-white text-[13.5px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
                style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
              >
                Contact us
                <span className="font-mono text-[14px] leading-none">→</span>
              </a>
              <a
                href="#console"
                className="inline-flex items-center justify-center gap-2.5 px-[18px] py-3 text-[13.5px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors"
              >
                See how it works
                <span className="font-mono text-[14px] leading-none">↓</span>
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.65 }}
              className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-5 pt-5 border-t border-dashed border-line-strong"
            >
              <HeroStat k="Plate formats" v="96 · 384" />
              <HeroStat k="Worklists" v="Echo · Hamilton · OT-2" />
              <HeroStat k="Modes" v="chat · voice · plan" />
              <HeroStat
                k="Design partners"
                v="accepting applications"
              />
            </motion.div>
          </div>

          {/* Right — animated lifecycle conversation */}
          <LifecyclePanel />
        </div>
      </div>
    </section>
  );
}

function HeroStat({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div>
      <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
        {k}
      </div>
      <div className="mt-1 text-[15px] font-semibold tracking-[-0.01em] text-ink">
        {v}
      </div>
    </div>
  );
}

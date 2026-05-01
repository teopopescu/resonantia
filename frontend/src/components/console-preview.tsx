"use client";

import { motion } from "framer-motion";
import {
  MessageSquare,
  LayoutGrid,
  Eye,
  FlaskConical,
  BookOpen,
  ClipboardList,
  BarChart3,
  Settings,
  ChevronLeft,
  Plus,
  Paperclip,
  Box,
  Sparkles,
  Mic,
  SendHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ── Console preview — section 02 ──
 * Mirrors the actual lab shell users see post-auth: 3 panes (rail · conversations · canvas).
 * No invented agent log, no fake tasks, no personalized greeting copy — just the empty
 * state of the chat interface, which is what /lab actually renders.
 */

function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <span
      className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[5px] rounded-[5px] bg-surface border border-line-strong"
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

const railItems = [
  { icon: MessageSquare, active: true },
  { icon: LayoutGrid },
  { icon: Eye },
  { icon: FlaskConical },
  { icon: BookOpen },
  { icon: ClipboardList },
  { icon: BarChart3 },
];

const conversations = [
  { title: "IC50 fit · staurosporine round 1", time: "2h ago", active: true },
  { title: "Cherry-pick 24 hits → 384", time: "yesterday" },
  { title: "Microscopy QC · Plate A", time: "2d ago" },
  { title: "Reagent expiry audit · Q1", time: "4d ago" },
];

export function ConsolePreview() {
  return (
    <section id="console" className="relative py-24 lg:py-28 border-t border-line">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section head */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-12 items-end mb-10"
        >
          <div>
            <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                02
              </span>
              <span>Console · agent home</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-[1.05] tracking-[-0.03em] text-ink">
              An agent that <span className="text-brand">listens</span>
              <br />
              before it acts.
            </h2>
          </div>
          <p className="text-[15.5px] text-ink-muted leading-relaxed max-w-[42ch] md:justify-self-end">
            One surface. The agent knows your plates, samples, and microscopy —
            and writes results back to your notebook with{" "}
            <strong className="text-ink font-medium">cited tool calls</strong>.
          </p>
        </motion.div>

        {/* App preview — 3 panes (rail · conversations · canvas) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="rounded-md border border-line bg-surface overflow-hidden"
          style={{
            boxShadow:
              "0 1px 2px rgba(20,16,10,.04), 0 12px 28px -16px rgba(20,16,10,.08)",
          }}
        >
          <div
            className="grid"
            style={{ gridTemplateColumns: "56px 260px 1fr", minHeight: 480 }}
          >
            {/* Rail */}
            <aside className="bg-bg border-r border-line flex flex-col items-center py-4 gap-1">
              <div className="mb-4">
                <BrandMark />
              </div>
              {railItems.map((item, i) => {
                const Icon = item.icon;
                return (
                  <span
                    key={i}
                    className={cn(
                      "w-10 h-10 rounded-md flex items-center justify-center",
                      item.active
                        ? "bg-brand-soft text-brand"
                        : "text-ink-muted"
                    )}
                    style={
                      item.active
                        ? { boxShadow: "inset 0 0 0 1px rgba(31, 77, 58, 0.25)" }
                        : undefined
                    }
                  >
                    <Icon size={17} strokeWidth={item.active ? 2 : 1.6} />
                  </span>
                );
              })}
              <div className="flex-1" />
              <span className="w-10 h-10 rounded-md flex items-center justify-center text-ink-muted">
                <Settings size={17} strokeWidth={1.6} />
              </span>
              <span className="w-7 h-7 rounded-full bg-ink text-bg font-mono text-[11px] font-semibold flex items-center justify-center mt-1">
                B
              </span>
            </aside>

            {/* Conversations panel */}
            <aside className="bg-bg border-r border-line flex flex-col">
              <div className="px-4 pt-4 pb-3 flex items-center justify-between">
                <span className="font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle">
                  Conversations
                </span>
                <span className="p-1 text-ink-subtle">
                  <ChevronLeft size={14} />
                </span>
              </div>
              <div className="px-4 pb-2">
                <div className="px-3 py-2 rounded-[3px] border border-line bg-surface font-mono text-[11.5px] text-ink-subtle">
                  ⌕ search conversations…
                </div>
              </div>
              <div className="flex-1 px-2 pt-1 overflow-hidden">
                {conversations.map((c, i) => (
                  <div
                    key={i}
                    className={cn(
                      "px-3 py-2.5 rounded-[3px] mb-0.5",
                      c.active && "bg-surface"
                    )}
                    style={
                      c.active
                        ? {
                            boxShadow:
                              "inset 2px 0 0 0 var(--color-brand), inset 0 0 0 1px var(--color-line)",
                          }
                        : undefined
                    }
                  >
                    <div
                      className={cn(
                        "text-[13px] leading-snug truncate",
                        c.active ? "text-brand font-medium" : "text-ink"
                      )}
                    >
                      {c.title}
                    </div>
                    <div className="font-mono text-[10.5px] tracking-[0.02em] text-ink-subtle mt-1">
                      {c.time}
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-3 py-3 border-t border-line">
                <button className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted border border-dashed border-line-strong rounded-[3px]">
                  <Plus size={12} />
                  new chat
                </button>
              </div>
            </aside>

            {/* Canvas — actual chat empty state */}
            <main className="bg-surface flex flex-col">
              <div className="flex-1 flex items-center px-10">
                <div className="max-w-xl">
                  <BrandMark size={40} />
                  <div className="mt-5 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                    <span className="text-brand">›</span> agent · ready
                  </div>
                  <h3 className="mt-3 text-[30px] font-semibold tracking-[-0.025em] leading-[1.1] text-ink">
                    What would you like to{" "}
                    <span className="text-brand">run</span> on the bench?
                  </h3>
                  <p className="mt-3 text-[14.5px] text-ink-muted leading-relaxed">
                    Design plate maps, fit dose-response curves, look up
                    samples, browse microscopy.
                  </p>
                </div>
              </div>

              {/* Composer mock */}
              <div className="px-10 pb-8">
                <div className="bg-bg border border-line-strong rounded-[5px]">
                  <div className="px-4 py-3.5 text-[14px] text-ink-subtle">
                    Ask the lab — fit ic50 plate A row B and write to ELN…
                  </div>
                  <div className="flex items-center justify-between px-2 py-2 border-t border-line">
                    <div className="flex gap-0.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-muted">
                      <span className="px-2 py-1 inline-flex items-center gap-1.5">
                        <Paperclip size={12} />
                      </span>
                      <span className="px-2 py-1 inline-flex items-center gap-1.5">
                        <Mic size={12} />
                      </span>
                      <span className="px-2 py-1 inline-flex items-center gap-1.5">
                        <Box size={12} /> resource
                      </span>
                      <span className="px-2 py-1 inline-flex items-center gap-1.5">
                        <Sparkles size={12} /> + skill
                      </span>
                    </div>
                    <span
                      className="w-7 h-7 rounded-[3px] bg-brand text-white inline-flex items-center justify-center"
                      style={{
                        boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)",
                      }}
                    >
                      <SendHorizontal size={13} />
                    </span>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

"use client";

import { useRef } from "react";
import { useLabStore } from "@/stores/lab-store";
import {
  LayoutGrid,
  BarChart3,
  Eye,
  FlaskConical,
  FileText,
  BookOpen,
  Compass,
} from "lucide-react";

const skills = [
  { id: "worklist-run", label: "Worklist Run", icon: LayoutGrid, prompt: "Build a validated liquid-handler run for " },
  { id: "data-analysis", label: "Results Analysis", icon: BarChart3, prompt: "Analyze the following run result data: " },
  { id: "microscopy", label: "Microscopy", icon: Eye, prompt: "Help me analyze microscopy images from " },
  { id: "sample-tracking", label: "Sample Tracking", icon: FlaskConical, prompt: "Look up information about sample " },
  { id: "protocol-design", label: "Protocol Design", icon: FileText, prompt: "Design an experimental protocol for " },
  { id: "run-record", label: "Run Record", icon: BookOpen, prompt: "Draft a run record for " },
  { id: "explore", label: "Explore", icon: Compass, prompt: "What can you help me with?" },
];

export default function SkillBar() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const setPendingPrompt = useLabStore((s) => s.setPendingPrompt);

  return (
    <div className="relative">
      <div
        ref={scrollRef}
        className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {skills.map((skill) => {
          const Icon = skill.icon;
          return (
            <button
              key={skill.id}
              onClick={() => setPendingPrompt(skill.prompt)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-[3px] font-mono text-[11px] uppercase tracking-[0.04em] whitespace-nowrap transition-colors duration-150 border bg-surface border-line text-ink-muted hover:text-ink hover:border-line-strong active:bg-brand-soft active:border-brand/30 active:text-brand"
            >
              <Icon size={13} strokeWidth={1.6} />
              {skill.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

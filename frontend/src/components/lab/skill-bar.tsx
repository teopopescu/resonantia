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
  { id: "plate-mapping", label: "Plate Mapping", icon: LayoutGrid, prompt: "Help me design a plate map for " },
  { id: "data-analysis", label: "Data Analysis", icon: BarChart3, prompt: "Analyze the following experimental data: " },
  { id: "microscopy", label: "Microscopy", icon: Eye, prompt: "Help me analyze microscopy images from " },
  { id: "sample-tracking", label: "Sample Tracking", icon: FlaskConical, prompt: "Look up information about sample " },
  { id: "protocol-design", label: "Protocol Design", icon: FileText, prompt: "Design an experimental protocol for " },
  { id: "eln-entry", label: "Notebook", icon: BookOpen, prompt: "Create an ELN entry for " },
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
              className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-150 border bg-surface border-border text-muted hover:text-charcoal hover:border-amber/20 active:bg-amber/15 active:border-amber/30 active:text-charcoal"
            >
              <Icon size={14} strokeWidth={1.5} />
              {skill.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

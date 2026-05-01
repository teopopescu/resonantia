"use client";

import { useState, useCallback } from "react";
import {
  Bold,
  Italic,
  Heading2,
  List,
  Link2,
  Image,
  Eye,
  Edit3,
} from "lucide-react";

interface ELNEditorProps {
  content: string;
  onChange: (content: string) => void;
}

function simpleMarkdownToHtml(md: string): string {
  let html = md
    // Headers
    .replace(/^### (.+)$/gm, '<h3 class="text-[15px] font-semibold text-ink mt-4 mb-2 tracking-[-0.01em]">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-[17px] font-semibold text-ink mt-5 mb-2 tracking-[-0.015em]">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-[20px] font-bold text-ink mt-6 mb-3 tracking-[-0.02em]">$1</h1>')
    // Bold and italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Links
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-brand underline underline-offset-2">$1</a>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="my-4 border-line" />')
    // Line breaks into paragraphs
    .replace(/\n\n/g, "</p><p class=\"text-[13px] text-ink leading-relaxed mb-2\">")
    .replace(/\n/g, "<br />");

  // Handle unordered lists (simple line-by-line)
  const lines = html.split("<br />");
  const processed: string[] = [];
  let inList = false;
  for (const line of lines) {
    if (line.trimStart().startsWith("- ")) {
      if (!inList) { processed.push('<ul class="my-2">'); inList = true; }
      processed.push(`<li class="ml-4 list-disc text-[13px] text-ink">${line.trimStart().slice(2)}</li>`);
    } else {
      if (inList) { processed.push("</ul>"); inList = false; }
      processed.push(line);
    }
  }
  if (inList) processed.push("</ul>");
  html = processed.join("");

  return `<div class="prose-resonantia"><p class="text-[13px] text-ink leading-relaxed mb-2">${html}</p></div>`;
}

const TOOLBAR_ITEMS = [
  { icon: Bold, label: "Bold", prefix: "**", suffix: "**" },
  { icon: Italic, label: "Italic", prefix: "*", suffix: "*" },
  { icon: Heading2, label: "Heading", prefix: "\n## ", suffix: "\n" },
  { icon: List, label: "List", prefix: "\n- ", suffix: "" },
  { icon: Link2, label: "Link", prefix: "[", suffix: "](url)" },
  { icon: Image, label: "Image", prefix: "![alt](", suffix: ")" },
];

export default function ELNEditor({ content, onChange }: ELNEditorProps) {
  const [mode, setMode] = useState<"edit" | "preview">("edit");

  const insertMarkdown = useCallback(
    (prefix: string, suffix: string) => {
      const textarea = document.getElementById("eln-textarea") as HTMLTextAreaElement | null;
      if (!textarea) return;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const selected = content.slice(start, end) || "text";
      const newContent = content.slice(0, start) + prefix + selected + suffix + content.slice(end);
      onChange(newContent);
      // Restore focus after React re-render
      requestAnimationFrame(() => {
        textarea.focus();
        textarea.setSelectionRange(start + prefix.length, start + prefix.length + selected.length);
      });
    },
    [content, onChange]
  );

  return (
    <div className="rounded-[5px] border border-line overflow-hidden bg-surface">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-2.5 py-2 border-b border-line bg-bg">
        <div className="flex items-center gap-0.5">
          {TOOLBAR_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                onClick={() => insertMarkdown(item.prefix, item.suffix)}
                title={item.label}
                className="p-1.5 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
              >
                <Icon size={13} />
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-0.5 bg-bg-sunk rounded-[3px] p-0.5 border border-line">
          <button
            onClick={() => setMode("edit")}
            className={`flex items-center gap-1 px-2 py-0.5 rounded-[2px] font-mono text-[10.5px] uppercase tracking-[0.04em] transition-colors ${
              mode === "edit"
                ? "bg-surface text-brand"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            <Edit3 size={11} />
            edit
          </button>
          <button
            onClick={() => setMode("preview")}
            className={`flex items-center gap-1 px-2 py-0.5 rounded-[2px] font-mono text-[10.5px] uppercase tracking-[0.04em] transition-colors ${
              mode === "preview"
                ? "bg-surface text-brand"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            <Eye size={11} />
            preview
          </button>
        </div>
      </div>

      {/* Content area */}
      {mode === "edit" ? (
        <textarea
          id="eln-textarea"
          value={content}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Write your lab notebook entry in Markdown…"
          className="w-full h-72 px-4 py-3 text-[13px] text-ink bg-surface resize-none focus:outline-none font-mono placeholder:text-ink-subtle"
        />
      ) : (
        <div
          className="w-full h-72 px-4 py-3 overflow-auto"
          dangerouslySetInnerHTML={{ __html: simpleMarkdownToHtml(content) }}
        />
      )}
    </div>
  );
}

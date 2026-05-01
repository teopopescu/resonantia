"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLabStore } from "@/stores/lab-store";
import { useUser } from "@clerk/nextjs";
import { getActiveOrgId } from "@/lib/api";
import Link from "next/link";
import SkillBar from "./skill-bar";
import {
  Paperclip,
  Box,
  Sparkles,
  SendHorizontal,
  User,
  X,
  Upload,
  LayoutGrid,
  FlaskConical,
  Eye,
  Cog,
  BarChart3,
  Search,
  Crosshair,
  Microscope,
  BookOpen,
  Loader2,
  Download,
  Mic,
  ChevronDown,
  ChevronRight,
  Wrench,
} from "lucide-react";
import type { ToolCall } from "@/stores/lab-store";
import VoiceMode from "./voice-mode";
import { ElabFTWLogo, BenchlingLogo, DotmaticsLogo } from "@/components/icons/integration-logos";

/* ---------- Attachment type ---------- */
interface Attachment {
  file: File;
  id: string;
}

/* ---------- Uploaded file metadata (from backend) ---------- */
interface UploadedFile {
  id: string;
  filename: string;
  size: number;
  content_type: string;
  uploaded_at: string;
  download_url: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ---------- Tool name → friendly label ---------- */
const TOOL_LABELS: Record<string, string> = {
  lookup_sample: "Looking up sample",
  check_inventory: "Checking inventory",
  query_experiments: "Querying experiments",
  get_ic50_values: "Fetching IC50 values",
  fit_dose_response: "Fitting dose-response curve",
  normalize_plate: "Normalizing plate data",
  calculate_z_prime: "Calculating Z-prime",
  qpcr_analysis: "Running qPCR analysis",
  create_plate_map: "Creating plate map",
  cherry_pick: "Cherry-picking wells",
  serial_dilution: "Setting up serial dilution",
  generate_worklist: "Generating worklist",
  get_plate_map_details: "Loading plate map details",
  query_plate_maps: "Querying plate maps",
  browse_microscopy: "Browsing microscopy images",
  generate_montage: "Generating montage",
  create_eln_entry: "Creating ELN entry",
  query_eln_entries: "Searching ELN entries",
  get_eln_entry: "Loading ELN entry",
  submit_eln_entry: "Submitting ELN entry",
  create_protocol: "Creating protocol",
  query_protocols: "Searching protocols",
  check_protocol_inventory: "Checking protocol reagents",
  calculate_dilution: "Calculating dilution",
  design_next_experiment: "Designing next experiment",
  get_expiring_samples: "Finding expiring samples",
  get_sample_stats: "Getting inventory stats",
  search_literature: "Searching literature",
  list_files: "Listing files",
  read_file_contents: "Reading file",
};

/* ---------- Thinking Trace component ---------- */
function ThinkingTrace({ toolCalls }: { toolCalls: ToolCall[] }) {
  const [expanded, setExpanded] = useState(false);

  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="mb-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle hover:text-ink-muted transition-colors group"
      >
        {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        <Wrench size={10} className="opacity-70" />
        <span>
          <span className="text-brand">›</span> {toolCalls.length} tool{toolCalls.length > 1 ? "s" : ""}
        </span>
        <span className="opacity-0 group-hover:opacity-100 transition-opacity">
          · {expanded ? "hide" : "show"}
        </span>
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="mt-1.5 ml-3.5 space-y-1.5 border-l-2 border-brand/30 pl-3">
              {toolCalls.map((tc, i) => (
                <ToolCallStep key={tc.id || i} tc={tc} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ToolCallStep({ tc, index }: { tc: ToolCall; index: number }) {
  const [showInput, setShowInput] = useState(false);
  const label = TOOL_LABELS[tc.name] || tc.name.replace(/_/g, " ");
  const hasInput = tc.input && Object.keys(tc.input).length > 0;

  return (
    <div className="font-mono text-[11px] tracking-[0.01em]">
      <div className="flex items-center gap-1.5">
        <span className="w-4 h-4 rounded-[2px] bg-brand-soft border border-brand/30 flex items-center justify-center text-[9px] font-medium text-brand shrink-0">
          {index + 1}
        </span>
        <span className="text-ink">{label}</span>
        {hasInput && (
          <button
            onClick={() => setShowInput(!showInput)}
            className="text-[10px] uppercase tracking-[0.04em] text-ink-subtle hover:text-ink-muted transition-colors ml-1"
          >
            {showInput ? "· hide params" : "· params"}
          </button>
        )}
      </div>
      {showInput && hasInput && (
        <pre className="mt-1 ml-5 text-[10.5px] text-ink-muted bg-bg border border-line rounded-[3px] px-2 py-1.5 overflow-x-auto max-h-24 font-mono">
          {JSON.stringify(tc.input, null, 2)}
        </pre>
      )}
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + "B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + "KB";
  return (bytes / (1024 * 1024)).toFixed(1) + "MB";
}

const ACCEPTED_TYPES = ".csv,.xlsx,.tsv,.fcs,.tiff,.png,.jpg,.jpeg,.pdf,.txt";

/* ---------- Mentionable items for @ mentions ---------- */
const mentionItems: Array<{ category: string; label: string; icon?: React.ReactNode; comingSoon?: boolean }> = [
  { category: "Integrations", label: "eLabFTW", icon: <ElabFTWLogo size={16} /> },
  { category: "Integrations", label: "Benchling", icon: <BenchlingLogo size={16} />, comingSoon: true },
  { category: "Integrations", label: "Dotmatics", icon: <DotmaticsLogo size={16} />, comingSoon: true },
  { category: "Resources", label: "Plate Maps" },
  { category: "Resources", label: "Sample Inventory" },
  { category: "Resources", label: "Microscopy Images" },
  { category: "Resources", label: "ELN Notebook" },
  { category: "Resources", label: "Protocols" },
  { category: "Resources", label: "Processing Results" },
];

/* ---------- Skills for the dropdown ---------- */
const agentSkills = [
  { label: "Plate Mapping", desc: "Design and configure plate layouts", prompt: "Design a plate map: ", icon: LayoutGrid },
  { label: "Dose-Response Analysis", desc: "Fit curves and compute IC50/EC50", prompt: "Analyze dose-response data: ", icon: BarChart3 },
  { label: "Sample Lookup", desc: "Find sample info across inventories", prompt: "Look up sample: ", icon: Search },
  { label: "Plate Normalization", desc: "Normalize plate data with controls", prompt: "Normalize plate data: ", icon: Crosshair },
  { label: "Image Analysis", desc: "Segment and quantify microscopy images", prompt: "Analyze microscopy image: ", icon: Microscope },
  { label: "Protocol Design", desc: "Draft and optimize lab protocols", prompt: "Design a protocol for: ", icon: BookOpen },
];

/* ---------- Resource items ---------- */
const resourceItems = [
  { label: "Upload Data File", icon: Upload, action: "upload" as const },
  { label: "Plate Maps", icon: LayoutGrid, href: "/lab/plates" },
  { label: "Sample Inventory", icon: FlaskConical, href: "/lab/samples" },
  { label: "Microscopy Images", icon: Eye, href: "/lab/microscopy" },
  { label: "Processing Results", icon: Cog, href: "/lab/processing" },
];

/* ---------- Render message content with clickable file links ---------- */
// Matches our custom file link format: [file:filename](url){size:1.2MB}
const FILE_LINK_REGEX = /\[file:(.+?)\]\((.+?)\)\{size:(.+?)\}/g;
// Also matches the old plain-text format for backward compat
const OLD_ATTACHED_REGEX = /\[Attached: (.+?) \((.+?)\)\]/g;

function MessageContent({ content, role }: { content: string; role: string }) {
  // Check if content has file links
  const hasFileLinks = FILE_LINK_REGEX.test(content) || OLD_ATTACHED_REGEX.test(content);
  // Reset regex lastIndex after test
  FILE_LINK_REGEX.lastIndex = 0;
  OLD_ATTACHED_REGEX.lastIndex = 0;

  if (!hasFileLinks) {
    return <>{content}</>;
  }

  // Split content into parts: file links and plain text
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Parse with file link regex
  let match: RegExpExecArray | null;
  const allMatches: Array<{
    index: number;
    length: number;
    filename: string;
    url: string | null;
    size: string;
  }> = [];

  while ((match = FILE_LINK_REGEX.exec(content)) !== null) {
    allMatches.push({
      index: match.index,
      length: match[0].length,
      filename: match[1],
      url: match[2],
      size: match[3],
    });
  }
  FILE_LINK_REGEX.lastIndex = 0;

  // Also match old format
  while ((match = OLD_ATTACHED_REGEX.exec(content)) !== null) {
    allMatches.push({
      index: match.index,
      length: match[0].length,
      filename: match[1],
      url: null,
      size: match[2],
    });
  }
  OLD_ATTACHED_REGEX.lastIndex = 0;

  // Sort by position
  allMatches.sort((a, b) => a.index - b.index);

  for (const m of allMatches) {
    // Add text before this match
    if (m.index > lastIndex) {
      parts.push(content.slice(lastIndex, m.index));
    }
    // Add file chip
    const isUserMsg = role === "user";
    if (m.url) {
      parts.push(
        <a
          key={m.index}
          href={m.url}
          target="_blank"
          rel="noopener noreferrer"
          download
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors no-underline ${
            isUserMsg
              ? "bg-white/15 text-white hover:bg-white/25"
              : "bg-brand-soft text-brand border border-brand/30 hover:bg-brand-soft/70"
          }`}
        >
          <Download size={12} />
          <span className="max-w-[200px] truncate">{m.filename}</span>
          <span className="opacity-60">({m.size})</span>
        </a>
      );
    } else {
      parts.push(
        <span
          key={m.index}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs ${
            isUserMsg ? "bg-white/15 text-white" : "bg-bg-sunk text-ink"
          }`}
        >
          <Paperclip size={12} />
          <span>{m.filename}</span>
          <span className="opacity-60">({m.size})</span>
        </span>
      );
    }
    lastIndex = m.index + m.length;
  }

  // Remaining text after last match
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return <>{parts}</>;
}

export default function ChatInterface() {
  const {
    chatMessages,
    addMessage,
    pendingPrompt,
    setPendingPrompt,
    activeConversationId,
    setActiveConversation,
    addConversation,
    fetchConversations,
  } = useLabStore();
  const { user } = useUser();
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showResources, setShowResources] = useState(false);
  const [showSkills, setShowSkills] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [voiceModeActive, setVoiceModeActive] = useState(false);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState("");
  const [mentionStartIndex, setMentionStartIndex] = useState(-1);
  const mentionRef = useRef<HTMLDivElement>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resourceRef = useRef<HTMLDivElement>(null);
  const skillRef = useRef<HTMLDivElement>(null);

  const hasMessages = chatMessages.length > 0;

  // Watch for pendingPrompt changes from skill bar
  useEffect(() => {
    if (pendingPrompt) {
      setInput(pendingPrompt);
      setPendingPrompt(null);
      textareaRef.current?.focus();
    }
  }, [pendingPrompt, setPendingPrompt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (resourceRef.current && !resourceRef.current.contains(e.target as Node)) {
        setShowResources(false);
      }
      if (skillRef.current && !skillRef.current.contains(e.target as Node)) {
        setShowSkills(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // File handling
  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files) return;
    const newAttachments: Attachment[] = Array.from(files).map((file) => ({
      file,
      id: Math.random().toString(36).substring(2, 10),
    }));
    setAttachments((prev) => [...prev, ...newAttachments]);
    // Reset input so the same file can be re-selected
    e.target.value = "";
  }

  function removeAttachment(id: string) {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  }

  function triggerFileUpload() {
    fileInputRef.current?.click();
  }

  async function uploadFiles(files: Attachment[]): Promise<UploadedFile[]> {
    const formData = new FormData();
    for (const att of files) {
      formData.append("files", att.file);
    }
    const res = await fetch(`${API_URL}/api/v1/files/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status}`);
    }
    return res.json();
  }

  async function handleSend() {
    const text = input.trim();
    if (!text && attachments.length === 0) return;

    // If there are attachments, upload them first
    let uploadedFiles: UploadedFile[] = [];
    if (attachments.length > 0) {
      setIsUploading(true);
      try {
        uploadedFiles = await uploadFiles(attachments);
      } catch (err) {
        console.error("File upload error:", err);
        addMessage(
          "system",
          "Failed to upload files. Please try again."
        );
        setIsUploading(false);
        return;
      }
      setIsUploading(false);
    }

    // Build message content with clickable attachment links
    let content = text;
    if (uploadedFiles.length > 0) {
      const attachmentLines = uploadedFiles
        .map(
          (f) =>
            `[file:${f.filename}](${API_URL}${f.download_url}){size:${formatFileSize(f.size)}}`
        )
        .join("\n");
      content = attachmentLines + (text ? "\n\n" + text : "");
    }

    addMessage("user", content);
    setInput("");
    setAttachments([]);

    // Call real backend chat endpoint
    setIsLoading(true);
    try {
      const activeOrgId = getActiveOrgId();
      const res = await fetch(`${API_URL}/api/v1/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Org-Id": activeOrgId,
        },
        body: JSON.stringify({
          message: content,
          conversation_id: activeConversationId || "new",
          clerk_user_id: user?.id,
          org_id: activeOrgId,
          // Image-typed uploads are encoded as vision content blocks
          // by the backend; non-image files pass through as text URLs
          // and are read on demand via the read_file_contents tool.
          attachments: uploadedFiles.length > 0 ? uploadedFiles.map((f) => f.id) : undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        addMessage("assistant", data.message, data.tool_calls || undefined);
        // If the backend returned a new conversation, add it to the list
        if (data.conversation_id && !activeConversationId) {
          const newConv = {
            id: data.conversation_id,
            title: data.conversation_title || content.slice(0, 50) || "New Chat",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
          addConversation(newConv);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        addMessage("assistant", `Error: ${(err as any).detail || "Could not process your request. Please try again."}`);
      }
    } catch {
      addMessage("assistant", "Could not reach the server. Please ensure the backend is running.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (showMentions && e.key === "Escape") {
      e.preventDefault();
      setShowMentions(false);
      setMentionFilter("");
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) {
      if (showMentions) {
        // If mentions are open, close them instead of sending
        setShowMentions(false);
        setMentionFilter("");
        return;
      }
      e.preventDefault();
      handleSend();
    }
  }

  // Insert skill prompt
  const insertSkillPrompt = useCallback((prompt: string) => {
    setInput(prompt);
    setShowSkills(false);
    textareaRef.current?.focus();
  }, []);

  // Filtered mention items
  const filteredMentions = mentionItems.filter((item) =>
    item.label.toLowerCase().includes(mentionFilter.toLowerCase())
  );

  // Group filtered mentions by category
  const groupedMentions = filteredMentions.reduce<Record<string, typeof mentionItems>>((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  function handleMentionSelect(label: string) {
    // Replace @filterText with @Label
    const before = input.slice(0, mentionStartIndex);
    const after = input.slice(textareaRef.current?.selectionStart ?? input.length);
    setInput(before + "@" + label + " " + after);
    setShowMentions(false);
    setMentionFilter("");
    setMentionStartIndex(-1);
    textareaRef.current?.focus();
  }

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const val = e.target.value;
    const cursorPos = e.target.selectionStart;
    setInput(val);

    // Detect @ mentions
    if (cursorPos > 0) {
      // Find the last @ before cursor
      const textBeforeCursor = val.slice(0, cursorPos);
      const lastAtIndex = textBeforeCursor.lastIndexOf("@");

      if (lastAtIndex !== -1) {
        const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
        // Only show if no spaces in the filter (or it's empty)
        if (!textAfterAt.includes("\n")) {
          setShowMentions(true);
          setMentionFilter(textAfterAt);
          setMentionStartIndex(lastAtIndex);
          return;
        }
      }
    }
    setShowMentions(false);
    setMentionFilter("");
    setMentionStartIndex(-1);
  }

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
    }
  }, [input]);

  return (
    <div className="flex-1 flex flex-col h-full">
      {hasMessages ? (
        /* Message thread view */
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {chatMessages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex gap-3 ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <span
                    className="shrink-0 inline-grid grid-cols-2 grid-rows-2 gap-[2px] p-[4px] rounded-[4px] bg-surface border border-line-strong mt-0.5"
                    style={{ width: 28, height: 28 }}
                    aria-hidden="true"
                  >
                    <span className="rounded-full bg-ink-subtle" />
                    <span className="rounded-full bg-ink-subtle" />
                    <span className="rounded-full bg-ink-subtle" />
                    <span className="rounded-full bg-brand" />
                  </span>
                )}
                <div className="max-w-[75%]">
                  {msg.role === "assistant" && msg.toolCalls && msg.toolCalls.length > 0 && (
                    <ThinkingTrace toolCalls={msg.toolCalls} />
                  )}
                  <div
                    className={`px-4 py-3 rounded-md text-[13.5px] leading-relaxed whitespace-pre-wrap ${
                      msg.role === "user"
                        ? "bg-brand text-white"
                        : msg.role === "system"
                        ? "bg-mch-soft border border-mch/30 text-mch"
                        : "bg-bg border border-line"
                    }`}
                    style={
                      msg.role === "user"
                        ? { boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }
                        : undefined
                    }
                  >
                    <MessageContent content={msg.content} role={msg.role} />
                  </div>
                </div>
                {msg.role === "user" && (
                  <div className="shrink-0 w-7 h-7 rounded-[4px] bg-bg-sunk border border-line flex items-center justify-center mt-0.5">
                    <User size={14} className="text-ink-muted" />
                  </div>
                )}
              </motion.div>
            ))}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 justify-start"
              >
                <span
                  className="shrink-0 inline-grid grid-cols-2 grid-rows-2 gap-[2px] p-[4px] rounded-[4px] bg-surface border border-line-strong mt-0.5"
                  style={{ width: 28, height: 28 }}
                  aria-hidden="true"
                >
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-ink-subtle" />
                  <span className="rounded-full bg-brand" />
                </span>
                <div className="px-4 py-3 rounded-md bg-bg border border-line">
                  <div className="flex items-center gap-2 font-mono text-[11px] tracking-[0.02em] text-ink-muted">
                    <Loader2 size={12} className="animate-spin text-brand" />
                    <span>thinking…</span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      ) : (
        /* Empty state / greeting */
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-2xl w-full">
            {/* Brand mark */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="mb-6"
            >
              <span
                className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[6px] rounded-[5px] bg-surface border border-line-strong"
                style={{ width: 40, height: 40 }}
                aria-hidden="true"
              >
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-ink-subtle" />
                <span className="rounded-full bg-brand" />
              </span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle mb-3"
            >
              <span className="text-brand">›</span> agent · ready · 32 tools
              wired
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.4 }}
              className="text-[32px] font-semibold tracking-[-0.025em] leading-[1.1] text-ink mb-3"
            >
              What would you like to{" "}
              <span className="text-brand">run</span> on the bench?
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.4 }}
              className="text-[15px] text-ink-muted leading-relaxed max-w-lg"
            >
              Design plate maps, fit dose-response curves, look up samples,
              browse microscopy. Every action is cited and written back to your
              notebook.
            </motion.p>
          </div>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Input area (always visible at bottom) */}
      <div className="shrink-0 px-6 pb-5">
        <AnimatePresence mode="wait">
          {voiceModeActive ? (
            <motion.div
              key="voice"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.2 }}
              className="max-w-3xl mx-auto relative"
            >
              <VoiceMode onExit={() => setVoiceModeActive(false)} />
            </motion.div>
          ) : (
            <motion.div
              key="text"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.2 }}
              className="max-w-3xl mx-auto"
            >
              {/* Chat input box */}
              <div className="rounded-[5px] border border-line-strong bg-surface focus-within:border-brand/50 transition-colors">
                {/* Attachment chips */}
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 px-4 pt-3">
                    {isUploading && (
                      <div className="flex items-center gap-2 px-2.5 py-1 rounded-[3px] bg-brand-soft border border-brand/30 font-mono text-[11px] tracking-[0.02em] text-brand">
                        <Loader2 size={11} className="animate-spin" />
                        <span>uploading {attachments.length} file{attachments.length > 1 ? "s" : ""}…</span>
                      </div>
                    )}
                    {attachments.map((att) => (
                      <div
                        key={att.id}
                        className="flex items-center gap-2 px-2.5 py-1 rounded-[3px] bg-bg border border-line font-mono text-[11px] tracking-[0.02em] text-ink"
                      >
                        <Paperclip size={11} className="text-ink-subtle" />
                        <span className="max-w-[160px] truncate">{att.file.name}</span>
                        <span className="text-ink-subtle">{formatFileSize(att.file.size)}</span>
                        <button
                          onClick={() => removeAttachment(att.id)}
                          className="text-ink-subtle hover:text-mch transition-colors"
                          disabled={isUploading}
                        >
                          <X size={11} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* @ Mention dropdown */}
                <div ref={mentionRef} className="relative">
                  <AnimatePresence>
                    {showMentions && filteredMentions.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: 4, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 4, scale: 0.97 }}
                        transition={{ duration: 0.15 }}
                        className="absolute bottom-full left-4 mb-1 w-64 max-h-64 overflow-y-auto rounded-[5px] border border-line bg-surface shadow-md z-50"
                      >
                        {Object.entries(groupedMentions).map(([category, items]) => (
                          <div key={category}>
                            <div className="px-3 pt-2.5 pb-1 font-mono text-[10px] font-medium uppercase tracking-[0.06em] text-ink-subtle">
                              @{category}
                            </div>
                            {items.map((item) => (
                              <button
                                key={item.label}
                                onClick={() => handleMentionSelect(item.label)}
                                className="flex items-center gap-2 w-full px-3 py-2 text-[12.5px] text-ink hover:bg-bg transition-colors text-left"
                              >
                                {item.icon && <span className="shrink-0 flex items-center">{item.icon}</span>}
                                <span className="font-medium">{item.label}</span>
                                {item.comingSoon && (
                                  <span className="ml-auto font-mono text-[10px] tracking-[0.02em] uppercase text-ink-subtle">coming soon</span>
                                )}
                              </button>
                            ))}
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="ask the lab — fit ic50 plate A row B and write to ELN…"
                  rows={1}
                  className="w-full px-4 pt-4 pb-2 text-[13.5px] bg-transparent resize-none focus:outline-none placeholder:text-ink-subtle"
                />

                {/* Toolbar */}
                <div className="flex items-center justify-between px-2.5 pb-2.5">
                  <div className="flex items-center gap-0.5">
                    {/* Paperclip / File upload */}
                    <button
                      onClick={triggerFileUpload}
                      className="flex items-center gap-1.5 px-2 py-1.5 rounded-[3px] font-mono text-[11px] tracking-[0.02em] uppercase text-ink-muted hover:text-ink hover:bg-bg transition-colors"
                      title="Attach file"
                    >
                      <Paperclip size={13} />
                    </button>

                    {/* Voice mode */}
                    <button
                      onClick={() => setVoiceModeActive(true)}
                      className="flex items-center gap-1.5 px-2 py-1.5 rounded-[3px] font-mono text-[11px] tracking-[0.02em] uppercase text-ink-muted hover:text-brand hover:bg-brand-soft transition-colors"
                      title="Voice mode"
                    >
                      <Mic size={13} />
                    </button>

                    {/* Resource dropdown */}
                    <div ref={resourceRef} className="relative">
                      <button
                        onClick={() => {
                          setShowResources(!showResources);
                          setShowSkills(false);
                        }}
                        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[3px] font-mono text-[11px] tracking-[0.02em] uppercase transition-colors ${
                          showResources
                            ? "text-brand bg-brand-soft"
                            : "text-ink-muted hover:text-ink hover:bg-bg"
                        }`}
                      >
                        <Box size={13} />
                        <span>resource</span>
                      </button>
                      <AnimatePresence>
                        {showResources && (
                          <motion.div
                            initial={{ opacity: 0, y: 4, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 4, scale: 0.97 }}
                            transition={{ duration: 0.15 }}
                            className="absolute bottom-full left-0 mb-2 w-56 rounded-[5px] border border-line bg-surface shadow-md z-50 overflow-hidden"
                          >
                            {resourceItems.map((item) => {
                              const Icon = item.icon;
                              if (item.action === "upload") {
                                return (
                                  <button
                                    key={item.label}
                                    onClick={() => {
                                      triggerFileUpload();
                                      setShowResources(false);
                                    }}
                                    className="flex items-center gap-3 w-full px-4 py-2.5 text-[12.5px] text-ink hover:bg-bg transition-colors text-left"
                                  >
                                    <Icon size={13} className="text-ink-subtle" />
                                    {item.label}
                                  </button>
                                );
                              }
                              return (
                                <Link
                                  key={item.label}
                                  href={item.href!}
                                  onClick={() => setShowResources(false)}
                                  className="flex items-center gap-3 w-full px-4 py-2.5 text-[12.5px] text-ink hover:bg-bg transition-colors"
                                >
                                  <Icon size={13} className="text-ink-subtle" />
                                  {item.label}
                                </Link>
                              );
                            })}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Skill dropdown */}
                    <div ref={skillRef} className="relative">
                      <button
                        onClick={() => {
                          setShowSkills(!showSkills);
                          setShowResources(false);
                        }}
                        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[3px] font-mono text-[11px] tracking-[0.02em] uppercase transition-colors ${
                          showSkills
                            ? "text-brand bg-brand-soft"
                            : "text-ink-muted hover:text-ink hover:bg-bg"
                        }`}
                      >
                        <Sparkles size={13} />
                        <span>+ skill</span>
                      </button>
                      <AnimatePresence>
                        {showSkills && (
                          <motion.div
                            initial={{ opacity: 0, y: 4, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 4, scale: 0.97 }}
                            transition={{ duration: 0.15 }}
                            className="absolute bottom-full left-0 mb-2 w-72 rounded-[5px] border border-line bg-surface shadow-md z-50 overflow-hidden"
                          >
                            {agentSkills.map((skill) => {
                              const Icon = skill.icon;
                              return (
                                <button
                                  key={skill.label}
                                  onClick={() => insertSkillPrompt(skill.prompt)}
                                  className="flex items-start gap-3 w-full px-4 py-3 hover:bg-bg transition-colors text-left"
                                >
                                  <Icon size={14} className="text-brand mt-0.5 shrink-0" />
                                  <div>
                                    <div className="text-[12.5px] font-medium text-ink">
                                      {skill.label}
                                    </div>
                                    <div className="font-mono text-[11px] tracking-[0.02em] text-ink-muted mt-0.5">
                                      {skill.desc}
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSend}
                      disabled={isUploading || isLoading || (!input.trim() && attachments.length === 0)}
                      className={`flex items-center justify-center w-8 h-8 rounded-[3px] transition-all ${
                        isUploading || isLoading
                          ? "bg-brand/70 text-white cursor-wait"
                          : input.trim() || attachments.length > 0
                          ? "bg-brand text-white hover:bg-brand-strong"
                          : "bg-bg-sunk text-ink-subtle cursor-not-allowed"
                      }`}
                      style={
                        input.trim() || attachments.length > 0
                          ? { boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }
                          : undefined
                      }
                    >
                      {isUploading ? (
                        <Loader2 size={15} className="animate-spin" />
                      ) : (
                        <SendHorizontal size={15} />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Skill categories */}
              {!hasMessages && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35, duration: 0.4 }}
                  className="mt-4"
                >
                  <SkillBar />
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </div>
  );
}

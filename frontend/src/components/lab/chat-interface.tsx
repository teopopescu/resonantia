"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLabStore } from "@/stores/lab-store";
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
} from "lucide-react";
import VoiceMode from "./voice-mode";

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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + "B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + "KB";
  return (bytes / (1024 * 1024)).toFixed(1) + "MB";
}

const ACCEPTED_TYPES = ".csv,.xlsx,.tsv,.fcs,.tiff,.png,.jpg,.jpeg,.pdf,.txt";

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
              : "bg-amber/10 text-amber border border-amber/20 hover:bg-amber/20"
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
            isUserMsg ? "bg-white/15 text-white" : "bg-charcoal/5 text-charcoal"
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
  const { chatMessages, addMessage, pendingPrompt, setPendingPrompt } = useLabStore();
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showResources, setShowResources] = useState(false);
  const [showSkills, setShowSkills] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [voiceModeActive, setVoiceModeActive] = useState(false);

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
      const res = await fetch(`${API_URL}/api/v1/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, conversation_id: "default" }),
      });
      if (res.ok) {
        const data = await res.json();
        addMessage("assistant", data.message);
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
    if (e.key === "Enter" && !e.shiftKey) {
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
                  <div className="shrink-0 w-8 h-8 rounded-lg bg-amber/15 flex items-center justify-center mt-0.5">
                    <span className="text-xs font-serif font-bold text-amber">R</span>
                  </div>
                )}
                <div
                  className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-charcoal text-white rounded-br-md"
                      : msg.role === "system"
                      ? "bg-red-50 border border-red-200 text-red-700 rounded-bl-md"
                      : "bg-cream border border-border rounded-bl-md"
                  }`}
                >
                  <MessageContent content={msg.content} role={msg.role} />
                </div>
                {msg.role === "user" && (
                  <div className="shrink-0 w-8 h-8 rounded-lg bg-charcoal/10 flex items-center justify-center mt-0.5">
                    <User size={16} className="text-charcoal/60" />
                  </div>
                )}
              </motion.div>
            ))}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="shrink-0 w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center mt-0.5 overflow-hidden">
                  <img src="/resonantia-logo.png" alt="Resonantia" className="w-6 h-6 object-contain" />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-cream border border-border rounded-bl-md">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-muted/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-muted/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-muted/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      ) : (
        /* Empty state / greeting */
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-2xl w-full text-center">
            {/* Logo mark */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="mx-auto w-16 h-16 rounded-2xl bg-amber/15 border border-amber/20 flex items-center justify-center mb-6"
            >
              <span className="text-2xl font-serif font-bold text-amber">
                R
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="text-3xl font-serif font-semibold text-charcoal mb-3"
            >
              Hi there,
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="text-base text-muted leading-relaxed max-w-lg mx-auto"
            >
              I&apos;m your lab assistant — ask me to design plate maps, fit
              dose-response curves, look up samples, or analyze your microscopy
              data.
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
              <div className="rounded-2xl border border-border bg-surface shadow-sm focus-within:border-amber/40 transition-colors">
                {/* Attachment chips */}
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 px-4 pt-3">
                    {isUploading && (
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber/10 border border-amber/20 text-xs text-amber">
                        <Loader2 size={12} className="animate-spin" />
                        <span>Uploading {attachments.length} file{attachments.length > 1 ? "s" : ""}...</span>
                      </div>
                    )}
                    {attachments.map((att) => (
                      <div
                        key={att.id}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cream border border-border text-xs text-charcoal"
                      >
                        <Paperclip size={12} className="text-muted" />
                        <span className="max-w-[160px] truncate">{att.file.name}</span>
                        <span className="text-muted">({formatFileSize(att.file.size)})</span>
                        <button
                          onClick={() => removeAttachment(att.id)}
                          className="text-muted hover:text-charcoal transition-colors"
                          disabled={isUploading}
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="What lab task can I help you with today?"
                  rows={1}
                  className="w-full px-4 pt-4 pb-2 text-sm bg-transparent resize-none focus:outline-none placeholder:text-muted/60"
                />

                {/* Toolbar */}
                <div className="flex items-center justify-between px-3 pb-3">
                  <div className="flex items-center gap-1">
                    {/* Paperclip / File upload */}
                    <button
                      onClick={triggerFileUpload}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-muted hover:text-charcoal hover:bg-cream transition-colors"
                      title="Attach file"
                    >
                      <Paperclip size={14} />
                    </button>

                    {/* Voice mode */}
                    <button
                      onClick={() => setVoiceModeActive(true)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-muted hover:text-amber hover:bg-amber/10 transition-colors"
                      title="Voice mode"
                    >
                      <Mic size={14} />
                    </button>

                    {/* Resource dropdown */}
                    <div ref={resourceRef} className="relative">
                      <button
                        onClick={() => {
                          setShowResources(!showResources);
                          setShowSkills(false);
                        }}
                        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                          showResources
                            ? "text-charcoal bg-cream"
                            : "text-muted hover:text-charcoal hover:bg-cream"
                        }`}
                      >
                        <Box size={14} />
                        <span>Resource</span>
                      </button>
                      <AnimatePresence>
                        {showResources && (
                          <motion.div
                            initial={{ opacity: 0, y: 4, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 4, scale: 0.97 }}
                            transition={{ duration: 0.15 }}
                            className="absolute bottom-full left-0 mb-2 w-56 rounded-xl border border-border bg-surface shadow-lg z-50 overflow-hidden"
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
                                    className="flex items-center gap-3 w-full px-4 py-2.5 text-xs text-charcoal hover:bg-cream transition-colors text-left"
                                  >
                                    <Icon size={14} className="text-muted" />
                                    {item.label}
                                  </button>
                                );
                              }
                              return (
                                <Link
                                  key={item.label}
                                  href={item.href!}
                                  onClick={() => setShowResources(false)}
                                  className="flex items-center gap-3 w-full px-4 py-2.5 text-xs text-charcoal hover:bg-cream transition-colors"
                                >
                                  <Icon size={14} className="text-muted" />
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
                        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                          showSkills
                            ? "text-charcoal bg-cream"
                            : "text-muted hover:text-charcoal hover:bg-cream"
                        }`}
                      >
                        <Sparkles size={14} />
                        <span>+ Skill</span>
                      </button>
                      <AnimatePresence>
                        {showSkills && (
                          <motion.div
                            initial={{ opacity: 0, y: 4, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 4, scale: 0.97 }}
                            transition={{ duration: 0.15 }}
                            className="absolute bottom-full left-0 mb-2 w-72 rounded-xl border border-border bg-surface shadow-lg z-50 overflow-hidden"
                          >
                            {agentSkills.map((skill) => {
                              const Icon = skill.icon;
                              return (
                                <button
                                  key={skill.label}
                                  onClick={() => insertSkillPrompt(skill.prompt)}
                                  className="flex items-start gap-3 w-full px-4 py-3 hover:bg-cream transition-colors text-left"
                                >
                                  <Icon size={14} className="text-amber mt-0.5 shrink-0" />
                                  <div>
                                    <div className="text-xs font-medium text-charcoal">
                                      {skill.label}
                                    </div>
                                    <div className="text-[11px] text-muted mt-0.5">
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
                      className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all ${
                        isUploading || isLoading
                          ? "bg-amber/60 text-charcoal cursor-wait"
                          : input.trim() || attachments.length > 0
                          ? "bg-amber text-charcoal hover:bg-amber-light shadow-sm"
                          : "bg-cream text-muted cursor-not-allowed"
                      }`}
                    >
                      {isUploading ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <SendHorizontal size={16} />
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

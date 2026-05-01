"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLabStore } from "@/stores/lab-store";
import {
  ChevronLeft,
  Search,
  Plus,
  X,
  MessageSquare,
  Pencil,
  Check,
} from "lucide-react";

function relativeDate(isoString: string) {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(isoString).toLocaleDateString();
}

export default function TaskPanel() {
  const {
    conversations,
    activeConversationId,
    sidebarCollapsed,
    fetchConversations,
    setActiveConversation,
    loadConversationMessages,
    startNewConversation,
    deleteConversation,
    renameConversation,
    toggleSidebar,
  } = useLabStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const editInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function handleSelectConversation(id: string) {
    if (editingId) return;
    setActiveConversation(id);
    loadConversationMessages(id);
  }

  function handleStartRename(id: string, currentTitle: string) {
    setEditingId(id);
    setEditTitle(currentTitle);
  }

  function handleFinishRename() {
    if (editingId && editTitle.trim()) {
      renameConversation(editingId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle("");
  }

  function handleRenameKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      handleFinishRename();
    } else if (e.key === "Escape") {
      setEditingId(null);
      setEditTitle("");
    }
  }

  return (
    <AnimatePresence initial={false}>
      {!sidebarCollapsed && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 320, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="shrink-0 bg-bg border-r border-line flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="px-4 pt-4 pb-2">
            <div className="flex items-center justify-between mb-2">
              <p className="font-mono text-[10.5px] font-medium tracking-[0.06em] text-ink-subtle uppercase">
                Conversations
              </p>
              <button
                onClick={toggleSidebar}
                className="p-1.5 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Search */}
            <div className="px-4 py-2">
              <div className="relative">
                <Search
                  size={13}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-subtle"
                />
                <input
                  type="text"
                  placeholder="search conversations…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 font-mono text-[12px] rounded-[3px] border border-line bg-surface text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle"
                />
              </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto px-2 pt-1">
              {filteredConversations.length === 0 && (
                <div className="flex flex-col items-center justify-center text-center px-4 py-12">
                  <div className="w-10 h-10 rounded-[4px] bg-surface border border-line flex items-center justify-center mb-3">
                    <MessageSquare size={18} className="text-ink-subtle" />
                  </div>
                  <p className="text-sm text-ink-muted">No conversations yet</p>
                  <p className="font-mono text-[11px] text-ink-subtle mt-1.5 tracking-[0.02em]">
                    start a new chat to begin
                  </p>
                </div>
              )}
              {filteredConversations.map((conv) => {
                const isActive = activeConversationId === conv.id;
                return (
                  <div
                    key={conv.id}
                    className={`group relative w-full text-left px-3 py-2.5 rounded-[3px] mb-0.5 cursor-pointer transition-colors ${
                      isActive
                        ? "bg-brand-soft"
                        : "hover:bg-bg-sunk"
                    }`}
                    style={
                      isActive
                        ? { boxShadow: "inset 2px 0 0 0 var(--color-brand)" }
                        : undefined
                    }
                    onClick={() => handleSelectConversation(conv.id)}
                  >
                    {editingId === conv.id ? (
                      <div className="flex items-center gap-1">
                        <input
                          ref={editInputRef}
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={handleRenameKeyDown}
                          onBlur={handleFinishRename}
                          className="flex-1 text-sm px-1.5 py-0.5 rounded-[3px] border border-brand/40 bg-surface text-ink focus:outline-none"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleFinishRename();
                          }}
                          className="p-0.5 text-brand hover:text-brand-strong"
                        >
                          <Check size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <p
                          className={`text-sm leading-snug truncate pr-12 ${
                            isActive
                              ? "text-brand font-medium"
                              : "text-ink"
                          }`}
                        >
                          {conv.title}
                        </p>
                        <p className="font-mono text-[10.5px] text-ink-subtle mt-1 tracking-[0.02em]">
                          {relativeDate(conv.updatedAt || conv.createdAt)}
                        </p>

                        {/* Hover actions */}
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-0.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartRename(conv.id, conv.title);
                            }}
                            className="p-1 rounded-[2px] text-ink-muted hover:text-ink hover:bg-surface transition-colors"
                            title="Rename"
                          >
                            <Pencil size={12} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteConversation(conv.id);
                            }}
                            className="p-1 rounded-[2px] text-ink-muted hover:text-mch hover:bg-mch-soft transition-colors"
                            title="Delete"
                          >
                            <X size={12} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* New Chat button */}
            <div className="px-3 py-3 border-t border-line">
              <button
                onClick={startNewConversation}
                className="flex items-center justify-center gap-2 w-full px-3 py-2 font-mono text-[11.5px] uppercase tracking-[0.04em] text-ink-muted hover:text-ink rounded-[3px] border border-dashed border-line-strong hover:border-brand hover:bg-surface transition-colors"
              >
                <Plus size={13} />
                new chat
              </button>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

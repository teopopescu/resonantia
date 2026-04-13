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
          className="shrink-0 bg-surface border-r border-border flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="px-4 pt-4 pb-2">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-[10px] font-semibold tracking-widest text-muted uppercase">
                  Conversations
                </p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={toggleSidebar}
                  className="p-1.5 rounded-md text-muted hover:text-charcoal hover:bg-cream transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Search */}
            <div className="px-4 py-2">
              <div className="relative">
                <Search
                  size={14}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted"
                />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors placeholder:text-muted"
                />
              </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto px-2">
              {filteredConversations.length === 0 && (
                <div className="flex flex-col items-center justify-center text-center px-4 py-12">
                  <div className="w-10 h-10 rounded-xl bg-cream flex items-center justify-center mb-3">
                    <MessageSquare size={20} className="text-muted" />
                  </div>
                  <p className="text-sm text-muted">No conversations yet</p>
                  <p className="text-xs text-muted/60 mt-1">
                    Start a new chat to begin
                  </p>
                </div>
              )}
              {filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`group relative w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-all duration-100 cursor-pointer ${
                    activeConversationId === conv.id
                      ? "bg-amber/10 border border-amber/20"
                      : "hover:bg-cream border border-transparent"
                  }`}
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
                        className="flex-1 text-sm px-1.5 py-0.5 rounded border border-amber/40 bg-surface text-charcoal focus:outline-none"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFinishRename();
                        }}
                        className="p-0.5 text-amber hover:text-amber-dark"
                      >
                        <Check size={14} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <p
                        className={`text-sm leading-snug truncate pr-12 ${
                          activeConversationId === conv.id
                            ? "text-charcoal font-medium"
                            : "text-charcoal/80"
                        }`}
                      >
                        {conv.title}
                      </p>
                      <p className="text-[10px] text-muted mt-0.5">
                        {relativeDate(conv.updatedAt || conv.createdAt)}
                      </p>

                      {/* Hover actions */}
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-0.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(conv.id, conv.title);
                          }}
                          className="p-1 rounded text-muted hover:text-charcoal hover:bg-cream transition-colors"
                          title="Rename"
                        >
                          <Pencil size={12} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteConversation(conv.id);
                          }}
                          className="p-1 rounded text-muted hover:text-red-500 hover:bg-red-50 transition-colors"
                          title="Delete"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>

            {/* New Chat button */}
            <div className="px-3 py-3 border-t border-border">
              <button
                onClick={startNewConversation}
                className="flex items-center gap-2 w-full px-3 py-2 text-xs font-medium text-muted hover:text-charcoal rounded-lg border border-dashed border-border hover:border-amber/40 transition-all"
              >
                <Plus size={14} />
                New Chat
              </button>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLabStore } from "@/stores/lab-store";
import {
  ChevronLeft,
  Settings,
  Search,
  Plus,
  ChevronDown,
  FolderOpen,
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
    tasks,
    activeTaskId,
    sidebarCollapsed,
    activeTab,
    setActiveTask,
    toggleSidebar,
    addTask,
    setActiveTab,
  } = useLabStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");

  const filteredTasks = tasks.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function handleCreateTask() {
    if (newTaskTitle.trim()) {
      addTask(newTaskTitle.trim());
      setNewTaskTitle("");
      setIsCreating(false);
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
                  Project
                </p>
                <button className="flex items-center gap-1 text-sm font-medium text-charcoal hover:text-amber transition-colors mt-0.5">
                  Quick Tasks
                  <ChevronDown size={14} />
                </button>
              </div>
              <div className="flex items-center gap-1">
                <button className="p-1.5 rounded-md text-muted hover:text-charcoal hover:bg-cream transition-colors">
                  <Settings size={16} />
                </button>
                <button
                  onClick={toggleSidebar}
                  className="p-1.5 rounded-md text-muted hover:text-charcoal hover:bg-cream transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border">
              <button
                onClick={() => setActiveTab("tasks")}
                className={`flex-1 pb-2 text-xs font-medium transition-colors border-b-2 ${
                  activeTab === "tasks"
                    ? "text-charcoal border-amber"
                    : "text-muted border-transparent hover:text-charcoal"
                }`}
              >
                Tasks
              </button>
              <button
                onClick={() => setActiveTab("files")}
                className={`flex-1 pb-2 text-xs font-medium transition-colors border-b-2 ${
                  activeTab === "files"
                    ? "text-charcoal border-amber"
                    : "text-muted border-transparent hover:text-charcoal"
                }`}
              >
                Files
              </button>
            </div>
          </div>

          {/* Content */}
          {activeTab === "tasks" ? (
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
                    placeholder="Search tasks..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors placeholder:text-muted"
                  />
                </div>
              </div>

              {/* Task list */}
              <div className="flex-1 overflow-y-auto px-2">
                {filteredTasks.map((task) => (
                  <button
                    key={task.id}
                    onClick={() => setActiveTask(task.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-all duration-100 group ${
                      activeTaskId === task.id
                        ? "bg-amber/10 border border-amber/20"
                        : "hover:bg-cream border border-transparent"
                    }`}
                  >
                    <p
                      className={`text-sm leading-snug truncate ${
                        activeTaskId === task.id
                          ? "text-charcoal font-medium"
                          : "text-charcoal/80"
                      }`}
                    >
                      {task.title}
                    </p>
                    <p className="text-[10px] text-muted mt-0.5">
                      {relativeDate(task.createdAt)}
                    </p>
                  </button>
                ))}
              </div>

              {/* New task */}
              <div className="px-3 py-3 border-t border-border">
                {isCreating ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newTaskTitle}
                      onChange={(e) => setNewTaskTitle(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleCreateTask()}
                      placeholder="Task name..."
                      autoFocus
                      className="flex-1 px-2.5 py-1.5 text-xs rounded-xl border border-border bg-surface text-charcoal focus:outline-none focus:border-amber/40 transition-colors"
                    />
                    <button
                      onClick={handleCreateTask}
                      className="px-3 py-1.5 text-xs font-medium bg-amber text-charcoal rounded-md hover:bg-amber-light transition-colors"
                    >
                      Add
                    </button>
                    <button
                      onClick={() => {
                        setIsCreating(false);
                        setNewTaskTitle("");
                      }}
                      className="px-2 py-1.5 text-xs text-muted hover:text-charcoal transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsCreating(true)}
                    className="flex items-center gap-2 w-full px-3 py-2 text-xs font-medium text-muted hover:text-charcoal rounded-lg border border-dashed border-border hover:border-amber/40 transition-all"
                  >
                    <Plus size={14} />
                    New Task
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Files tab */
            <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
              <div className="w-12 h-12 rounded-xl bg-cream flex items-center justify-center mb-3">
                <FolderOpen size={24} className="text-muted" />
              </div>
              <p className="text-sm font-medium text-charcoal/70">
                No files yet
              </p>
              <p className="text-xs text-muted mt-1">
                Files generated by tasks will appear here
              </p>
            </div>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

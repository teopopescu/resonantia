import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Task {
  id: string;
  title: string;
  createdAt: string;
  status: "active" | "completed" | "archived";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

interface LabState {
  tasks: Task[];
  activeTaskId: string | null;
  chatMessages: ChatMessage[];
  sidebarCollapsed: boolean;
  activeTool: string;
  activeTab: "tasks" | "files";
  pendingPrompt: string | null;

  addTask: (title: string) => void;
  setActiveTask: (id: string | null) => void;
  addMessage: (role: ChatMessage["role"], content: string) => void;
  toggleSidebar: () => void;
  setActiveTool: (tool: string) => void;
  setActiveTab: (tab: "tasks" | "files") => void;
  setPendingPrompt: (prompt: string | null) => void;
}

function generateId() {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

export const useLabStore = create<LabState>()(
  persist(
    (set) => ({
      tasks: [
        {
          id: "default-1",
          title: "Plate mapping for experiment A",
          createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
          status: "active",
        },
        {
          id: "default-2",
          title: "Microscopy image analysis",
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          status: "active",
        },
        {
          id: "default-3",
          title: "Sample inventory check",
          createdAt: new Date(Date.now() - 3600000 * 5).toISOString(),
          status: "completed",
        },
      ],
      activeTaskId: null,
      chatMessages: [],
      sidebarCollapsed: false,
      activeTool: "chat",
      activeTab: "tasks",
      pendingPrompt: null,

      addTask: (title) =>
        set((state) => ({
          tasks: [
            {
              id: generateId(),
              title,
              createdAt: new Date().toISOString(),
              status: "active",
            },
            ...state.tasks,
          ],
        })),

      setActiveTask: (id) => set({ activeTaskId: id }),

      addMessage: (role, content) =>
        set((state) => ({
          chatMessages: [
            ...state.chatMessages,
            {
              id: generateId(),
              role,
              content,
              timestamp: new Date().toISOString(),
            },
          ],
        })),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setActiveTool: (tool) => set({ activeTool: tool }),

      setActiveTab: (tab) => set({ activeTab: tab }),

      setPendingPrompt: (prompt) => set({ pendingPrompt: prompt }),
    }),
    {
      name: "resonantia-lab",
      partialize: (state) => ({
        tasks: state.tasks,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, API_URL, getActiveOrgId } from "@/lib/api";

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  toolCalls?: ToolCall[];
}

interface LabState {
  conversations: Conversation[];
  activeConversationId: string | null;
  chatMessages: ChatMessage[];
  sidebarCollapsed: boolean;
  activeTool: string;
  pendingPrompt: string | null;
  voiceModeActive: boolean;

  fetchConversations: (clerkUserId?: string) => Promise<void>;
  setActiveConversation: (id: string | null) => void;
  loadConversationMessages: (id: string) => Promise<void>;
  startNewConversation: () => void;
  deleteConversation: (id: string) => Promise<void>;
  renameConversation: (id: string, title: string) => Promise<void>;
  addMessage: (role: ChatMessage["role"], content: string, toolCalls?: ToolCall[]) => void;
  clearMessages: () => void;
  toggleSidebar: () => void;
  setActiveTool: (tool: string) => void;
  setPendingPrompt: (prompt: string | null) => void;
  setVoiceModeActive: (active: boolean) => void;
  addConversation: (conv: Conversation) => void;
}

function generateId() {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

export const useLabStore = create<LabState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,
      chatMessages: [],
      sidebarCollapsed: false,
      activeTool: "chat",
      pendingPrompt: null,
      voiceModeActive: false,

      fetchConversations: async (_clerkUserId?: string) => {
        void _clerkUserId;
        try {
          const data = await api<Conversation[]>("/api/v1/chat/conversations");
          set({ conversations: data });
        } catch (err) {
          console.error("Failed to fetch conversations:", err);
        }
      },

      setActiveConversation: (id) => set({ activeConversationId: id }),

      loadConversationMessages: async (id: string) => {
        try {
          const response = await api<{ messages: any[] }>(
            `/api/v1/chat/conversations/${id}`
          );
          const raw = response.messages || [];
          // Merge tool-call metadata into assistant messages, skip tool-result rows
          const data: ChatMessage[] = [];
          let pendingToolCalls: ToolCall[] = [];
          for (const m of raw) {
            if (m.role === "tool") continue; // skip tool result messages
            if (m.role === "assistant" && Array.isArray(m.toolCalls) && m.toolCalls.length > 0) {
              // assistant message that triggered tool calls — collect them
              pendingToolCalls.push(
                ...m.toolCalls.map((tc: any) => ({
                  id: tc.id,
                  name: tc.function?.name || tc.name || "unknown",
                  input: tc.function?.arguments
                    ? (typeof tc.function.arguments === "string" ? JSON.parse(tc.function.arguments) : tc.function.arguments)
                    : tc.input || {},
                }))
              );
              // If the message also has content, include it
              if (m.content) {
                data.push({
                  id: m.id || generateId(),
                  role: m.role,
                  content: m.content,
                  toolCalls: [...pendingToolCalls],
                  timestamp: m.createdAt || m.timestamp || new Date().toISOString(),
                });
                pendingToolCalls = [];
              }
              continue;
            }
            // Regular user or assistant message
            const msg: ChatMessage = {
              id: m.id || generateId(),
              role: m.role,
              content: m.content || "",
              timestamp: m.createdAt || m.timestamp || new Date().toISOString(),
            };
            // Attach any pending tool calls to the next assistant text response
            if (m.role === "assistant" && pendingToolCalls.length > 0) {
              msg.toolCalls = [...pendingToolCalls];
              pendingToolCalls = [];
            }
            data.push(msg);
          }
          set({ chatMessages: data, activeConversationId: id });
        } catch (err) {
          console.error("Failed to load conversation messages:", err);
        }
      },

      startNewConversation: () => {
        set({ activeConversationId: null, chatMessages: [] });
      },

      deleteConversation: async (id: string) => {
        try {
          await api(`/api/v1/chat/conversations/${id}`, { method: "DELETE" });
          const state = get();
          const updated = state.conversations.filter((c) => c.id !== id);
          set({
            conversations: updated,
            ...(state.activeConversationId === id
              ? { activeConversationId: null, chatMessages: [] }
              : {}),
          });
        } catch (err) {
          console.error("Failed to delete conversation:", err);
        }
      },

      renameConversation: async (id: string, title: string) => {
        try {
          await api(`/api/v1/chat/conversations/${id}`, {
            method: "PATCH",
            body: JSON.stringify({ title }),
          });
          set((state) => ({
            conversations: state.conversations.map((c) =>
              c.id === id ? { ...c, title } : c
            ),
          }));
        } catch (err) {
          console.error("Failed to rename conversation:", err);
        }
      },

      addMessage: (role, content, toolCalls?) =>
        set((state) => ({
          chatMessages: [
            ...state.chatMessages,
            {
              id: generateId(),
              role,
              content,
              toolCalls,
              timestamp: new Date().toISOString(),
            },
          ],
        })),

      clearMessages: () => set({ chatMessages: [] }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setActiveTool: (tool) => set({ activeTool: tool }),

      setPendingPrompt: (prompt) => set({ pendingPrompt: prompt }),

      setVoiceModeActive: (active) => set({ voiceModeActive: active }),

      addConversation: (conv) =>
        set((state) => ({
          conversations: [conv, ...state.conversations],
          activeConversationId: conv.id,
        })),
    }),
    {
      name: "resonantia-lab",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

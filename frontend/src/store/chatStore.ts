import { create } from 'zustand'
import { Thread, Message, Source } from '../types/chat'

export interface StreamingState {
  threadId: string
  content: string
  sources: Source[] | null
  isStreaming: boolean
}

interface ChatDataState {
  threads: Thread[]
  activeThreadId: string | null
  messages: Record<string, Message[]>
  streaming: StreamingState | null
}

const initialState: ChatDataState = {
  threads: [],
  activeThreadId: null,
  messages: {},
  streaming: null,
}

interface ChatState extends ChatDataState {
  setThreads: (threads: Thread[]) => void
  addThread: (thread: Thread) => void
  updateThread: (thread: Thread) => void
  removeThread: (threadId: string) => void
  setActiveThread: (threadId: string | null) => void

  setMessages: (threadId: string, messages: Message[]) => void
  addMessage: (threadId: string, message: Message) => void

  startStreaming: (threadId: string) => void
  appendToken: (threadId: string, token: string) => void
  setSources: (threadId: string, sources: Source[]) => void
  finalizeStream: (threadId: string, messageId: string) => void
  cancelStream: () => void

  /**
   * Wipes all chat data back to initial state.
   * MUST be called on logout. This store is a module-level singleton that
   * lives outside React's component tree — unmounting ChatPage does NOT
   * clear it. Without this, the next account to log in inherits the
   * previous account's open thread and cached messages.
   */
  reset: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  ...initialState,

  setThreads: (threads) => set({ threads }),

  addThread: (thread) =>
    set((s) => ({ threads: [thread, ...s.threads] })),

  updateThread: (thread) =>
    set((s) => ({ threads: s.threads.map((t) => (t.id === thread.id ? thread : t)) })),

  removeThread: (threadId) =>
    set((s) => ({
      threads: s.threads.filter((t) => t.id !== threadId),
      activeThreadId: s.activeThreadId === threadId ? null : s.activeThreadId,
      messages: Object.fromEntries(
        Object.entries(s.messages).filter(([k]) => k !== threadId),
      ),
    })),

  setActiveThread: (threadId) => set({ activeThreadId: threadId }),

  setMessages: (threadId, messages) =>
    set((s) => ({ messages: { ...s.messages, [threadId]: messages } })),

  addMessage: (threadId, message) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [threadId]: [...(s.messages[threadId] ?? []), message],
      },
    })),

  startStreaming: (threadId) =>
    set({ streaming: { threadId, content: '', sources: null, isStreaming: true } }),

  appendToken: (threadId, token) =>
    set((s) => {
      if (!s.streaming || s.streaming.threadId !== threadId) return s
      return { streaming: { ...s.streaming, content: s.streaming.content + token } }
    }),

  setSources: (threadId, sources) =>
    set((s) => {
      if (!s.streaming || s.streaming.threadId !== threadId) return s
      return { streaming: { ...s.streaming, sources } }
    }),

  finalizeStream: (threadId, messageId) =>
    set((s) => {
      if (!s.streaming) return s
      const saved: Message = {
        id: messageId,
        thread_id: threadId,
        role: 'assistant',
        content: s.streaming.content,
        sources: s.streaming.sources,
        created_at: new Date().toISOString(),
      }
      return {
        streaming: null,
        messages: {
          ...s.messages,
          [threadId]: [...(s.messages[threadId] ?? []), saved],
        },
      }
    }),

  cancelStream: () => set({ streaming: null }),

  reset: () => set({ ...initialState }),
}))
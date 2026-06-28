import client from './client'
import { ChatMode, Thread, ThreadWithMessages, SendMessageResponse } from '../types/chat'

export const chatApi = {
  createThread: (title: string, mode: ChatMode) =>
    client.post<Thread>('/chat/threads', { title, mode }),

  listThreads: () =>
    client.get<Thread[]>('/chat/threads'),

  getThread: (threadId: string) =>
    client.get<ThreadWithMessages>(`/chat/threads/${threadId}`),

  renameThread: (threadId: string, title: string) =>
    client.patch<Thread>(`/chat/threads/${threadId}`, { title }),

  deleteThread: (threadId: string) =>
    client.delete(`/chat/threads/${threadId}`),

  // Step 1 of two-step SSE: saves the user message, returns user_message_id
  // which is then passed to the GET /stream endpoint.
  sendMessage: (threadId: string, content: string) =>
    client.post<SendMessageResponse>(
      `/chat/threads/${threadId}/messages`,
      { content },
    ),
}
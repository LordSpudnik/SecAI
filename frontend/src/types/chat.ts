export type ChatMode = 'general' | 'rag'
export type MessageRole = 'user' | 'assistant'

export interface Thread {
  id: string
  title: string
  mode: ChatMode
  created_at: string
  updated_at: string
}

export interface Source {
  document_id: string
  source: string
  distance: number
}

export interface Message {
  id: string
  thread_id: string
  role: MessageRole
  content: string
  sources?: Source[] | null
  created_at: string
}

export interface ThreadWithMessages extends Thread {
  messages: Message[]
}

export interface SendMessageResponse {
  user_message_id: string
  thread_id: string
}

export type SSEEvent =
  | { type: 'token';   content: string }
  | { type: 'sources'; sources: Source[] }
  | { type: 'done';    message_id: string }
  | { type: 'error';   detail: string }
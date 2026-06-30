import { useEffect, useRef } from 'react'
import { useChatStore } from '../../store/chatStore'
import { Message } from '../../types/chat'
import MessageBubble from './MessageBubble'
import StreamingBubble from './StreamingBubble'
import MessageInput from './MessageInput'

interface Props { threadId: string }

// Stable reference returned when a thread has no messages yet.
// Do NOT replace this with an inline `[]` inside the selector below.
// A new `[]` created on every render is treated by Zustand/React as
// "the state changed" (different array reference in memory), which
// forces another render, which creates another new `[]` — forever.
// That's the "Maximum update depth exceeded" / "getSnapshot should be
// cached" crash. Using one shared constant means the same reference
// is returned every time, so React correctly sees "nothing changed".
const EMPTY_MESSAGES: Message[] = []

export default function ChatView({ threadId }: Props) {
  const threads = useChatStore((s) => s.threads)
  const messages = useChatStore((s) => s.messages[threadId] ?? EMPTY_MESSAGES)
  const streaming = useChatStore((s) => s.streaming)
  const bottomRef = useRef<HTMLDivElement>(null)

  const thread = threads.find((t) => t.id === threadId)
  const isStreaming = streaming?.isStreaming === true && streaming.threadId === threadId

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streaming?.content])

  const modeLabel = thread?.mode === 'rag' ? '[RAG]' : '[GEN]'
  const modeCls = thread?.mode === 'rag'
    ? 'text-violet-400 border-violet-500/30 bg-violet-500/10'
    : 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 h-12 border-b border-zinc-800 flex-shrink-0">
        <h2 className="flex-1 text-sm font-semibold text-zinc-100 truncate min-w-0">
          {thread?.title ?? 'Chat'}
        </h2>
        <span className={`text-[10px] font-bold font-mono border rounded px-1.5 py-0.5 flex-shrink-0 ${modeCls}`}>
          {modeLabel}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-5 min-h-0">
        {messages.length === 0 && !streaming && (
          <div className="h-full flex items-center justify-center">
            <p className="text-xs text-zinc-600 font-mono">// send a message to begin</p>
          </div>
        )}
        {messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)}
        {streaming && streaming.threadId === threadId && (
          <StreamingBubble content={streaming.content} sources={streaming.sources} />
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex-shrink-0 border-t border-zinc-800 px-4 py-3">
        <MessageInput threadId={threadId} isStreaming={isStreaming} />
      </div>
    </div>
  )
}
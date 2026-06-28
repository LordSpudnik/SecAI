import { useState, useEffect, useRef, KeyboardEvent } from 'react'
import { ArrowUp } from 'lucide-react'
import { chatApi } from '../../api/chat'
import { useSSE } from '../../hooks/useSSE'
import { useChatStore } from '../../store/chatStore'
import { SSEEvent } from '../../types/chat'

interface Props {
  threadId: string
  isStreaming: boolean
}

export default function MessageInput({ threadId, isStreaming }: Props) {
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { connect, disconnect } = useSSE()
  const { addMessage, startStreaming, appendToken, setSources, finalizeStream, cancelStream } = useChatStore()

  // Disconnect SSE and reset streaming state when thread changes or component unmounts
  useEffect(() => {
    return () => { disconnect(); cancelStream() }
  }, [threadId]) // eslint-disable-line react-hooks/exhaustive-deps

  const syncHeight = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 144) + 'px'
  }

  const handleSend = async () => {
    const trimmed = content.trim()
    if (!trimmed || isStreaming) return

    setContent(''); setError('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      // Step 1 — POST saves user message, returns user_message_id
      const res = await chatApi.sendMessage(threadId, trimmed)
      const { user_message_id } = res.data

      addMessage(threadId, {
        id: user_message_id,
        thread_id: threadId,
        role: 'user',
        content: trimmed,
        created_at: new Date().toISOString(),
      })

      // Step 2 — open SSE stream
      startStreaming(threadId)
      connect(threadId, user_message_id, (event: SSEEvent) => {
        switch (event.type) {
          case 'token':   appendToken(threadId, event.content); break
          case 'sources': setSources(threadId, event.sources); break
          case 'done':    finalizeStream(threadId, event.message_id); break
          case 'error':   setError(event.detail); cancelStream(); break
        }
      })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Failed to send message')
      cancelStream()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="space-y-2">
      {error && (
        <p className="text-[11px] text-red-400 font-mono bg-red-400/10 border border-red-400/20 rounded px-3 py-1.5">
          {error}
        </p>
      )}
      <div className={`flex items-end gap-2 bg-zinc-800 border rounded-xl px-3 py-2.5 transition-colors ${
        isStreaming ? 'border-zinc-700 opacity-70' : 'border-zinc-700 focus-within:border-zinc-600'
      }`}>
        <textarea ref={textareaRef} value={content} disabled={isStreaming}
          onChange={(e) => { setContent(e.target.value); syncHeight() }}
          onKeyDown={handleKeyDown}
          placeholder={isStreaming ? 'Generating…' : 'Ask anything  (↵ send · ⇧↵ newline)'}
          rows={1}
          className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-600 resize-none focus:outline-none min-w-0 overflow-y-auto"
          style={{ lineHeight: '1.5rem' }}
        />
        <button onClick={handleSend} disabled={isStreaming || !content.trim()}
          className="flex-shrink-0 w-7 h-7 flex items-center justify-center bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-700 disabled:text-zinc-600 text-white rounded-lg transition-colors">
          <ArrowUp className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
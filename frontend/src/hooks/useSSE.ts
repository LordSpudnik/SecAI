import { useRef, useCallback } from 'react'
import { useAuthStore } from '../store/authStore'
import { SSEEvent } from '../types/chat'

export function useSSE() {
  const esRef = useRef<EventSource | null>(null)

  const connect = useCallback(
    (
      threadId: string,
      userMessageId: string,
      onEvent: (event: SSEEvent) => void,
    ): (() => void) => {
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }

      const token = useAuthStore.getState().token
      if (!token) return () => {}

      // JWT as query param — EventSource cannot send custom headers.
      // Only safe over HTTPS; enforce that in nginx for production.
      const url =
        `/api/chat/threads/${threadId}/stream` +
        `?user_message_id=${encodeURIComponent(userMessageId)}` +
        `&token=${encodeURIComponent(token)}`

      const es = new EventSource(url)
      esRef.current = es

      es.onmessage = (e: MessageEvent<string>) => {
        try {
          const data = JSON.parse(e.data) as SSEEvent
          onEvent(data)
          if (data.type === 'done' || data.type === 'error') {
            es.close()
            esRef.current = null
          }
        } catch {
          // Ignore malformed frames
        }
      }

      es.onerror = () => {
        onEvent({ type: 'error', detail: 'Connection lost' })
        es.close()
        esRef.current = null
      }

      return () => { es.close(); esRef.current = null }
    },
    [],
  )

  const disconnect = useCallback(() => {
    if (esRef.current) { esRef.current.close(); esRef.current = null }
  }, [])

  return { connect, disconnect }
}
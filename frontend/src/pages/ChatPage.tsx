import { useEffect, useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import ChatView from '../components/chat/ChatView'
import EmptyState from '../components/chat/EmptyState'
import FilePanel from '../components/files/FilePanel'
import { useChatStore } from '../store/chatStore'
import { useFileStore } from '../store/fileStore'
import { chatApi } from '../api/chat'
import { filesApi } from '../api/files'

export default function ChatPage() {
  const [filesOpen, setFilesOpen] = useState(false)
  const setThreads = useChatStore((s) => s.setThreads)
  const activeThreadId = useChatStore((s) => s.activeThreadId)
  const setMessages = useChatStore((s) => s.setMessages)
  const setDocuments = useFileStore((s) => s.setDocuments)

  useEffect(() => {
    chatApi.listThreads().then((r) => setThreads(r.data)).catch(() => {})
    filesApi.list().then((r) => setDocuments(r.data)).catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!activeThreadId) return
    chatApi.getThread(activeThreadId)
      .then((r) => setMessages(activeThreadId, r.data.messages))
      .catch(() => {})
  }, [activeThreadId]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AppLayout onOpenFiles={() => setFilesOpen(true)}>
      {activeThreadId
        ? <ChatView threadId={activeThreadId} />
        : <EmptyState onOpenFiles={() => setFilesOpen(true)} />}
      {filesOpen && <FilePanel onClose={() => setFilesOpen(false)} />}
    </AppLayout>
  )
}
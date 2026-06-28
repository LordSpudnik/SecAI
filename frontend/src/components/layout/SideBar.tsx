import { useState } from 'react'
import { Plus, FolderOpen, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useChatStore } from '../../store/chatStore'
import { useFileStore } from '../../store/fileStore'
import { chatApi } from '../../api/chat'
import { authApi } from '../../api/auth'
import ThreadList from '../chat/ThreadList'
import NewThreadModal from '../chat/NewThreadModal'
import { ChatMode } from '../../types/chat'

interface Props {
  onOpenFiles: () => void
}

export default function Sidebar({ onOpenFiles }: Props) {
  const [showNewThread, setShowNewThread] = useState(false)
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const user = useAuthStore((s) => s.user)
  const { addThread, setActiveThread } = useChatStore()
  const documents = useFileStore((s) => s.documents)

  const readyCount = documents.filter((d) => d.processing_status === 'ready').length

  const handleLogout = async () => {
    try { await authApi.logout() } finally { clearAuth() }
  }

  const handleCreate = async (title: string, mode: ChatMode) => {
    const res = await chatApi.createThread(title, mode)
    addThread(res.data)
    setActiveThread(res.data.id)
    setShowNewThread(false)
  }

  return (
    <>
      <aside className="w-60 flex flex-col bg-zinc-900 border-r border-zinc-800 h-full flex-shrink-0">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-4 h-12 border-b border-zinc-800 flex-shrink-0">
          <div className="w-6 h-6 rounded bg-indigo-600 flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold font-mono">S</span>
          </div>
          <span className="text-sm font-semibold text-zinc-100 tracking-tight">SecAI</span>
          <span className="ml-auto text-[10px] font-mono text-zinc-600 border border-zinc-700 rounded px-1">
            v0.4
          </span>
        </div>

        {/* New thread */}
        <div className="px-3 pt-3 pb-1 flex-shrink-0">
          <button
            onClick={() => setShowNewThread(true)}
            className="w-full flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-lg px-3 py-2 text-xs font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5 flex-shrink-0" />
            New thread
          </button>
        </div>

        {/* Thread list */}
        <div className="flex-1 overflow-hidden flex flex-col min-h-0 py-1">
          <p className="px-4 py-1.5 text-[10px] uppercase font-semibold tracking-widest text-zinc-600">
            Threads
          </p>
          <div className="overflow-y-auto flex-1 px-2">
            <ThreadList />
          </div>
        </div>

        {/* Bottom */}
        <div className="border-t border-zinc-800 p-2 space-y-0.5 flex-shrink-0">
          <button
            onClick={onOpenFiles}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-xs text-zinc-400 hover:text-zinc-200"
          >
            <FolderOpen className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="flex-1 text-left">Documents</span>
            {readyCount > 0 && (
              <span className="font-mono text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded px-1.5 py-0.5">
                {readyCount}
              </span>
            )}
          </button>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors text-xs text-zinc-500 hover:text-red-400"
          >
            <LogOut className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="flex-1 text-left truncate">{user?.email}</span>
          </button>
        </div>
      </aside>

      {showNewThread && (
        <NewThreadModal
          onClose={() => setShowNewThread(false)}
          onCreate={handleCreate}
        />
      )}
    </>
  )
}
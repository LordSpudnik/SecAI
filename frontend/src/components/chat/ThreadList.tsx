import { useChatStore } from '../../store/chatStore'
import ThreadItem from './ThreadItem'

export default function ThreadList() {
  const threads = useChatStore((s) => s.threads)
  const activeThreadId = useChatStore((s) => s.activeThreadId)
  const setActiveThread = useChatStore((s) => s.setActiveThread)

  if (threads.length === 0) {
    return (
      <p className="px-2 py-6 text-[11px] text-zinc-600 text-center font-mono">
        // no threads yet
      </p>
    )
  }

  return (
    <div className="space-y-0.5 pb-2">
      {threads.map((thread) => (
        <ThreadItem
          key={thread.id}
          thread={thread}
          isActive={thread.id === activeThreadId}
          onSelect={() => setActiveThread(thread.id)}
        />
      ))}
    </div>
  )
}
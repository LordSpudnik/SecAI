import React, { useState, KeyboardEvent } from 'react'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import { Thread } from '../../types/chat'
import { useChatStore } from '../../store/chatStore'
import { chatApi } from '../../api/chat'

interface Props {
  thread: Thread
  isActive: boolean
  onSelect: () => void
}

const modeBadge: Record<Thread['mode'], { label: string; cls: string }> = {
  general: { label: '[GEN]', cls: 'text-emerald-500' },
  rag:     { label: '[RAG]', cls: 'text-violet-400' },
}

export default function ThreadItem({ thread, isActive, onSelect }: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(thread.title)
  const { updateThread, removeThread } = useChatStore()
  const badge = modeBadge[thread.mode]

  const commitRename = async () => {
    const trimmed = draft.trim()
    if (!trimmed) { setDraft(thread.title); setEditing(false); return }
    try {
      const res = await chatApi.renameThread(thread.id, trimmed)
      updateThread(res.data)
    } finally { setEditing(false) }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') commitRename()
    if (e.key === 'Escape') { setDraft(thread.title); setEditing(false) }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Delete "${thread.title}"?`)) return
    await chatApi.deleteThread(thread.id)
    removeThread(thread.id)
  }

  return (
    <div
      onClick={!editing ? onSelect : undefined}
      className={`group flex items-center gap-1.5 rounded-md px-2 py-1.5 cursor-pointer transition-colors ${
        isActive ? 'bg-zinc-800 text-zinc-100' : 'hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200'
      }`}
    >
      <span className={`text-[9px] font-bold font-mono flex-shrink-0 ${badge.cls}`}>
        {badge.label}
      </span>

      {editing ? (
        <input autoFocus value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          className="flex-1 bg-zinc-700 text-zinc-100 text-xs rounded px-1.5 py-0.5 focus:outline-none min-w-0"
        />
      ) : (
        <span className="flex-1 text-xs truncate min-w-0">{thread.title}</span>
      )}

      {editing ? (
        <div className="flex gap-0.5 flex-shrink-0">
          <button onClick={(e) => { e.stopPropagation(); commitRename() }} className="p-0.5 text-emerald-400 hover:text-emerald-300"><Check className="w-3 h-3" /></button>
          <button onClick={(e) => { e.stopPropagation(); setDraft(thread.title); setEditing(false) }} className="p-0.5 text-zinc-500 hover:text-zinc-300"><X className="w-3 h-3" /></button>
        </div>
      ) : (
        <div className="hidden group-hover:flex gap-0.5 flex-shrink-0">
          <button onClick={(e) => { e.stopPropagation(); setEditing(true) }} className="p-0.5 text-zinc-600 hover:text-zinc-300 transition-colors" title="Rename"><Pencil className="w-3 h-3" /></button>
          <button onClick={handleDelete} className="p-0.5 text-zinc-600 hover:text-red-400 transition-colors" title="Delete"><Trash2 className="w-3 h-3" /></button>
        </div>
      )}
    </div>
  )
}
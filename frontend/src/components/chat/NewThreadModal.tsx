import { useState, FormEvent } from 'react'
import { X, MessageSquare, FileSearch } from 'lucide-react'
import { ChatMode } from '../../types/chat'

interface Props {
  onClose: () => void
  onCreate: (title: string, mode: ChatMode) => Promise<void>
}

export default function NewThreadModal({ onClose, onCreate }: Props) {
  const [title, setTitle] = useState('')
  const [mode, setMode] = useState<ChatMode>('general')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true); setError('')
    try { await onCreate(title.trim(), mode) }
    catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Failed to create thread')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 w-full max-w-sm shadow-2xl mx-4">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold text-zinc-100">New thread</h2>
          <button onClick={onClose} className="text-zinc-600 hover:text-zinc-300 transition-colors"><X className="w-4 h-4" /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">Title</label>
            <input autoFocus type="text" value={title} onChange={(e) => setTitle(e.target.value)}
              placeholder="Thread title" required
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors" />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-2">Mode</label>
            <div className="grid grid-cols-2 gap-2">
              {([['general', MessageSquare, 'emerald'], ['rag', FileSearch, 'violet']] as const).map(
                ([m, Icon, color]) => (
                  <button key={m} type="button" onClick={() => setMode(m)}
                    className={`flex flex-col items-start gap-1.5 p-3 rounded-lg border text-left transition-colors ${
                      mode === m
                        ? `border-${color}-600 bg-${color}-600/10`
                        : 'border-zinc-700 hover:border-zinc-600'
                    }`}>
                    <div className="flex items-center gap-1.5">
                      <Icon className={`w-3.5 h-3.5 ${mode === m ? `text-${color}-400` : 'text-zinc-500'}`} />
                      <span className={`text-xs font-mono font-bold ${mode === m ? `text-${color}-400` : 'text-zinc-400'}`}>
                        {m === 'general' ? '[GEN]' : '[RAG]'}
                      </span>
                    </div>
                    <span className="text-[11px] text-zinc-500 leading-tight">
                      {m === 'general' ? 'Free-form conversation with history' : 'Grounded in your documents'}
                    </span>
                  </button>
                )
              )}
            </div>
          </div>

          {error && <p className="text-xs text-red-400 font-mono bg-red-400/10 border border-red-400/20 rounded px-3 py-2">{error}</p>}

          <button type="submit" disabled={loading || !title.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg py-2.5 text-sm font-medium transition-colors">
            {loading ? 'Creating…' : 'Create thread'}
          </button>
        </form>
      </div>
    </div>
  )
}
import { MessageSquare, FileSearch, ArrowRight } from 'lucide-react'

interface Props { onOpenFiles: () => void }

export default function EmptyState({ onOpenFiles }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 select-none">
      <div className="w-10 h-10 rounded-lg bg-indigo-600/20 border border-indigo-600/30 flex items-center justify-center mb-5">
        <span className="text-indigo-400 font-bold font-mono">S</span>
      </div>
      <h2 className="text-zinc-100 font-semibold text-base mb-1">SecAI</h2>
      <p className="text-zinc-500 text-xs mb-8 text-center max-w-xs">
        Private, local AI — your data never leaves your machine. Create a thread to start.
      </p>
      <div className="flex gap-3 mb-8">
        <div className="flex flex-col gap-2 bg-zinc-900 border border-zinc-800 rounded-xl p-4 w-36">
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[10px] font-mono font-bold text-emerald-400">[GEN]</span>
          </div>
          <p className="text-[11px] text-zinc-500 leading-snug">Open-ended conversation with full history context</p>
        </div>
        <div onClick={onOpenFiles}
          className="flex flex-col gap-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl p-4 w-36 cursor-pointer transition-colors">
          <div className="flex items-center gap-1.5">
            <FileSearch className="w-3.5 h-3.5 text-violet-400" />
            <span className="text-[10px] font-mono font-bold text-violet-400">[RAG]</span>
          </div>
          <p className="text-[11px] text-zinc-500 leading-snug">Answers grounded strictly in your documents</p>
          <div className="flex items-center gap-1 text-[10px] text-zinc-600 mt-auto">
            <span>Upload docs</span><ArrowRight className="w-2.5 h-2.5" />
          </div>
        </div>
      </div>
      <p className="text-[11px] text-zinc-700 font-mono">// select a thread or create one in the sidebar</p>
    </div>
  )
}
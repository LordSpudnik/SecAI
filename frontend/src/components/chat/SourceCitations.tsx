import { FileText } from 'lucide-react'
import { Source } from '../../types/chat'

interface Props { sources: Source[] }

export default function SourceCitations({ sources }: Props) {
  return (
    <div className="space-y-1.5">
      <p className="text-[9px] font-mono uppercase tracking-widest text-zinc-600">sources</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s, i) => (
          <div key={s.document_id}
            className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-700 rounded-md px-2 py-1 text-[11px]"
            title={s.source}>
            <FileText className="w-3 h-3 text-violet-400 flex-shrink-0" />
            <span className="font-mono font-bold text-zinc-500">[{i + 1}]</span>
            <span className="text-zinc-400 truncate max-w-[130px]">{s.source}</span>
            <span className="font-mono text-zinc-600">{Math.round((1 - s.distance) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
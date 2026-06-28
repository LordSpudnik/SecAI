import React from 'react'
import { Trash2, CheckCircle2, AlertCircle, Loader2, Clock } from 'lucide-react'
import { DocumentListItem, ProcessingStatus } from '../../types/files'
import { filesApi } from '../../api/files'
import { useFileStore } from '../../store/fileStore'

interface Props { document: DocumentListItem }

const statusConfig: Record<ProcessingStatus, { icon: React.ElementType; color: string; label: string; spin?: boolean }> = {
  ready:      { icon: CheckCircle2, color: 'text-emerald-400', label: 'ready' },
  processing: { icon: Loader2,      color: 'text-amber-400',   label: 'processing', spin: true },
  queued:     { icon: Clock,        color: 'text-zinc-500',    label: 'queued' },
  failed:     { icon: AlertCircle,  color: 'text-red-400',     label: 'failed' },
}

const typeBadge: Record<string, string> = {
  pdf:  'text-red-400   bg-red-400/10   border-red-400/20',
  docx: 'text-blue-400  bg-blue-400/10  border-blue-400/20',
  xlsx: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  txt:  'text-zinc-400  bg-zinc-700/40  border-zinc-600/30',
  csv:  'text-amber-400 bg-amber-400/10 border-amber-400/20',
}

export default function FileItem({ document }: Props) {
  const removeDocument = useFileStore((s) => s.removeDocument)
  const cfg = statusConfig[document.processing_status]
  const StatusIcon = cfg.icon
  const badge = typeBadge[document.file_type] ?? 'text-zinc-400 bg-zinc-700/40 border-zinc-600/30'

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Delete "${document.filename}"?`)) return
    try { await filesApi.delete(document.id); removeDocument(document.id) } catch { /* already gone */ }
  }

  return (
    <div className="group flex items-center gap-3 bg-zinc-800/50 border border-zinc-700/40 rounded-xl px-4 py-3">
      <span className={`text-[9px] font-mono font-bold uppercase border rounded px-1.5 py-0.5 flex-shrink-0 ${badge}`}>
        {document.file_type}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-zinc-200 font-medium truncate">{document.filename}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] font-mono text-zinc-600">{document.file_size_mb.toFixed(2)} MB</span>
          {document.processing_status === 'ready' && <span className="text-[10px] font-mono text-zinc-600">· {document.vector_count} chunks</span>}
          {document.processing_status === 'failed' && <span className="text-[10px] font-mono text-red-500">· processing failed</span>}
        </div>
      </div>
      <div className={`flex items-center gap-1.5 flex-shrink-0 ${cfg.color}`}>
        <StatusIcon className={`w-3.5 h-3.5 ${cfg.spin ? 'animate-spin' : ''}`} />
        <span className="text-[10px] font-mono">{cfg.label}</span>
      </div>
      <button onClick={handleDelete} className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all" title="Delete document">
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
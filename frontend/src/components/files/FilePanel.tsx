import { X } from 'lucide-react'
import FileUpload from './FileUpload'
import FileList from './FileList'

interface Props { onClose: () => void }

export default function FilePanel({ onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-xl max-h-[85vh] flex flex-col shadow-2xl mx-4">
        <div className="flex items-start justify-between px-5 py-4 border-b border-zinc-800 flex-shrink-0">
          <div>
            <h2 className="text-sm font-semibold text-zinc-100">Document library</h2>
            <p className="text-[11px] text-zinc-500 mt-0.5 font-mono">// upload files to query in [RAG] threads</p>
          </div>
          <button onClick={onClose} className="text-zinc-600 hover:text-zinc-300 transition-colors mt-0.5">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-5 py-4 border-b border-zinc-800 flex-shrink-0">
          <FileUpload />
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-3 min-h-0">
          <FileList />
        </div>
      </div>
    </div>
  )
}
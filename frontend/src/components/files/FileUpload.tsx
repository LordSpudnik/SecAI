import { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { CloudUpload } from 'lucide-react'
import { filesApi } from '../../api/files'
import { useFileStore } from '../../store/fileStore'
import { DocumentListItem, FileType } from '../../types/files'

const ALLOWED = ['.pdf', '.docx', '.xlsx', '.txt', '.csv']
const POLL_MS = 3000

export default function FileUpload() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const { addDocument, updateDocument } = useFileStore()

  const upload = async (file: File) => {
    const ext = '.' + (file.name.split('.').pop() ?? '').toLowerCase()
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported type: ${ext}. Allowed: ${ALLOWED.join(', ')}`); return
    }
    setUploading(true); setError('')
    try {
      const res = await filesApi.upload(file)
      const { document_id, filename } = res.data
      const placeholder: DocumentListItem = {
        id: document_id, filename,
        original_filename: file.name,
        file_type: ext.slice(1) as FileType,
        file_size_mb: file.size / (1024 * 1024),
        processing_status: 'queued',
        vector_count: 0,
        uploaded_at: new Date().toISOString(),
      }
      addDocument(placeholder)

      const id = setInterval(async () => {
        try {
          const s = await filesApi.status(document_id)
          updateDocument(document_id, { processing_status: s.data.status, vector_count: s.data.vector_count })
          if (s.data.status === 'ready' || s.data.status === 'failed') clearInterval(id)
        } catch { clearInterval(id) }
      }, POLL_MS)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Upload failed')
    } finally { setUploading(false) }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) upload(file)
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) upload(file)
    e.target.value = ''
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl py-6 px-4 cursor-pointer transition-colors ${
          dragging ? 'border-indigo-500 bg-indigo-500/5' : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800/40'
        } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <CloudUpload className={`w-6 h-6 ${dragging ? 'text-indigo-400' : 'text-zinc-600'}`} />
        <div className="text-center">
          <p className="text-xs text-zinc-300">{uploading ? 'Uploading…' : 'Drop a file here, or click to browse'}</p>
          <p className="text-[11px] text-zinc-600 mt-0.5 font-mono">pdf · docx · xlsx · txt · csv · max 50 MB</p>
        </div>
        <input ref={inputRef} type="file" className="hidden" accept={ALLOWED.join(',')} onChange={handleChange} disabled={uploading} />
      </div>
      {error && (
        <p className="text-[11px] text-red-400 font-mono bg-red-400/10 border border-red-400/20 rounded px-3 py-1.5">{error}</p>
      )}
    </div>
  )
}
import { useFileStore } from '../../store/fileStore'
import FileItem from './FileItem'

export default function FileList() {
  const documents = useFileStore((s) => s.documents)
  if (documents.length === 0) {
    return <p className="text-center text-[11px] text-zinc-600 font-mono py-8">// no documents yet</p>
  }
  return (
    <div className="space-y-2">
      {documents.map((doc) => <FileItem key={doc.id} document={doc} />)}
    </div>
  )
}
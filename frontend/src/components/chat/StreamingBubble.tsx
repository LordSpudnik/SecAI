import { Source } from '../../types/chat'
import SourceCitations from './SourceCitations'

interface Props {
  content: string
  sources: Source[] | null
}

export default function StreamingBubble({ content, sources }: Props) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] space-y-2">
        <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-zinc-600">
          secai
        </span>
        <div className="bg-zinc-800 border border-zinc-700/50 rounded-xl rounded-tl-sm px-4 py-3">
          <p className="text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap">
            {content}
            {/* Terminal blinking block cursor */}
            <span className="inline-block w-[7px] h-[14px] bg-indigo-400 ml-0.5 align-middle cursor-blink" />
          </p>
        </div>
        {sources && sources.length > 0 && <SourceCitations sources={sources} />}
      </div>
    </div>
  )
}
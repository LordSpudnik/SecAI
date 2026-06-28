import { Message } from '../../types/chat'
import SourceCitations from './SourceCitations'

interface Props { message: Message }

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] space-y-2 ${isUser ? 'flex flex-col items-end' : ''}`}>
        <span className={`text-[9px] font-mono font-bold uppercase tracking-widest ${isUser ? 'text-indigo-400' : 'text-zinc-600'}`}>
          {isUser ? 'you' : 'secai'}
        </span>
        <div className={`rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-indigo-600 text-white rounded-tr-sm'
            : 'bg-zinc-800 text-zinc-100 rounded-tl-sm border border-zinc-700/50'
        }`}>
          {message.content}
        </div>
        {message.sources && message.sources.length > 0 && (
          <SourceCitations sources={message.sources} />
        )}
      </div>
    </div>
  )
}
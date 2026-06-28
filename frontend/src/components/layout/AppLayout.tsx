import { ReactNode } from 'react'
import Sidebar from './Sidebar'

interface Props {
  children: ReactNode
  onOpenFiles: () => void
}

export default function AppLayout({ children, onOpenFiles }: Props) {
  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      <Sidebar onOpenFiles={onOpenFiles} />
      <main className="flex-1 flex flex-col overflow-hidden min-w-0">
        {children}
      </main>
    </div>
  )
}
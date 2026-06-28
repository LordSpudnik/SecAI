import { create } from 'zustand'
import { DocumentListItem } from '../types/files'

interface FileState {
  documents: DocumentListItem[]
  setDocuments: (docs: DocumentListItem[]) => void
  addDocument: (doc: DocumentListItem) => void
  updateDocument: (id: string, partial: Partial<DocumentListItem>) => void
  removeDocument: (id: string) => void
}

export const useFileStore = create<FileState>((set) => ({
  documents: [],
  setDocuments: (docs) => set({ documents: docs }),
  addDocument: (doc) => set((s) => ({ documents: [doc, ...s.documents] })),
  updateDocument: (id, partial) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === id ? { ...d, ...partial } : d)),
    })),
  removeDocument: (id) =>
    set((s) => ({ documents: s.documents.filter((d) => d.id !== id) })),
}))
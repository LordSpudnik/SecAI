import { create } from 'zustand'
import { DocumentListItem } from '../types/files'

interface FileDataState {
  documents: DocumentListItem[]
}

const initialState: FileDataState = {
  documents: [],
}

interface FileState extends FileDataState {
  setDocuments: (docs: DocumentListItem[]) => void
  addDocument: (doc: DocumentListItem) => void
  updateDocument: (id: string, partial: Partial<DocumentListItem>) => void
  removeDocument: (id: string) => void

  /**
   * Wipes all document data back to initial state.
   * MUST be called on logout — same reasoning as chatStore.reset(). This
   * store is account-scoped and has no awareness of auth state on its own.
   */
  reset: () => void
}

export const useFileStore = create<FileState>((set) => ({
  ...initialState,
  setDocuments: (docs) => set({ documents: docs }),
  addDocument: (doc) => set((s) => ({ documents: [doc, ...s.documents] })),
  updateDocument: (id, partial) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === id ? { ...d, ...partial } : d)),
    })),
  removeDocument: (id) =>
    set((s) => ({ documents: s.documents.filter((d) => d.id !== id) })),
  reset: () => set({ ...initialState }),
}))
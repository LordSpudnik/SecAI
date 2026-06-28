import client from './client'
import { DocumentListItem, DocumentStatusResponse, UploadResponse } from '../types/files'

export const filesApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post<UploadResponse>('/files/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: () => client.get<DocumentListItem[]>('/files/'),

  status: (documentId: string) =>
    client.get<DocumentStatusResponse>(`/files/${documentId}/status`),

  delete: (documentId: string) =>
    client.delete(`/files/${documentId}`),
}
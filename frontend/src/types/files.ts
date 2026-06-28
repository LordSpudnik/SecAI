export type FileType = 'pdf' | 'docx' | 'xlsx' | 'txt' | 'csv'
export type ProcessingStatus = 'queued' | 'processing' | 'ready' | 'failed'

export interface DocumentListItem {
  id: string
  filename: string
  original_filename: string
  file_type: FileType
  file_size_mb: number
  processing_status: ProcessingStatus
  vector_count: number
  uploaded_at: string
}

export interface UploadResponse {
  document_id: string
  filename: string
  status: string
}

export interface DocumentStatusResponse {
  status: ProcessingStatus
  vector_count: number
  error_message?: string | null
}
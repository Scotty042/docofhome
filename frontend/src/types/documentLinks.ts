export type DocumentTargetType = 'asset' | 'location' | 'distribution' | 'protective_device' | 'circuit'

export interface DocumentLink {
  id: string
  target_type: DocumentTargetType
  target_id: string
  document_path: string
  document_name: string
  document_etag: string | null
  available: boolean
  created_at: string
  updated_at: string
}

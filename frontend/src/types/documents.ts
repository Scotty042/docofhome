export type DocumentEntryType = 'file' | 'folder'

export interface DocumentEntry {
  name: string
  path: string
  entry_type: DocumentEntryType
  size_bytes: number
  modified_at: string | null
  content_type: string | null
  etag: string | null
}

export interface DocumentListRead {
  path: string
  root_path: string
  root_exists: boolean
  items: DocumentEntry[]
}

export interface DocumentMutationRead {
  item: DocumentEntry
  created: boolean
  overwritten: boolean
}

export interface DocumentMoveRequest {
  source_path: string
  target_parent_path: string
  name: string
}

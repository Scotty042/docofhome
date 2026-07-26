export type KnowledgeTargetType =
  | 'asset'
  | 'location'
  | 'distribution'
  | 'protective_device'
  | 'circuit'

export interface WikiPageRead {
  id: string
  parent_id: string | null
  title: string
  slug: string
  content: string
  path: string
  depth: number
  sort_order: number
  archived: boolean
  created_at: string
  updated_at: string
}

export interface WikiPageWrite {
  title: string
  content: string
  parent_id: string | null
  sort_order: number
}

export interface DomainNote {
  id: string
  target_type: KnowledgeTargetType
  target_id: string
  content: string
  created_at: string
  updated_at: string
}

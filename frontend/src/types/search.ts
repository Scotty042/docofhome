export type SearchResultType =
  | 'asset'
  | 'location'
  | 'electrical_distribution'
  | 'electrical_protective_device'
  | 'electrical_circuit'
  | 'wiki_page'
  | 'network_device'
  | 'network_segment'
  | 'consumption_meter'
  | 'document'

export interface SearchResult {
  result_type: SearchResultType
  id: string
  title: string
  subtitle: string
  description: string | null
  route: string
  archived: boolean
  matched_fields: string[]
}

export interface SearchGroup {
  result_type: SearchResultType
  label: string
  total: number
  results: SearchResult[]
}

export interface SearchResponse {
  query: string
  total: number
  groups: SearchGroup[]
}

export interface SearchRequestOptions {
  limitPerType?: number
  includeArchived?: boolean
  signal?: AbortSignal
}

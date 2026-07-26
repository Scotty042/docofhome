export type LocationType =
  | 'building'
  | 'floor'
  | 'room'
  | 'area'
  | 'cabinet'
  | 'installation_point'
  | 'outdoor'

export interface LocationBreadcrumb {
  id: string
  name: string
  location_type: LocationType
}

export interface Location {
  id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  name: string
  location_type: LocationType
  description: string | null
  parent_id: string | null
  short_name: string | null
  sort_order: number | null
  notes: string | null
  path: string
  breadcrumbs: LocationBreadcrumb[]
  direct_asset_count: number
  descendant_asset_count: number
}

export interface LocationTreeNode extends Location {
  children: LocationTreeNode[]
}

export interface LocationWrite {
  name: string
  location_type: LocationType
  description: string | null
  parent_id: string | null
  short_name: string | null
  sort_order: number | null
  notes: string | null
}

export interface LocationListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  include_deleted?: boolean
  parent_id?: string
  location_type?: LocationType | ''
}

export function createEmptyLocation(parentId: string | null = null): LocationWrite {
  return {
    name: '',
    location_type: 'area',
    description: null,
    parent_id: parentId,
    short_name: null,
    sort_order: null,
    notes: null
  }
}

export function editableLocation(location: Location): LocationWrite {
  return {
    name: location.name,
    location_type: location.location_type,
    description: location.description,
    parent_id: location.parent_id,
    short_name: location.short_name,
    sort_order: location.sort_order,
    notes: location.notes
  }
}

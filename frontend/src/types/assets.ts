import type { Location } from './locations'

export type { Location } from './locations'

export type AssetStatus = 'active' | 'inactive' | 'maintenance' | 'retired'
export type SortOrder = 'asc' | 'desc'
export type ProductImageSource = 'url' | 'upload' | 'immich' | 'online'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AssetRecord {
  id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface Reference {
  id: string
  name: string
}

export interface AssetType extends AssetRecord {
  name: string
  code_prefix: string
  description: string | null
  icon: string | null
  module_width: number | null
}

export interface AssetTypeWrite {
  name: string
  description: string | null
  icon: string | null
  module_width: number | null
}

export interface Product extends AssetRecord {
  name: string
  manufacturer: string | null
  model_number: string | null
  description: string | null
  image_url?: string | null
  image_source: ProductImageSource
  image_reference: string | null
  din_rail_mount: boolean
  module_width: number | null
  asset_type_id: string | null
}

export interface ProductWrite {
  name: string
  manufacturer: string | null
  model_number: string | null
  description: string | null
  image_url?: string | null
  image_source: ProductImageSource
  image_reference: string | null
  din_rail_mount: boolean
  module_width: number | null
  asset_type_id: string | null
}

export interface Label extends AssetRecord {
  name: string
  color: string
}

export interface LabelWrite {
  name: string
  color: string
}

export interface Asset extends AssetRecord {
  name: string
  jarvis_code: string
  description: string | null
  asset_type_id: string
  product_id: string | null
  location_id: string | null
  serial_number: string | null
  inventory_number: string | null
  module_width: number | null
  effective_module_width: number | null
  status: AssetStatus
  asset_type: Reference
  product: Reference | null
  product_image_url?: string | null
  location: Reference | null
  labels: Label[]
}

export interface AssetWrite {
  name: string
  description: string | null
  asset_type_id: string
  product_id: string | null
  location_id: string | null
  serial_number: string | null
  inventory_number: string | null
  module_width: number | null
  status: AssetStatus
  label_ids: string[]
}


export interface AssetDuplicateWrite {
  name?: string | null
  copy_location: boolean
  copy_labels: boolean
  copy_electrical_role: boolean
}

export interface AssetSeriesWrite {
  count: number
  start_number: number
  name_template: string
  copy_location: boolean
  copy_labels: boolean
  copy_electrical_role: boolean
  place_sequentially: boolean
  distribution_id: string | null
  area_id: string | null
  row_number: number | null
  start_position: number | null
}

export interface AssetSeriesRead {
  items: Asset[]
  created_count: number
}

export interface ProductImageUpload {
  image_url: string
  image_source: ProductImageSource
  image_reference: string
}

export interface ProductImageSearchItem {
  title: string
  thumbnail_url: string
  source_url: string
  image_url: string
  license_name: string | null
  author: string | null
}

export interface ProductImageSearch {
  items: ProductImageSearchItem[]
  enabled: boolean
}
export interface Relationship extends AssetRecord {
  source_asset_id: string
  target_asset_id: string
  relationship_type: string
  description: string | null
}

export interface AssetReplacement {
  archived: Asset
  replacement: Asset
  relationship: Relationship
}

export interface AssetListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  include_deleted?: boolean
  status?: AssetStatus | ''
  asset_type_id?: string
  product_id?: string
  location_id?: string
  label_id?: string
}

export function createEmptyAsset(): AssetWrite {
  return {
    name: '',
    description: null,
    asset_type_id: '',
    product_id: null,
    location_id: null,
    serial_number: null,
    inventory_number: null,
    module_width: null,
    status: 'active',
    label_ids: []
  }
}

export function editableAsset(asset: Asset): AssetWrite {
  return {
    name: asset.name,
    description: asset.description,
    asset_type_id: asset.asset_type_id,
    product_id: asset.product_id,
    location_id: asset.location_id,
    serial_number: asset.serial_number,
    inventory_number: asset.inventory_number,
    module_width: asset.module_width,
    status: asset.status,
    label_ids: asset.labels.map((label) => label.id)
  }
}

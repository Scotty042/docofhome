export type HomeAssistantObjectType = 'device' | 'entity'
export type HomeAssistantSelectionMode = 'all' | 'selected'
export type HomeAssistantSelectionScope = 'visible' | 'all'
export type HomeAssistantEntityRole =
  | 'primary_live' | 'total_power' | 'voltage' | 'current' | 'energy'
  | 'power_l1' | 'power_l2' | 'power_l3'
  | 'voltage_l1' | 'voltage_l2' | 'voltage_l3' | 'additional'

export type HomeAssistantArea = {
  area_id: string
  name: string
  floor_id: string | null
}

export type HomeAssistantDevice = {
  device_id: string
  name: string
  manufacturer: string | null
  model: string | null
  model_id: string | null
  sw_version: string | null
  hw_version: string | null
  serial_number: string | null
  area_id: string | null
  area_name: string | null
  entity_count: number
  disabled: boolean
}

export type HomeAssistantEntity = {
  entity_id: string
  name: string
  domain: string
  state: string
  unit: string | null
  device_class: string | null
  icon: string | null
  device_id: string | null
  device_name: string | null
  area_id: string | null
  area_name: string | null
  platform: string | null
  entity_category: string | null
  last_changed: string | null
  last_updated: string | null
  available: boolean
  disabled: boolean
}

export type HomeAssistantSummary = {
  location_name: string | null
  version: string | null
  time_zone: string | null
  device_count: number
  entity_count: number
  area_count: number
  unavailable_entity_count: number
  selection_mode: HomeAssistantSelectionMode
  selected_entity_count: number
  visible_device_count: number
  visible_entity_count: number
  registry_available: boolean
  warning: string | null
  refreshed_at: string
}

export type HomeAssistantOverview = {
  summary: HomeAssistantSummary
  areas: HomeAssistantArea[]
  domains: string[]
  device_classes: string[]
  units: string[]
}

export type HomeAssistantDeviceList = {
  items: HomeAssistantDevice[]
  total: number
  offset: number
  limit: number
}

export type HomeAssistantEntityList = {
  items: HomeAssistantEntity[]
  total: number
  offset: number
  limit: number
}

export type HomeAssistantDeviceQuery = {
  search?: string
  area_id?: string
  offset?: number
  limit?: number
  refresh?: boolean
  selection_scope?: HomeAssistantSelectionScope
}

export type HomeAssistantEntityQuery = {
  search?: string
  domain?: string
  device_id?: string
  area_id?: string
  available?: boolean
  device_class?: string
  unit?: string
  offset?: number
  limit?: number
  refresh?: boolean
  selection_scope?: HomeAssistantSelectionScope
}

export type HomeAssistantSelection = {
  mode: HomeAssistantSelectionMode
  entity_ids: string[]
  selected_count: number
  updated_at: string | null
}

export type HomeAssistantSelectionWrite = {
  mode: HomeAssistantSelectionMode
  entity_ids: string[]
}

export type HomeAssistantAssetLink = {
  id: string
  object_type: HomeAssistantObjectType
  external_id: string
  asset_id: string
  role: HomeAssistantEntityRole
  asset_name: string
  asset_code: string
  asset_archived: boolean
  created_at: string
  updated_at: string
}

export type HomeAssistantAssetLinkList = {
  items: HomeAssistantAssetLink[]
}


export type HomeAssistantAssetBindings = {
  asset_id: string
  device_links: HomeAssistantAssetLink[]
  entity_links: HomeAssistantAssetLink[]
  devices: HomeAssistantDevice[]
  entities: HomeAssistantEntity[]
  missing_device_ids: string[]
  missing_entity_ids: string[]
  warning: string | null
  refreshed_at: string | null
}

export type HomeAssistantEntityBindingWrite = {
  external_id: string
  role: HomeAssistantEntityRole
}

export type HomeAssistantAssetBindingsWrite = {
  device_ids: string[]
  entities: HomeAssistantEntityBindingWrite[]
}

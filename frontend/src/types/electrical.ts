import type { Page, SortOrder } from './assets'

export type { Page, SortOrder } from './assets'

export type ElectricalRole = 'distribution' | 'protective_device'
export type DistributionType = 'main' | 'sub'
export type DistributionLayoutMode = 'rows' | 'sections' | 'junction_box'
export type DistributionAreaType = 'device_rows' | 'meter' | 'connection' | 'neutral_rail' | 'protective_earth_rail' | 'technology' | 'reserve' | 'cover'
export type DistributionAreaWidth = 'full' | 'half'
export type DistributionAreaSide = 'left' | 'right'
export type ElectricalRailMountingSide = 'above' | 'below'

export type ElectricalCabinetComponentType = 'phase_distribution_block' | 'busbar' | 'phase_rail' | 'neutral_rail' | 'protective_earth_rail' | 'terminal_block' | 'connection_block' | 'potential_distribution' | 'other'
export type ProtectiveDeviceType = 'fuse' | 'rcd' | 'mcb' | 'rcbo' | 'spd'

export interface ElectricalAsset {
  id: string
  name: string
  jarvis_code: string
  location_id: string
  location_path: string
  status: string
  effective_module_width: number | null
  asset_type_name?: string
  effective_breaker_characteristic?: string | null
  effective_rated_current_a?: number | null
  technical_short_label?: string | null
}

export interface DistributionBreadcrumb {
  id: string
  display_name: string
}

export interface Distribution {
  id: string
  asset_id: string
  role: 'distribution'
  created_at: string
  updated_at: string
  deleted_at: string | null
  asset: ElectricalAsset
  parent_distribution_id: string | null
  distribution_type: DistributionType
  layout_mode: DistributionLayoutMode
  designation: string | null
  display_name: string
  rows: number | null
  modules_per_row: number | null
  description: string | null
  notes: string | null
  breadcrumbs: DistributionBreadcrumb[]
  direct_subdistribution_count: number
  direct_protective_device_count: number
}

export interface DistributionTreeNode extends Distribution {
  children: DistributionTreeNode[]
}

export interface DistributionDetail extends Distribution {
  protective_devices: ProtectiveDevice[]
}

export interface DistributionWrite {
  asset_id: string
  parent_distribution_id: string | null
  distribution_type: DistributionType
  layout_mode: DistributionLayoutMode
  designation: string | null
  rows: number | null
  modules_per_row: number | null
  description: string | null
  notes: string | null
}

export interface DistributionSection {
  id: string
  distribution_id: string
  name: string
  position: number
  description: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
  areas: DistributionArea[]
}

export interface DistributionSectionWrite {
  name: string
  position: number
  description: string | null
}

export interface DistributionArea {
  id: string
  section_id: string
  name: string
  area_type: DistributionAreaType
  position: number
  rows: number | null
  modules_per_row: number | null
  width: DistributionAreaWidth
  side: DistributionAreaSide | null
  description: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface DistributionAreaWrite {
  name: string
  area_type: DistributionAreaType
  position: number
  rows: number | null
  modules_per_row: number | null
  width: DistributionAreaWidth
  side: DistributionAreaSide | null
  description: string | null
}

export interface ElectricalMeterPlacement {
  id: string
  distribution_id: string
  area_id: string
  area_name: string
  position: number
  source_kind: 'consumption_meter' | 'asset'
  meter_id: string | null
  meter_name: string
  meter_type: string
  unit: string
  serial_number: string | null
  asset_id: string | null
  asset_name: string | null
  asset_code: string | null
  location_path: string | null
  latest_value: number | null
  latest_measured_at: string | null
  created_at: string
  updated_at: string
}

export interface ElectricalMeterPlacementWrite {
  area_id: string
  position: number
}

export interface ElectricalLiveValue {
  entity_id: string
  name: string
  role: string
  state: string
  unit: string | null
  available: boolean
  last_updated: string | null
}

export interface ElectricalAssetPlacement {
  id: string
  distribution_id: string
  area_id: string | null
  area_name: string
  asset_id: string
  asset_name: string
  asset_code: string
  asset_type_name?: string
  product_name: string | null
  location_path: string | null
  row_number: number
  start_position: number
  module_width: number
  effective_breaker_characteristic?: string | null
  effective_rated_current_a?: number | null
  technical_short_label?: string | null
  primary_live_value: ElectricalLiveValue | null
  live_values: ElectricalLiveValue[]
  live_warning: string | null
  created_at: string
  updated_at: string
}

export interface ElectricalAssetPlacementWrite {
  area_id: string | null
  row_number: number
  start_position: number
  module_width: number | null
}

export interface ElectricalCabinetComponent {
  id: string
  distribution_id: string
  distribution_name: string
  area_id: string | null
  area_name: string
  name: string
  component_type: ElectricalCabinetComponentType
  row_number: number
  start_position: number
  module_width: number
  phases: ElectricalPhase[]
  rated_current_a: number | null
  max_cross_section_mm2: number | null
  outgoing_connections: number | null
  linked_rcd_device_id: string | null
  linked_rcd_name: string | null
  start_phase: ElectricalPhase | null
  mounting_side: ElectricalRailMountingSide | null
  description: string | null
  notes: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface ElectricalCabinetComponentWrite {
  name: string
  component_type: ElectricalCabinetComponentType
  area_id: string | null
  row_number: number
  start_position: number
  module_width: number
  phases: ElectricalPhase[]
  rated_current_a: number | null
  max_cross_section_mm2: number | null
  outgoing_connections: number | null
  linked_rcd_device_id: string | null
  start_phase: ElectricalPhase | null
  mounting_side: ElectricalRailMountingSide | null
  description: string | null
  notes: string | null
}

export interface ProtectiveDevice {
  id: string
  asset_id: string
  role: 'protective_device'
  created_at: string
  updated_at: string
  deleted_at: string | null
  asset: ElectricalAsset
  distribution_id: string
  distribution_name: string
  area_id: string | null
  area_name: string | null
  device_type: ProtectiveDeviceType
  row_number: number | null
  start_position: number | null
  module_width: number | null
  rated_current_a: number | null
  residual_current_ma: number | null
  characteristic: string | null
  poles: number | null
  breaking_capacity_ka: number | null
  rcd_type: string | null
  fuse_type: string | null
  spd_type: string | null
  assigned_rcd_id: string | null
  assigned_rcd_name: string | null
  neutral_rail_id: string | null
  neutral_rail_name: string | null
  effective_rcd_id: string | null
  effective_rcd_name: string | null
  effective_neutral_rail_id: string | null
  effective_neutral_rail_name: string | null
  busbar_component_id: string | null
  busbar_component_name: string | null
  calculated_phases: ElectricalPhase[]
  group_warnings: string[]
  description: string | null
  notes: string | null
}

export interface ProtectiveDeviceWrite {
  asset_id: string
  distribution_id: string
  area_id: string | null
  device_type: ProtectiveDeviceType
  row_number: number | null
  start_position: number | null
  module_width: number | null
  rated_current_a: number | null
  residual_current_ma: number | null
  characteristic: string | null
  poles: number | null
  breaking_capacity_ka: number | null
  rcd_type: string | null
  fuse_type: string | null
  spd_type: string | null
  assigned_rcd_id?: string | null
  neutral_rail_id?: string | null
  description: string | null
  notes: string | null
}

export interface ElectricalCircuit {
  id: string
  distribution_id: string
  distribution_name: string
  protective_device_id: string | null
  protective_device_name: string | null
  protective_device_code: string | null
  name: string
  circuit_number: string | null
  description: string | null
  notes: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface ElectricalCircuitWrite {
  distribution_id: string
  protective_device_id: string | null
  name: string
  circuit_number: string | null
  description: string | null
  notes: string | null
}

export interface ElectricalCircuitAsset {
  link_id: string
  circuit_id: string
  asset_id: string
  asset_name: string
  asset_code: string
  asset_status: string
  asset_type_name: string
  location_name: string | null
  asset_deleted_at: string | null
  assigned_at: string
  removed_at: string | null
}

export type ElectricalEndpointKind = 'grid_connection' | 'asset' | 'distribution' | 'protective_device' | 'cabinet_component' | 'circuit'
export type ElectricalConnectionType = 'unknown' | 'cable' | 'wire' | 'busbar' | 'internal'
export type ElectricalPhase = 'L1' | 'L2' | 'L3' | 'N' | 'PE'

export interface ElectricalEndpoint {
  key: string
  kind: ElectricalEndpointKind
  id: string
  name: string
  code: string | null
  type_name: string
  location_name: string | null
  device_type: ProtectiveDeviceType | ElectricalCabinetComponentType | null
  effective_phases: ElectricalPhase[] | null
  deleted_at: string | null
}

export interface ElectricalConnectionWrite {
  source_kind: ElectricalEndpointKind
  source_id: string
  target_kind: ElectricalEndpointKind
  target_id: string
  connection_type: ElectricalConnectionType
  label: string | null
  phases: ElectricalPhase[]
  cable_type: string | null
  cores: number | null
  cross_section_mm2: number | null
  length_m: number | null
  route: string | null
  notes: string | null
}

export interface ElectricalConnection {
  id: string
  source: ElectricalEndpoint
  target: ElectricalEndpoint
  connection_type: ElectricalConnectionType
  label: string | null
  phases: ElectricalPhase[]
  effective_phases: ElectricalPhase[]
  phase_warnings: string[]
  cable_type: string | null
  cores: number | null
  cross_section_mm2: number | null
  length_m: number | null
  route: string | null
  notes: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface ElectricalTopologyNode {
  endpoint: ElectricalEndpoint
  source_names: string[]
  incoming_phases: ElectricalPhase[]
  downstream_protective_device_count: number
  downstream_circuit_count: number
  downstream_asset_count: number
}

export type SmartMeterMeasurementPhase = 'L1' | 'L2' | 'L3' | 'N'
export type SmartMeterMeasurementDirection = 'unspecified' | 'source_to_target' | 'target_to_source'
export type SmartMeterMeasurementEntityRole = 'power' | 'current' | 'voltage' | 'energy' | 'energy_import' | 'energy_export' | 'frequency' | 'power_factor' | 'additional'

export interface SmartMeterMeasurementEntity {
  id: string
  entity_id: string
  role: SmartMeterMeasurementEntityRole
  created_at: string
  updated_at: string
}

export interface SmartMeterMeasurementEntityWrite {
  entity_id: string
  role: SmartMeterMeasurementEntityRole
}

export interface SmartMeterMeasurementPoint {
  id: string
  smart_meter_asset_id: string
  smart_meter_asset_name: string
  smart_meter_asset_code: string
  connection_id: string
  connection_source_name: string
  connection_target_name: string
  connection_label: string | null
  channel_name: string
  name: string
  phase: SmartMeterMeasurementPhase | null
  direction: SmartMeterMeasurementDirection
  inverted: boolean
  transformer_nominal_current_a: number | null
  transformer_ratio: string | null
  notes: string | null
  entities: SmartMeterMeasurementEntity[]
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface SmartMeterMeasurementPointWrite {
  connection_id: string
  channel_name: string
  name: string
  phase: SmartMeterMeasurementPhase | null
  direction: SmartMeterMeasurementDirection
  inverted: boolean
  transformer_nominal_current_a: number | null
  transformer_ratio: string | null
  notes: string | null
  entities: SmartMeterMeasurementEntityWrite[]
}

export interface ElectricalTopology {
  nodes: ElectricalTopologyNode[]
  connections: ElectricalConnection[]
  measurement_points?: SmartMeterMeasurementPoint[]
}

export interface ProtectiveDevicePlacementWrite {
  area_id: string | null
  row_number: number | null
  start_position: number | null
  module_width: number | null
  assigned_rcd_id?: string | null
  neutral_rail_id?: string | null
}

export interface AvailableElectricalAsset {
  id: string
  name: string
  jarvis_code: string
  location_id: string
  location_path: string
  effective_module_width: number | null
}

export interface DistributionListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  include_deleted?: boolean
  distribution_type?: DistributionType | ''
  parent_distribution_id?: string
  location_id?: string
}

export interface ProtectiveDeviceListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  include_deleted?: boolean
  distribution_id?: string
  device_type?: ProtectiveDeviceType | ''
  location_id?: string
}

export interface ElectricalCircuitListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  include_deleted?: boolean
  distribution_id?: string
  protective_device_id?: string
}

export interface AvailableAssetQuery {
  role: ElectricalRole
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  current_component_id?: string
}

export interface FlatDistribution {
  distribution: Distribution
  depth: number
}

export function createEmptyDistribution(parentId: string | null = null): DistributionWrite {
  return {
    asset_id: '',
    parent_distribution_id: parentId,
    distribution_type: parentId ? 'sub' : 'main',
    layout_mode: 'rows',
    designation: null,
    rows: null,
    modules_per_row: null,
    description: null,
    notes: null
  }
}

export function editableDistribution(distribution: Distribution): DistributionWrite {
  return {
    asset_id: distribution.asset_id,
    parent_distribution_id: distribution.parent_distribution_id,
    distribution_type: distribution.distribution_type,
    layout_mode: distribution.layout_mode,
    designation: distribution.designation,
    rows: distribution.rows,
    modules_per_row: distribution.modules_per_row,
    description: distribution.description,
    notes: distribution.notes
  }
}

export function createEmptyProtectiveDevice(distributionId = ''): ProtectiveDeviceWrite {
  return {
    asset_id: '',
    distribution_id: distributionId,
    area_id: null,
    device_type: 'mcb',
    row_number: null,
    start_position: null,
    module_width: null,
    rated_current_a: null,
    residual_current_ma: null,
    characteristic: null,
    poles: null,
    breaking_capacity_ka: null,
    rcd_type: null,
    fuse_type: null,
    spd_type: null,
    assigned_rcd_id: null,
    neutral_rail_id: null,
    description: null,
    notes: null
  }
}

export function editableProtectiveDevice(device: ProtectiveDevice): ProtectiveDeviceWrite {
  return {
    asset_id: device.asset_id,
    distribution_id: device.distribution_id,
    area_id: device.area_id,
    device_type: device.device_type,
    row_number: device.row_number,
    start_position: device.start_position,
    module_width: device.module_width,
    rated_current_a: device.rated_current_a,
    residual_current_ma: device.residual_current_ma,
    characteristic: device.characteristic,
    poles: device.poles,
    breaking_capacity_ka: device.breaking_capacity_ka,
    rcd_type: device.rcd_type,
    fuse_type: device.fuse_type,
    spd_type: device.spd_type,
    assigned_rcd_id: device.assigned_rcd_id,
    neutral_rail_id: device.neutral_rail_id,
    description: device.description,
    notes: device.notes
  }
}

export function createEmptyElectricalCircuit(distributionId = ''): ElectricalCircuitWrite {
  return {
    distribution_id: distributionId,
    protective_device_id: null,
    name: '',
    circuit_number: null,
    description: null,
    notes: null
  }
}

export function editableElectricalCircuit(circuit: ElectricalCircuit): ElectricalCircuitWrite {
  return {
    distribution_id: circuit.distribution_id,
    protective_device_id: circuit.protective_device_id,
    name: circuit.name,
    circuit_number: circuit.circuit_number,
    description: circuit.description,
    notes: circuit.notes
  }
}

export function emptyPage<T>(): Page<T> {
  return { items: [], total: 0, page: 1, page_size: 25, pages: 0 }
}

export function createEmptyElectricalConnection(): ElectricalConnectionWrite {
  return {
    source_kind: 'asset',
    source_id: '',
    target_kind: 'asset',
    target_id: '',
    connection_type: 'unknown',
    label: null,
    phases: [],
    cable_type: null,
    cores: null,
    cross_section_mm2: null,
    length_m: null,
    route: null,
    notes: null
  }
}

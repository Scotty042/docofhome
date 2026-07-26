export type EnergyComponentType = 'pv_source' | 'inverter' | 'storage'

export interface EnergyConfiguration {
  grid_connection_name: string | null
  grid_operator: string | null
  energy_supplier: string | null
  metering_point_id: string | null
  connection_capacity_kw: number | null
  grid_import_meter_id: string | null
  pv_generation_meter_id: string | null
  grid_export_meter_id: string | null
  notes: string | null
  grid_import_meter_name: string | null
  pv_generation_meter_name: string | null
  grid_export_meter_name: string | null
  complete_for_balance: boolean
  updated_at: string
}

export type EnergyConfigurationWrite = Omit<
  EnergyConfiguration,
  | 'grid_import_meter_name'
  | 'pv_generation_meter_name'
  | 'grid_export_meter_name'
  | 'complete_for_balance'
  | 'updated_at'
>

export interface EnergyComponent {
  id: string
  component_type: EnergyComponentType
  name: string
  asset_id: string | null
  asset_name: string | null
  manufacturer: string | null
  model: string | null
  serial_number: string | null
  rated_power_kw: number | null
  capacity_kwh: number | null
  sort_order: number
  notes: string | null
  archived: boolean
  created_at: string
  updated_at: string
}

export type EnergyComponentWrite = Omit<
  EnergyComponent,
  'id' | 'asset_name' | 'archived' | 'created_at' | 'updated_at'
>

export interface EnergyBalancePeriod {
  label: string
  period_start: string
  period_end: string
  grid_import_kwh: number | null
  pv_generation_kwh: number | null
  grid_export_kwh: number | null
  house_consumption_kwh: number | null
  self_consumption_kwh: number | null
  autonomy_percent: number | null
  self_consumption_rate_percent: number | null
  estimated: boolean
  incomplete: boolean
}

export interface EnergyBalance {
  months: number
  configuration_complete: boolean
  periods: EnergyBalancePeriod[]
}

export const energyComponentLabels: Record<EnergyComponentType, string> = {
  pv_source: 'PV-Energiequelle',
  inverter: 'Wechselrichter',
  storage: 'Speicher'
}

export const energyComponentIcons: Record<EnergyComponentType, string> = {
  pv_source: 'mdi-solar-power-variant',
  inverter: 'mdi-sine-wave',
  storage: 'mdi-battery-high'
}

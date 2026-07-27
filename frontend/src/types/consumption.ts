export type ConsumptionMeterType = 'water' | 'electricity_grid' | 'electricity_pv' | 'electricity_feed_in' | 'gas' | 'heat' | 'oil' | 'other'
export type ConsumptionWaterRole = 'none' | 'main' | 'eg_component'
export type ConsumptionReadingSource = 'manual' | 'csv' | 'legacy_sqlite' | 'home_assistant'
export type ConsumptionNoteScope = 'general' | 'month' | 'year'

export interface ConsumptionMeter {
  id: string
  name: string
  meter_type: ConsumptionMeterType
  unit: string
  decimals: number
  sort_order: number
  serial_number: string | null
  asset_id: string | null
  asset_name: string | null
  asset_code: string | null
  location_id: string | null
  location_name: string | null
  location_path: string | null
  parent_meter_id: string | null
  parent_meter_name: string | null
  home_assistant_entity_id: string | null
  home_assistant_power_entity_id: string | null
  home_assistant_voltage_entity_id: string | null
  water_role: ConsumptionWaterRole
  primary_for_dashboard: boolean
  reading_schedule_day: number | null
  reading_schedule_last_day: boolean
  reminder_days: number[]
  notes: string | null
  latest_value: number | null
  latest_measured_at: string | null
  reading_count: number
  due_for_reading: boolean
  archived: boolean
  created_at: string
  updated_at: string
}

export interface ConsumptionMeterWrite {
  name: string
  meter_type: ConsumptionMeterType
  unit: string
  decimals: number
  sort_order: number
  serial_number: string | null
  asset_id: string | null
  location_id: string | null
  parent_meter_id: string | null
  home_assistant_entity_id: string | null
  home_assistant_power_entity_id: string | null
  home_assistant_voltage_entity_id: string | null
  water_role: ConsumptionWaterRole
  primary_for_dashboard: boolean
  reading_schedule_day: number | null
  reading_schedule_last_day: boolean
  reminder_days: number[]
  notes: string | null
}

export interface ConsumptionMeterLive {
  meter_id: string
  power_entity_id: string | null
  voltage_entity_id: string | null
  power_w: number | null
  voltage_v: number | null
  power_updated_at: string | null
  voltage_updated_at: string | null
  available: boolean
  warning: string | null
}

export interface ConsumptionReading {
  id: string
  meter_id: string
  meter_name: string
  unit: string
  decimals: number
  measured_at: string
  value: number
  previous_value: number | null
  delta: number | null
  note: string | null
  source: ConsumptionReadingSource
  is_reset: boolean
  immich_asset_id: string | null
  immich_original_file_name: string | null
  immich_thumbnail_url: string | null
  plausibility_warning: boolean
  plausibility_message: string | null
  created_at: string
  updated_at: string
}

export interface ConsumptionReadingWrite {
  meter_id: string
  measured_at: string
  value: number
  note: string | null
  source: ConsumptionReadingSource
  is_reset: boolean
  immich_asset_id: string | null
  immich_original_file_name: string | null
}

export interface ConsumptionMeterReplacementWrite {
  replaced_at: string
  old_final_value: number
  new_serial_number: string
  new_start_value: number
  note: string | null
}

export interface ConsumptionNote {
  id: string
  note_date: string
  scope: ConsumptionNoteScope
  title: string
  note: string | null
  created_at: string
  updated_at: string
}

export interface ConsumptionNoteWrite {
  note_date: string
  scope: ConsumptionNoteScope
  title: string
  note: string | null
}

export interface ConsumptionSettings {
  reminder_days: number
  plausibility_threshold_percent: number
  updated_at: string
}

export interface ConsumptionSettingsWrite {
  reminder_days: number
  plausibility_threshold_percent: number
}

export interface ConsumptionPeriodResult {
  value: number | null
  estimated: boolean
  incomplete: boolean
  reset_detected: boolean
}

export interface ConsumptionSeriesPoint {
  label: string
  period_start: string
  period_end: string
  result: ConsumptionPeriodResult
}

export interface ConsumptionSeries {
  key: string
  name: string
  meter_id: string | null
  meter_type: ConsumptionMeterType
  unit: string
  decimals: number
  virtual: boolean
  description: string | null
  points: ConsumptionSeriesPoint[]
}

export interface ConsumptionStatistics {
  months: number
  series: ConsumptionSeries[]
}

export interface ConsumptionSummaryItem {
  key: string
  name: string
  description: string
  unit: string
  decimals: number
  result: ConsumptionPeriodResult
}

export interface ConsumptionSummary {
  meter_count: number
  reading_count: number
  readings_last_30_days: number
  meters_without_readings: number
  meters_due_for_reading: number
  last_reading_at: string | null
  current_month: ConsumptionSummaryItem[]
}

export interface ConsumptionImportPreview {
  format: string
  file_name: string
  meter_count: number
  reading_count: number
  note_count: number
  matched_meters: string[]
  missing_meters: string[]
  warnings: string[]
}

export interface ConsumptionImportResult {
  format: string
  file_name: string
  meters_created: number
  readings_created: number
  readings_updated: number
  duplicates_skipped: number
  rows_skipped: number
  notes_created: number
  settings_imported: boolean
  errors: string[]
}

export interface ConsumptionDefaultSeed {
  created: number
  existing: number
  meters: ConsumptionMeter[]
}

export interface ConsumptionComparison {
  medium: 'water' | 'electricity' | 'pv_generation' | 'pv_feed_in' | 'gas'
  name: string
  meter_id: string | null
  unit: string | null
  decimals: number
  current_value: number | null
  previous_value: number | null
  difference: number | null
  percent_change: number | null
  trend: 'increased' | 'decreased' | 'equal' | 'unavailable'
  comparison_available: boolean
  incomplete: boolean
}

export interface ConsumptionReadingReminder {
  meter_id: string
  meter_name: string
  unit: string
  due_at: string
  days_remaining: number
  status: 'upcoming' | 'today' | 'overdue'
}

export const consumptionMeterTypeLabels: Record<ConsumptionMeterType, string> = {
  water: 'Wasser',
  electricity_grid: 'Strom Netzbezug',
  electricity_pv: 'PV-Erzeugung',
  electricity_feed_in: 'Netzeinspeisung',
  gas: 'Gas',
  heat: 'Wärme',
  oil: 'Heizöl',
  other: 'Sonstiges'
}

export const consumptionMeterTypeIcons: Record<ConsumptionMeterType, string> = {
  water: 'mdi-water-pump',
  electricity_grid: 'mdi-flash',
  electricity_pv: 'mdi-solar-power-variant',
  electricity_feed_in: 'mdi-export',
  gas: 'mdi-counter',
  heat: 'mdi-radiator',
  oil: 'mdi-counter',
  other: 'mdi-counter'
}

export const consumptionSourceLabels: Record<ConsumptionReadingSource, string> = {
  manual: 'Manuell',
  csv: 'CSV-Import',
  legacy_sqlite: 'Altdatenbank',
  home_assistant: 'Home Assistant'
}

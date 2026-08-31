<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'

import EnergyBalanceCard from '../components/EnergyBalanceCard.vue'
import ImmichReadingPicker from '../components/ImmichReadingPicker.vue'
import { assetApi } from '../services/assetApi'
import { consumptionApi } from '../services/consumptionApi'
import { homeAssistantApi } from '../services/homeAssistantApi'
import { locationApi } from '../services/locationApi'
import { locationSelectItems } from '../services/locationOptions'
import { useNotificationStore } from '../stores/notifications'
import { consumptionSeriesMax } from '../services/consumptionPresentation'
import type { Asset } from '../types/assets'
import type { HomeAssistantEntity } from '../types/homeAssistant'
import type { LocationSelectItem } from '../services/locationOptions'
import type {
  ConsumptionImportPreview,
  ConsumptionImportResult,
  ConsumptionMeter,
  ConsumptionMeterReplacementWrite,
  ConsumptionMeterLive,
  ConsumptionMeterType,
  ConsumptionMeterWrite,
  ConsumptionReading,
  ConsumptionReadingWrite,
  ConsumptionSettings,
  ConsumptionSeries,
  ConsumptionSeriesPoint,
  ConsumptionStatistics,
  ConsumptionSummary
} from '../types/consumption'
import {
  consumptionMeterTypeIcons,
  consumptionMeterTypeLabels,
  consumptionSourceLabels
} from '../types/consumption'

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const notice = ref<string | null>(null)
const tab = ref('overview')
const summary = ref<ConsumptionSummary | null>(null)
const statistics = ref<ConsumptionStatistics | null>(null)
const meters = ref<ConsumptionMeter[]>([])
const readings = ref<ConsumptionReading[]>([])
const settings = ref<ConsumptionSettings | null>(null)
const assets = ref<Asset[]>([])
const locationItems = ref<LocationSelectItem[]>([])
const homeAssistantEntities = ref<HomeAssistantEntity[]>([])
const liveValues = ref<Record<string, ConsumptionMeterLive>>({})
const liveLoading = ref<Set<string>>(new Set())
const months = ref(12)
const chartMode = ref<'month' | 'year'>('month')
const chartDialog = ref(false)
const enlargedSeries = ref<ConsumptionSeries | null>(null)
const selectedChartPoint = ref<{ series: ConsumptionSeries; point: ConsumptionSeriesPoint } | null>(null)
const search = ref('')
const typeFilter = ref<ConsumptionMeterType | ''>('')
const selectedMeterId = ref<string | null>(null)
const route = useRoute()
const { smAndDown } = useDisplay()
const notifications = useNotificationStore()

const meterDialog = ref(false)
const editingMeter = ref<ConsumptionMeter | null>(null)
const meterForm = ref<ConsumptionMeterWrite>(emptyMeter())
const readingDialog = ref(false)
const editingReading = ref<ConsumptionReading | null>(null)
const readingForm = ref<ConsumptionReadingWrite>(emptyReading())
const replacementDialog = ref(false)
const replacementMeter = ref<ConsumptionMeter | null>(null)
const replacementForm = ref<ConsumptionMeterReplacementWrite>({
  replaced_at: currentLocalDateTime(),
  old_final_value: 0,
  new_serial_number: '',
  new_start_value: 0,
  note: null
})
const importDialog = ref(false)
const importFile = ref<File | null>(null)
const importPreview = ref<ConsumptionImportPreview | null>(null)
const importResult = ref<ConsumptionImportResult | null>(null)
const createMissingMeters = ref(true)
const overwriteImport = ref(false)

const meterTypeItems = Object.entries(consumptionMeterTypeLabels).map(([value, title]) => ({ value, title }))
const waterRoleItems = [
  { value: 'none', title: 'Keine besondere Rolle' },
  { value: 'main', title: 'Hauptwasserzähler' },
  { value: 'eg_component', title: 'Bestandteil EG-Verbrauch' }
]

const assetItems = computed(() => assets.value.map((asset) => ({
  value: asset.id,
  title: `${asset.name} · ${asset.jarvis_code}`
})))
const entityItems = computed(() => homeAssistantEntities.value.map((entity) => ({
  value: entity.entity_id,
  title: `${entity.name} · ${entity.entity_id}${entity.unit ? ` · ${entity.unit}` : ''}`
})))

const filteredMeters = computed(() => meters.value.filter((meter) => {
  const query = search.value.trim().toLocaleLowerCase()
  const haystack = [meter.name, meter.serial_number, meter.location_path, meter.asset_name, meter.home_assistant_entity_id, meter.home_assistant_power_entity_id, meter.home_assistant_voltage_entity_id]
    .filter(Boolean).join(' ').toLocaleLowerCase()
  return (!typeFilter.value || meter.meter_type === typeFilter.value) && (!query || haystack.includes(query))
}))
const selectedReadings = computed(() => readings.value.filter((reading) => !selectedMeterId.value || reading.meter_id === selectedMeterId.value))
const selectedReadingMeter = computed(() => meters.value.find((meter) => meter.id === readingForm.value.meter_id) ?? null)
const selectedReadingObis = computed(() => {
  if (selectedReadingMeter.value?.meter_type === 'electricity_grid') return 'OBIS 1.8.0 · bezogene Energie'
  if (selectedReadingMeter.value?.meter_type === 'electricity_feed_in') return 'OBIS 2.8.0 · eingespeiste Energie'
  return null
})
const displayedSeries = computed(() => {
  if (chartMode.value === 'month') return statistics.value?.series ?? []
  return (statistics.value?.series ?? []).map((series) => {
    const years = new Map<string, ConsumptionSeriesPoint[]>()
    for (const point of series.points) {
      const year = point.period_start.slice(0, 4)
      years.set(year, [...(years.get(year) ?? []), point])
    }
    return {
      ...series,
      points: [...years.entries()].map(([year, points]) => {
        const values = points.map((point) => point.result.value).filter((value): value is number => value !== null)
        return {
          label: year,
          period_start: `${year}-01-01`,
          period_end: `${year}-12-31`,
          result: {
            value: values.length ? values.reduce((sum, value) => sum + value, 0) : null,
            estimated: points.some((point) => point.result.estimated),
            incomplete: points.some((point) => point.result.incomplete) || values.length < points.length,
            reset_detected: points.some((point) => point.result.reset_detected)
          }
        }
      })
    }
  })
})

function selectChartPoint(series: ConsumptionSeries, point: ConsumptionSeriesPoint) {
  selectedChartPoint.value = { series, point }
}

function emptyMeter(): ConsumptionMeterWrite {
  return {
    name: '', meter_type: 'water', unit: 'm³', decimals: 3, sort_order: 100,
    serial_number: null, asset_id: null, location_id: null, parent_meter_id: null,
    home_assistant_entity_id: null, home_assistant_power_entity_id: null,
    home_assistant_voltage_entity_id: null, water_role: 'none',
    primary_for_dashboard: false, reading_schedule_day: null,
    reading_schedule_last_day: false, reminder_days: [], notes: null
  }
}
function emptyReading(): ConsumptionReadingWrite {
  return {
    meter_id: selectedMeterId.value ?? '', measured_at: currentLocalDateTime(), value: 0,
    note: null, source: 'manual', is_reset: false, immich_asset_id: null, immich_original_file_name: null
  }
}
function currentLocalDateTime(date = new Date()): string {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}
function formatDate(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '–'
}
function formatValue(value: number | null | undefined, decimals = 2, unit = '') {
  return value === null || value === undefined ? '–' : `${new Intl.NumberFormat('de-DE', { maximumFractionDigits: decimals }).format(value)}${unit ? ` ${unit}` : ''}`
}
function setError(reason: unknown, fallback: string) {
  const message = reason instanceof Error ? reason.message : fallback
  error.value = message
  notifications.error(message)
}

function setNotice(message: string) {
  notice.value = message
  notifications.success(message)
}

async function loadAll() {
  loading.value = true
  error.value = null
  try {
    const [summaryData, statisticsData, meterData, readingData, settingsData] = await Promise.all([
      consumptionApi.summary(), consumptionApi.statistics(months.value), consumptionApi.meters(),
      consumptionApi.readings({ limit: 1000 }), consumptionApi.settings()
    ])
    summary.value = summaryData
    statistics.value = statisticsData
    meters.value = meterData
    readings.value = readingData
    settings.value = settingsData
    await loadLiveValues()
  } catch (reason) {
    setError(reason, 'Verbrauchsdaten konnten nicht geladen werden.')
  } finally {
    loading.value = false
  }
}
async function reloadStatistics() {
  try { statistics.value = await consumptionApi.statistics(months.value) }
  catch (reason) { setError(reason, 'Statistik konnte nicht geladen werden.') }
}
async function loadMeterReferences() {
  try {
    const [assetData, locationTree] = await Promise.all([assetApi.allAssets(), locationApi.tree()])
    assets.value = assetData
    locationItems.value = locationSelectItems(locationTree)
  } catch (reason) {
    setError(reason, 'Orte und Assets konnten nicht geladen werden.')
  }
  try {
    homeAssistantEntities.value = await homeAssistantApi.allEntities({
      domain: 'sensor', available: true, selection_scope: 'all'
    })
  } catch {
    homeAssistantEntities.value = []
  }
}

async function loadLiveValue(meter: ConsumptionMeter, refresh = false) {
  if (!meter.home_assistant_power_entity_id && !meter.home_assistant_voltage_entity_id) return
  const next = new Set(liveLoading.value)
  next.add(meter.id)
  liveLoading.value = next
  try {
    liveValues.value = {
      ...liveValues.value,
      [meter.id]: await consumptionApi.live(meter.id, refresh)
    }
  } catch (reason) {
    liveValues.value = {
      ...liveValues.value,
      [meter.id]: {
        meter_id: meter.id, power_entity_id: meter.home_assistant_power_entity_id,
        voltage_entity_id: meter.home_assistant_voltage_entity_id, power_w: null, voltage_v: null,
        power_updated_at: null, voltage_updated_at: null, available: false,
        warning: reason instanceof Error ? reason.message : 'Livewerte nicht verfügbar'
      }
    }
  } finally {
    const current = new Set(liveLoading.value)
    current.delete(meter.id)
    liveLoading.value = current
  }
}

async function loadLiveValues() {
  for (const meter of meters.value) await loadLiveValue(meter)
}

function selectMeterAsset(assetId: string | null) {
  if (!assetId || meterForm.value.location_id) return
  const asset = assets.value.find((item) => item.id === assetId)
  if (asset?.location_id) meterForm.value.location_id = asset.location_id
}

function openMeter(meter?: ConsumptionMeter) {
  editingMeter.value = meter ?? null
  meterForm.value = meter ? {
    name: meter.name, meter_type: meter.meter_type, unit: meter.unit, decimals: meter.decimals,
    sort_order: meter.sort_order, serial_number: meter.serial_number, asset_id: meter.asset_id,
    location_id: meter.location_id, parent_meter_id: meter.parent_meter_id,
    home_assistant_entity_id: meter.home_assistant_entity_id,
    home_assistant_power_entity_id: meter.home_assistant_power_entity_id,
    home_assistant_voltage_entity_id: meter.home_assistant_voltage_entity_id, water_role: meter.water_role,
    primary_for_dashboard: meter.primary_for_dashboard,
    reading_schedule_day: meter.reading_schedule_day,
    reading_schedule_last_day: meter.reading_schedule_last_day,
    reminder_days: meter.reminder_days,
    notes: meter.notes
  } : emptyMeter()
  meterDialog.value = true
}
function applyTypeDefaults(type: ConsumptionMeterType) {
  const defaults: Record<ConsumptionMeterType, { unit: string; decimals: number }> = {
    water: { unit: 'm³', decimals: 3 }, electricity_grid: { unit: 'kWh', decimals: 1 },
    electricity_pv: { unit: 'kWh', decimals: 1 }, electricity_feed_in: { unit: 'kWh', decimals: 1 }, gas: { unit: 'm³', decimals: 3 },
    heat: { unit: 'kWh', decimals: 1 }, oil: { unit: 'l', decimals: 0 }, other: { unit: '', decimals: 2 }
  }
  meterForm.value.unit = defaults[type].unit
  meterForm.value.decimals = defaults[type].decimals
  if (type !== 'water') meterForm.value.water_role = 'none'
}
async function saveMeter() {
  saving.value = true; error.value = null
  try {
    if (editingMeter.value) await consumptionApi.updateMeter(editingMeter.value.id, meterForm.value)
    else await consumptionApi.createMeter(meterForm.value)
    meterDialog.value = false; setNotice('Zähler wurde gespeichert.'); await loadAll()
  } catch (reason) { setError(reason, 'Zähler konnte nicht gespeichert werden.') }
  finally { saving.value = false }
}
async function archiveMeter(meter: ConsumptionMeter) {
  if (!confirm(`Zähler „${meter.name}“ archivieren? Die Ablesungen bleiben erhalten.`)) return
  try { await consumptionApi.removeMeter(meter.id); await loadAll() }
  catch (reason) { setError(reason, 'Zähler konnte nicht archiviert werden.') }
}
function openReading(reading?: ConsumptionReading, meterId?: string) {
  editingReading.value = reading ?? null
  readingForm.value = reading ? {
    meter_id: reading.meter_id, measured_at: reading.measured_at.slice(0, 16), value: reading.value,
    note: reading.note, source: reading.source, is_reset: reading.is_reset,
    immich_asset_id: reading.immich_asset_id, immich_original_file_name: reading.immich_original_file_name
  } : { ...emptyReading(), meter_id: meterId ?? selectedMeterId.value ?? meters.value[0]?.id ?? '' }
  readingDialog.value = true
}
function openReplacement(meter: ConsumptionMeter) {
  replacementMeter.value = meter
  replacementForm.value = {
    replaced_at: currentLocalDateTime(),
    old_final_value: meter.latest_value ?? 0,
    new_serial_number: '',
    new_start_value: 0,
    note: null
  }
  replacementDialog.value = true
}
async function saveReplacement() {
  if (!replacementMeter.value) return
  saving.value = true
  error.value = null
  try {
    await consumptionApi.replaceMeter(replacementMeter.value.id, {
      ...replacementForm.value,
      replaced_at: new Date(replacementForm.value.replaced_at).toISOString()
    })
    replacementDialog.value = false
    setNotice('Zählerwechsel wurde mit Alt- und Startstand gespeichert.')
    await loadAll()
  } catch (reason) {
    setError(reason, 'Zählerwechsel konnte nicht gespeichert werden.')
  } finally {
    saving.value = false
  }
}
async function saveReading() {
  saving.value = true; error.value = null
  try {
    const payload = { ...readingForm.value, measured_at: new Date(readingForm.value.measured_at).toISOString() }
    if (editingReading.value) await consumptionApi.updateReading(editingReading.value.id, payload)
    else await consumptionApi.createReading(payload)
    readingDialog.value = false; setNotice('Ablesung wurde gespeichert.'); await loadAll()
  } catch (reason) { setError(reason, 'Ablesung konnte nicht gespeichert werden.') }
  finally { saving.value = false }
}
async function archiveReading(reading: ConsumptionReading) {
  if (!confirm('Diese Ablesung archivieren?')) return
  try { await consumptionApi.removeReading(reading.id); await loadAll() }
  catch (reason) { setError(reason, 'Ablesung konnte nicht archiviert werden.') }
}
async function captureHomeAssistant(meter: ConsumptionMeter) {
  try { await consumptionApi.captureHomeAssistant(meter.id); setNotice('Home-Assistant-Wert wurde übernommen.'); await loadAll() }
  catch (reason) { setError(reason, 'Home-Assistant-Wert konnte nicht übernommen werden.') }
}
async function seedDefaults() {
  try {
    const result = await consumptionApi.seedDefaults()
    setNotice(`${result.created} Standardzähler angelegt, ${result.existing} bereits vorhanden.`)
    await loadAll()
  } catch (reason) { setError(reason, 'Standardzähler konnten nicht angelegt werden.') }
}
async function saveSettings() {
  if (!settings.value) return
  try { settings.value = await consumptionApi.updateSettings({ reminder_days: settings.value.reminder_days, plausibility_threshold_percent: settings.value.plausibility_threshold_percent }); setNotice('Einstellungen gespeichert.') }
  catch (reason) { setError(reason, 'Einstellungen konnten nicht gespeichert werden.') }
}
function pickImportFile(files: File | File[] | null) {
  importFile.value = Array.isArray(files) ? files[0] ?? null : files
  importPreview.value = null; importResult.value = null
}
async function previewImport() {
  if (!importFile.value) return
  saving.value = true
  try { importPreview.value = await consumptionApi.previewImport(importFile.value) }
  catch (reason) { setError(reason, 'Importvorschau konnte nicht erstellt werden.') }
  finally { saving.value = false }
}
async function executeImport() {
  if (!importFile.value) return
  saving.value = true
  try {
    importResult.value = await consumptionApi.importFile(importFile.value, createMissingMeters.value, overwriteImport.value)
    setNotice('Import wurde verarbeitet.'); await loadAll()
  } catch (reason) { setError(reason, 'Import konnte nicht ausgeführt werden.') }
  finally { saving.value = false }
}

onMounted(async () => {
  await loadMeterReferences()
  await loadAll()
  const meterId = typeof route.query.read === 'string' ? route.query.read : null
  if (meterId && meters.value.some((meter) => meter.id === meterId)) {
    tab.value = 'readings'
    openReading(undefined, meterId)
  } else if (route.query.capture === '1') {
    tab.value = 'readings'
    openReading()
  }
})
</script>

<template>
  <v-container fluid class="pa-3 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-4">
      <div>
        <h1 class="text-h4 font-weight-bold">Verbrauch</h1>
        <div class="text-medium-emphasis">Zählerstände, Monatsverbräuche und virtuelle Wassergruppen</div>
      </div>
      <v-spacer />
      <v-btn prepend-icon="mdi-database-import-outline" variant="tonal" @click="importDialog = true">Import</v-btn>
      <v-btn prepend-icon="mdi-plus" color="primary" @click="openReading()">Ablesung</v-btn>
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error = null">{{ error }}</v-alert>
    <v-alert v-if="notice" type="success" closable class="mb-4" @click:close="notice = null">{{ notice }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-tabs v-model="tab" class="mb-4" show-arrows>
      <v-tab value="overview">Übersicht</v-tab>
      <v-tab value="meters">Zähler</v-tab>
      <v-tab value="readings">Ablesungen</v-tab>
      <v-tab value="statistics">Statistik</v-tab>
      <v-tab value="energy">PV & Energiebilanz</v-tab>
      <v-tab value="settings">Einstellungen</v-tab>
    </v-tabs>

    <v-window v-model="tab" :touch="false">
      <v-window-item value="overview">
        <v-row>
          <v-col v-for="item in [
            { label: 'Zähler', value: summary?.meter_count ?? 0, icon: 'mdi-counter' },
            { label: 'Ablesungen', value: summary?.reading_count ?? 0, icon: 'mdi-clipboard-check-outline' },
            { label: 'Fällige Ablesungen', value: summary?.meters_due_for_reading ?? 0, icon: 'mdi-clock-outline' },
            { label: 'Ohne Ablesung', value: summary?.meters_without_readings ?? 0, icon: 'mdi-alert-outline' }
          ]" :key="item.label" cols="12" sm="6" lg="3">
            <v-card><v-card-text class="d-flex align-center ga-4"><v-icon :icon="item.icon" size="36" /><div><div class="text-h4">{{ item.value }}</div><div class="text-medium-emphasis">{{ item.label }}</div></div></v-card-text></v-card>
          </v-col>
        </v-row>
        <v-card class="mt-4">
          <v-card-title>Aktueller Monat · bis heute</v-card-title>
          <v-card-text>
            <v-row v-if="summary?.current_month.length">
              <v-col v-for="item in summary.current_month" :key="item.key" cols="12" md="6" lg="4">
                <v-sheet border rounded class="pa-4 h-100">
                  <div class="text-subtitle-1 font-weight-bold">{{ item.name }}</div>
                  <div class="text-h5 mt-2">{{ formatValue(item.result.value, item.decimals, item.unit) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ item.description }}</div>
                  <v-chip v-if="item.result.incomplete" size="small" color="warning" class="mt-2">Unvollständig</v-chip>
                  <v-chip v-if="item.result.estimated" size="small" class="mt-2 ml-2">Geschätzt</v-chip>
                </v-sheet>
              </v-col>
            </v-row>
            <v-empty-state v-else icon="mdi-chart-line" title="Noch keine Monatswerte" text="Lege Zähler und mindestens zwei passende Ablesungen an." />
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="meters">
        <v-card>
          <v-card-title class="d-flex flex-wrap align-center ga-2">
            Zähler
            <v-spacer />
            <v-btn size="small" variant="text" prepend-icon="mdi-auto-fix" @click="seedDefaults">Standardzähler</v-btn>
            <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="openMeter()">Zähler</v-btn>
          </v-card-title>
          <v-card-text>
            <v-row dense class="mb-3"><v-col cols="12" md="8"><v-text-field v-model="search" label="Zähler suchen" prepend-inner-icon="mdi-magnify" hide-details clearable /></v-col><v-col cols="12" md="4"><v-select v-model="typeFilter" :items="[{ value: '', title: 'Alle Arten' }, ...meterTypeItems]" label="Art" hide-details /></v-col></v-row>
            <v-table hover>
              <thead><tr><th>Zähler</th><th>Letzter Stand</th><th>Ort / Asset</th><th>Quelle</th><th class="text-right">Aktionen</th></tr></thead>
              <tbody>
                <tr v-for="meter in filteredMeters" :key="meter.id">
                  <td><div class="d-flex align-center ga-2"><v-icon :icon="consumptionMeterTypeIcons[meter.meter_type]" /><div><strong>{{ meter.name }}</strong><div class="text-caption text-medium-emphasis">{{ consumptionMeterTypeLabels[meter.meter_type] }} · {{ meter.unit }}</div></div></div></td>
                  <td>{{ formatValue(meter.latest_value, meter.decimals, meter.unit) }}<div class="text-caption">{{ formatDate(meter.latest_measured_at) }}</div></td>
                  <td>{{ meter.location_path || meter.asset_name || '–' }}</td>
                  <td>
                    <div v-if="liveValues[meter.id]?.available" class="d-flex flex-column ga-1">
                      <v-chip size="small" prepend-icon="mdi-home-assistant">
                        <span v-if="liveValues[meter.id].power_w !== null">{{ formatValue(liveValues[meter.id].power_w, 0, 'W') }}</span>
                        <span v-if="liveValues[meter.id].power_w !== null && liveValues[meter.id].voltage_v !== null"> · </span>
                        <span v-if="liveValues[meter.id].voltage_v !== null">{{ formatValue(liveValues[meter.id].voltage_v, 1, 'V') }}</span>
                      </v-chip>
                      <span class="text-caption text-medium-emphasis">Live aus Home Assistant</span>
                    </div>
                    <v-chip v-else-if="meter.home_assistant_entity_id || meter.home_assistant_power_entity_id || meter.home_assistant_voltage_entity_id" size="small" prepend-icon="mdi-home-assistant">Home Assistant</v-chip>
                    <span v-else>Manuell</span>
                  </td>
                  <td class="text-right text-no-wrap">
                    <v-btn v-if="meter.home_assistant_power_entity_id || meter.home_assistant_voltage_entity_id" icon="mdi-refresh" size="small" variant="text" title="Livewerte aktualisieren" :loading="liveLoading.has(meter.id)" @click="loadLiveValue(meter, true)" />
                    <v-btn v-if="meter.home_assistant_entity_id" icon="mdi-download" size="small" variant="text" title="Aktuellen HA-Wert übernehmen" @click="captureHomeAssistant(meter)" />
                    <v-btn icon="mdi-plus" size="small" variant="text" title="Ablesung" @click="openReading(undefined, meter.id)" />
                    <v-btn icon="mdi-swap-horizontal" size="small" variant="text" title="Zähler austauschen" @click="openReplacement(meter)" />
                    <v-btn icon="mdi-pencil" size="small" variant="text" @click="openMeter(meter)" />
                    <v-btn icon="mdi-archive-outline" size="small" variant="text" color="error" @click="archiveMeter(meter)" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="readings">
        <v-card>
          <v-card-title class="d-flex flex-wrap align-center ga-2">Ablesungen<v-spacer /><v-select v-model="selectedMeterId" :items="[{ value: null, title: 'Alle Zähler' }, ...meters.map(m => ({ value: m.id, title: m.name }))]" label="Zähler" density="compact" hide-details style="max-width: 280px" /><v-btn color="primary" prepend-icon="mdi-plus" @click="openReading()">Ablesung</v-btn></v-card-title>
          <v-card-text>
            <v-table hover><thead><tr><th>Zeitpunkt</th><th>Zähler</th><th>Stand</th><th>Verbrauch</th><th>Quelle</th><th class="text-right">Aktionen</th></tr></thead><tbody>
              <tr v-for="reading in selectedReadings" :key="reading.id"><td>{{ formatDate(reading.measured_at) }}</td><td>{{ reading.meter_name }}</td><td>{{ formatValue(reading.value, reading.decimals, reading.unit) }}</td><td><span v-if="reading.delta !== null">{{ formatValue(reading.delta, reading.decimals, reading.unit) }}</span><v-chip v-if="reading.plausibility_warning" size="x-small" color="warning" class="ml-2">Prüfen</v-chip></td><td>{{ consumptionSourceLabels[reading.source] }}</td><td class="text-right"><v-btn icon="mdi-pencil" size="small" variant="text" @click="openReading(reading)" /><v-btn icon="mdi-archive-outline" size="small" variant="text" color="error" @click="archiveReading(reading)" /></td></tr>
            </tbody></v-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="statistics">
        <v-card>
          <v-card-title class="d-flex flex-wrap align-center ga-2">
            Verbrauchsvergleich
            <v-spacer />
            <v-btn-toggle v-model="chartMode" mandatory density="compact" color="primary">
              <v-btn value="month">Monate</v-btn><v-btn value="year">Jahre</v-btn>
            </v-btn-toggle>
            <v-select v-model="months" :items="[6, 12, 24, 36]" label="Zeitraum (Monate)" density="compact" hide-details style="max-width: 180px" @update:model-value="reloadStatistics" />
          </v-card-title>
          <v-card-text>
            <v-alert v-if="selectedChartPoint" type="info" variant="tonal" closable class="mb-4" @click:close="selectedChartPoint = null">
              {{ selectedChartPoint.series.name }} · {{ selectedChartPoint.point.label }}:
              {{ formatValue(selectedChartPoint.point.result.value, selectedChartPoint.series.decimals, selectedChartPoint.series.unit) }}
              <span v-if="selectedChartPoint.point.result.incomplete"> · Zeitraum unvollständig</span>
            </v-alert>
            <div v-for="series in displayedSeries" :key="series.key" class="mb-7">
              <div class="d-flex align-center ga-2 mb-2">
                <v-icon :icon="consumptionMeterTypeIcons[series.meter_type]" /><strong>{{ series.name }}</strong>
                <v-chip v-if="series.virtual" size="x-small">Virtuell</v-chip>
                <v-spacer />
                <v-btn icon="mdi-fullscreen" size="small" variant="text" :aria-label="`${series.name} vergrößern`" @click="enlargedSeries = series; chartDialog = true" />
              </div>
              <div class="chart-scroll">
                <div class="bar-chart">
                  <button
                    v-for="point in series.points"
                    :key="point.period_start"
                    type="button"
                    class="bar-column"
                    :aria-label="`${point.label}: ${formatValue(point.result.value, series.decimals, series.unit)}${point.result.incomplete ? ', unvollständig' : ''}`"
                    @click="selectChartPoint(series, point)"
                  >
                    <span class="bar-value">{{ point.result.value === null ? '–' : formatValue(point.result.value, series.decimals) }}</span>
                    <span class="bar" :style="{ height: point.result.value === null ? '0' : `${Math.max(2, (point.result.value / consumptionSeriesMax(series)) * 150)}px` }" :class="{ incomplete: point.result.incomplete, empty: point.result.value === null }" />
                    <span class="bar-label">{{ point.label }}</span>
                  </button>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="energy">
        <EnergyBalanceCard :meters="meters" />
      </v-window-item>

      <v-window-item value="settings">
        <v-card max-width="760"><v-card-title>Verbrauchseinstellungen</v-card-title><v-card-text v-if="settings"><v-text-field v-model.number="settings.reminder_days" type="number" label="Ablesung nach Tagen als fällig markieren" /><v-text-field v-model.number="settings.plausibility_threshold_percent" type="number" label="Plausibilitätswarnung ab Prozent des Vergleichsverbrauchs" /><v-btn color="primary" @click="saveSettings">Speichern</v-btn></v-card-text></v-card>
      </v-window-item>
    </v-window>

    <v-dialog v-model="meterDialog" max-width="900">
      <v-card>
        <v-card-title>{{ editingMeter ? 'Zähler bearbeiten' : 'Zähler anlegen' }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="8"><v-text-field v-model="meterForm.name" label="Name" /></v-col>
            <v-col cols="12" md="4"><v-select v-model="meterForm.meter_type" :items="meterTypeItems" label="Art" @update:model-value="applyTypeDefaults" /></v-col>
            <v-col cols="6" md="3"><v-text-field v-model="meterForm.unit" label="Einheit" /></v-col>
            <v-col cols="6" md="3"><v-text-field v-model.number="meterForm.decimals" type="number" label="Nachkommastellen" /></v-col>
            <v-col cols="12" md="6"><v-text-field v-model="meterForm.serial_number" label="Zählernummer" clearable /></v-col>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="meterForm.asset_id" :items="assetItems" label="Asset (optional)" clearable @update:model-value="selectMeterAsset" />
            </v-col>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="meterForm.location_id" :items="locationItems" label="Ort (optional)" clearable>
                <template #item="{ props, item }"><v-list-item v-bind="props" :style="{ paddingInlineStart: `${16 + item.raw.depth * 18}px` }" /></template>
              </v-autocomplete>
            </v-col>
            <v-col cols="12"><v-checkbox v-model="meterForm.primary_for_dashboard" :label="meterForm.meter_type === 'electricity_pv' ? 'PV-Zähler auf dem Dashboard berücksichtigen' : 'Primärzähler für den Dashboard-Vergleich'" /></v-col>
            <v-col v-if="meterForm.meter_type === 'water'" cols="12"><v-select v-model="meterForm.water_role" :items="waterRoleItems" label="Wasser-Auswertung" /></v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="meterForm.reading_schedule_day"
                :disabled="meterForm.reading_schedule_last_day"
                type="number"
                min="1"
                max="31"
                label="Monatlicher Ablesetag"
                clearable
              />
            </v-col>
            <v-col cols="12" sm="6"><v-checkbox v-model="meterForm.reading_schedule_last_day" label="Am letzten Monatstag" /></v-col>
            <v-col cols="12">
              <v-select
                v-model="meterForm.reminder_days"
                :items="Array.from({ length: 31 }, (_, index) => ({ value: index + 1, title: `${index + 1}. Kalendertag` }))"
                multiple
                chips
                clearable
                label="Weitere Erinnerungstage im Monat"
              />
            </v-col>
            <v-col cols="12"><v-divider class="mb-4" /><div class="text-subtitle-1 font-weight-bold mb-2">Home Assistant</div></v-col>
            <v-col cols="12">
              <v-autocomplete v-model="meterForm.home_assistant_entity_id" :items="entityItems" label="Kumulativer Zählerstand" hint="Wird für automatische Ablesungen übernommen, z. B. kWh." persistent-hint clearable />
            </v-col>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="meterForm.home_assistant_power_entity_id" :items="entityItems" label="Aktuelle Gesamtleistung" hint="Livewert in W oder kW." persistent-hint clearable />
            </v-col>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="meterForm.home_assistant_voltage_entity_id" :items="entityItems" label="Aktuelle Spannung" hint="Livewert in V." persistent-hint clearable />
            </v-col>
            <v-col cols="12"><v-textarea v-model="meterForm.notes" label="Notizen" rows="3" clearable /></v-col>
          </v-row>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="meterDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveMeter">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="readingDialog" :fullscreen="smAndDown" max-width="680">
      <v-card>
        <v-toolbar v-if="smAndDown" color="surface">
          <v-btn icon="mdi-close" aria-label="Abbrechen" @click="readingDialog = false" />
          <v-toolbar-title>{{ editingReading ? 'Ablesung bearbeiten' : 'Ablesung erfassen' }}</v-toolbar-title>
        </v-toolbar>
        <v-card-title v-else>{{ editingReading ? 'Ablesung bearbeiten' : 'Ablesung erfassen' }}</v-card-title>
        <v-card-text>
          <v-select v-model="readingForm.meter_id" :items="meters.map(m => ({ value: m.id, title: m.name }))" label="Zähler" />
          <v-text-field
            v-model.number="readingForm.value"
            type="number"
            inputmode="decimal"
            :step="10 ** -(selectedReadingMeter?.decimals ?? 2)"
            :suffix="selectedReadingMeter?.unit"
            label="Zählerstand"
            class="reading-value"
            autofocus
          />
          <v-alert v-if="selectedReadingMeter" type="info" variant="tonal" density="compact" class="mb-3">
            <div v-if="selectedReadingMeter.latest_value !== null">
              Letzter Wert: <strong>{{ formatValue(selectedReadingMeter.latest_value, selectedReadingMeter.decimals, selectedReadingMeter.unit) }}</strong>
              · {{ formatDate(selectedReadingMeter.latest_measured_at) }}
            </div>
            <div v-else>Noch keine vorherige Ablesung vorhanden.</div>
            <div v-if="selectedReadingObis" class="mt-1">{{ selectedReadingObis }}</div>
          </v-alert>
          <v-text-field v-model="readingForm.measured_at" type="datetime-local" label="Zeitpunkt" />
          <v-textarea v-model="readingForm.note" label="Notiz" rows="3" clearable />
          <ImmichReadingPicker
            v-model:asset-id="readingForm.immich_asset_id"
            v-model:file-name="readingForm.immich_original_file_name"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="readingDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" size="large" :loading="saving" :disabled="saving || !readingForm.meter_id" @click="saveReading">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="replacementDialog" :fullscreen="smAndDown" max-width="680">
      <v-card title="Zähler austauschen" prepend-icon="mdi-swap-horizontal">
        <v-card-text v-if="replacementMeter">
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            {{ replacementMeter.name }} · bisherige Zählernummer:
            {{ replacementMeter.serial_number || 'nicht dokumentiert' }}
          </v-alert>
          <v-text-field v-model="replacementForm.replaced_at" type="datetime-local" label="Datum und Zeitpunkt des Austauschs" />
          <v-text-field v-model.number="replacementForm.old_final_value" type="number" inputmode="decimal" :suffix="replacementMeter.unit" label="Letzter Stand des alten Zählers" />
          <v-text-field v-model="replacementForm.new_serial_number" label="Neue Zählernummer" />
          <v-text-field v-model.number="replacementForm.new_start_value" type="number" inputmode="decimal" :suffix="replacementMeter.unit" label="Startstand des neuen Zählers" />
          <v-textarea v-model="replacementForm.note" label="Notiz / Dokumentation (optional)" rows="3" clearable />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="replacementDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!replacementForm.new_serial_number.trim()" @click="saveReplacement">Austausch speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="chartDialog" fullscreen>
      <v-card>
        <v-toolbar color="surface"><v-btn icon="mdi-close" aria-label="Vollbild schließen" @click="chartDialog = false" /><v-toolbar-title>{{ enlargedSeries?.name }}</v-toolbar-title></v-toolbar>
        <v-card-text v-if="enlargedSeries" class="d-flex align-center">
          <div class="chart-scroll w-100">
            <div class="bar-chart enlarged">
              <button v-for="point in enlargedSeries.points" :key="point.period_start" type="button" class="bar-column" :aria-label="`${point.label}: ${formatValue(point.result.value, enlargedSeries.decimals, enlargedSeries.unit)}`" @click="selectChartPoint(enlargedSeries, point)">
                <span class="bar-value">{{ formatValue(point.result.value, enlargedSeries.decimals, enlargedSeries.unit) }}</span>
                <span class="bar" :style="{ height: point.result.value === null ? '0' : `${Math.max(3, (point.result.value / consumptionSeriesMax(enlargedSeries)) * 300)}px` }" :class="{ incomplete: point.result.incomplete }" />
                <span class="bar-label">{{ point.label }}</span>
              </button>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="importDialog" max-width="760"><v-card><v-card-title>Verbrauchsdaten importieren</v-card-title><v-card-text><v-alert type="info" variant="tonal" class="mb-4">Unterstützt werden die alte <code>verbrauch.sqlite</code> sowie CSV-Dateien. Zugangsdaten aus Altdaten werden nicht übernommen.</v-alert><v-file-input label="SQLite- oder CSV-Datei" accept=".sqlite,.db,.csv,text/csv,application/x-sqlite3" @update:model-value="pickImportFile" /><v-checkbox v-model="createMissingMeters" label="Fehlende Zähler automatisch anlegen" /><v-checkbox v-model="overwriteImport" label="Vorhandene Ablesungen mit gleichem Zeitpunkt überschreiben" /><div class="d-flex ga-2 mb-4"><v-btn :disabled="!importFile" :loading="saving" @click="previewImport">Vorschau</v-btn><v-btn color="primary" :disabled="!importPreview" :loading="saving" @click="executeImport">Importieren</v-btn></div><v-sheet v-if="importPreview" border rounded class="pa-4 mb-4"><strong>Vorschau: {{ importPreview.format }}</strong><div>{{ importPreview.meter_count }} Zähler · {{ importPreview.reading_count }} Ablesungen · {{ importPreview.note_count }} Notizen</div><v-alert v-for="warning in importPreview.warnings" :key="warning" type="warning" density="compact" class="mt-2">{{ warning }}</v-alert></v-sheet><v-sheet v-if="importResult" border rounded class="pa-4"><strong>Importergebnis</strong><div>{{ importResult.meters_created }} Zähler und {{ importResult.readings_created }} Ablesungen angelegt.</div><div>{{ importResult.duplicates_skipped }} Duplikate übersprungen, {{ importResult.rows_skipped }} Zeilen ausgelassen.</div><v-alert v-for="item in importResult.errors" :key="item" type="warning" density="compact" class="mt-2">{{ item }}</v-alert></v-sheet></v-card-text><v-card-actions><v-spacer /><v-btn @click="importDialog = false">Schließen</v-btn></v-card-actions></v-card></v-dialog>
  </v-container>
</template>

<style scoped>
.chart-scroll { overflow-x: auto; overscroll-behavior-x: contain; touch-action: pan-x; -webkit-overflow-scrolling: touch; }
.bar-chart { min-width: 680px; height: 205px; display: flex; align-items: flex-end; gap: 10px; padding: 8px 4px; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.bar-column { width: 58px; min-width: 58px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; border: 0; background: transparent; color: inherit; cursor: pointer; }
.bar-column:focus-visible { outline: 3px solid rgb(var(--v-theme-primary)); outline-offset: 3px; border-radius: 4px; }
.bar { width: 34px; background: rgb(var(--v-theme-primary)); border-radius: 5px 5px 0 0; }
.bar.incomplete { opacity: .45; }
.bar.empty { min-height: 0; background: transparent; }
.bar-chart.enlarged { min-width: 900px; height: 380px; }
.bar-label, .bar-value { font-size: .72rem; text-align: center; white-space: nowrap; }
.bar-value { margin-bottom: 4px; }
.bar-label { margin-top: 5px; color: rgba(var(--v-theme-on-surface), .7); }
.reading-value :deep(input) { font-size: 1.7rem; font-weight: 700; }
@media (max-width: 600px) {
  .bar-chart { min-width: max-content; }
  .bar-column { width: 66px; min-width: 66px; }
}
</style>

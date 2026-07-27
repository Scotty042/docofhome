<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import ElectricalWiringSummary from '../components/ElectricalWiringSummary.vue'
import { assetApi } from '../services/assetApi'
import { consumptionApi } from '../services/consumptionApi'
import { electricalApi } from '../services/electricalApi'
import { useNotificationStore } from '../stores/notifications'
import {
  assetCabinetClass,
  busbarPhasePattern,
  cabinetComponentClass,
  groupProtectiveDevices,
  moduleBoardStyle,
  moduleNumbers,
  modulePlacements,
  protectiveDeviceCabinetClass,
  protectiveDeviceLabels,
  isElectricalConsumptionMeterType,
  isNonElectricalMeterAssetType
} from '../services/electricalPresentation'
import type { Asset } from '../types/assets'
import type { ConsumptionMeter } from '../types/consumption'
import type {
  DistributionArea,
  DistributionAreaType,
  DistributionAreaWrite,
  DistributionDetail,
  DistributionSection,
  DistributionSectionWrite,
  ElectricalAssetPlacement,
  ElectricalAssetPlacementWrite,
  ElectricalCabinetComponent,
  ElectricalCabinetComponentType,
  ElectricalCabinetComponentWrite,
  ElectricalPhase,
  ElectricalMeterPlacement,
  ElectricalTopology,
  ProtectiveDevice,
  ProtectiveDevicePlacementWrite
} from '../types/electrical'

const route = useRoute()
const notifications = useNotificationStore()
const distributionId = computed(() => String(route.params.id ?? ''))
const distribution = ref<DistributionDetail | null>(null)
const structuredLayout = computed(() => distribution.value?.layout_mode === 'sections')
const simpleDeviceGroups = computed(() => {
  const groups = groupProtectiveDevices(
    distribution.value?.protective_devices ?? [],
    distribution.value?.rows ?? null
  )
  const knownRows = new Set(groups.map((group) => group.row))
  const occupiedRows = [
    ...cabinetComponents.value
      .filter((component) => component.area_id === null)
      .map((component) => component.row_number),
    ...assetPlacements.value
      .filter((placement) => placement.area_id === null)
      .map((placement) => placement.row_number)
  ]
  for (const row of occupiedRows) {
    if (!knownRows.has(row)) {
      groups.push({ row, devices: [] })
      knownRows.add(row)
    }
  }
  return groups.sort((left, right) => (
    (left.row ?? Number.MAX_SAFE_INTEGER) - (right.row ?? Number.MAX_SAFE_INTEGER)
  ))
})
const simpleModuleLabels = computed(() => (
  distribution.value?.modules_per_row
    ? moduleNumbers(distribution.value.modules_per_row)
    : []
))
const simpleLayoutConfigured = computed(() => Boolean(
  distribution.value?.rows
  || distribution.value?.modules_per_row
  || distribution.value?.protective_devices.length
  || cabinetComponents.value.length
  || assetPlacements.value.length
))
function protectiveDeviceWidth(device: ProtectiveDevice): number | null {
  return device.module_width ?? device.asset.effective_module_width
}

function devicesWithoutModulePlacement(devices: ProtectiveDevice[]): ProtectiveDevice[] {
  return devices.filter((device) => device.start_position === null || device.module_width === null)
}
const sections = ref<DistributionSection[]>([])
const topology = ref<ElectricalTopology>({ nodes: [], connections: [], measurement_points: [] })
const meterPlacements = ref<ElectricalMeterPlacement[]>([])
const assetPlacements = ref<ElectricalAssetPlacement[]>([])
const cabinetComponents = ref<ElectricalCabinetComponent[]>([])
const consumptionMeters = ref<ConsumptionMeter[]>([])
const assets = ref<Asset[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const topologyError = ref<string | null>(null)
const success = ref<string | null>(null)

watch(error, (message) => {
  if (message) notifications.error(message)
})
watch(success, (message) => {
  if (message) notifications.success(message)
})
watch(topologyError, (message) => {
  if (message) notifications.warning(message)
})
const desktopDragEnabled = ref(false)
const draggedDeviceId = ref<string | null>(null)
const draggedAsset = ref<{ assetId: string; moduleWidth: number; name: string } | null>(null)
const activeDropTarget = ref<string | null>(null)
let dragMediaQuery: MediaQueryList | null = null

const sectionDialog = ref(false)
const editingSectionId = ref<string | null>(null)
const sectionForm = ref<DistributionSectionWrite>({ name: '', position: 1, description: null })

const areaDialog = ref(false)
const editingAreaId = ref<string | null>(null)
const targetSectionId = ref<string | null>(null)
const areaForm = ref<DistributionAreaWrite>({
  name: '', area_type: 'device_rows', position: 1, rows: null, modules_per_row: null, width: 'full', side: null, description: null
})

const placementDialog = ref(false)
const placementDeviceId = ref<string | null>(null)
const placementForm = ref<ProtectiveDevicePlacementWrite>({
  area_id: null, row_number: null, start_position: null, module_width: null,
  assigned_rcd_id: null, neutral_rail_id: null
})

watch(placementDeviceId, (deviceId) => {
  const device = deviceId ? findDevice(deviceId) : undefined
  placementForm.value.module_width = device ? protectiveDeviceWidth(device) : null
  placementForm.value.assigned_rcd_id = device?.assigned_rcd_id ?? null
  placementForm.value.neutral_rail_id = device?.neutral_rail_id ?? null
})

const meterPlacementDialog = ref(false)
const meterPlacementSourceKey = ref<string | null>(null)
const meterPlacementAreaId = ref<string | null>(null)
const meterPlacementPosition = ref(1)

const assetPlacementDialog = ref(false)
const assetPlacementAssetId = ref<string | null>(null)
const assetPlacementForm = ref<ElectricalAssetPlacementWrite>({
  area_id: null, row_number: 1, start_position: 1, module_width: null
})

const cabinetComponentDialog = ref(false)
const editingCabinetComponentId = ref<string | null>(null)
const cabinetComponentForm = ref<ElectricalCabinetComponentWrite>({
  name: '',
  component_type: 'phase_distribution_block',
  area_id: null,
  row_number: 1,
  start_position: 1,
  module_width: 4,
  phases: ['L1', 'L2', 'L3'],
  rated_current_a: null,
  max_cross_section_mm2: null,
  outgoing_connections: null,
  linked_rcd_device_id: null,
  start_phase: 'L1',
  description: null,
  notes: null
})

const cabinetComponentTypeOptions: Array<{
  title: string
  value: ElectricalCabinetComponentType
  icon: string
}> = [
  { title: 'Phasenverteilerblock', value: 'phase_distribution_block', icon: 'mdi-call-split' },
  { title: 'Sammelschiene', value: 'busbar', icon: 'mdi-view-stream-outline' },
  { title: 'Phasenschiene', value: 'phase_rail', icon: 'mdi-transit-connection-horizontal' },
  { title: 'N-Schiene', value: 'neutral_rail', icon: 'mdi-minus-box-outline' },
  { title: 'PE-Schiene', value: 'protective_earth_rail', icon: 'mdi-earth' },
  { title: 'Reihenklemme', value: 'terminal_block', icon: 'mdi-connection' },
  { title: 'Anschlussblock', value: 'connection_block', icon: 'mdi-power-plug-outline' },
  { title: 'Potentialverteiler', value: 'potential_distribution', icon: 'mdi-source-branch' },
  { title: 'Sonstige passive Komponente', value: 'other', icon: 'mdi-view-grid-plus-outline' }
]
const cabinetComponentTypeMeta = Object.fromEntries(
  cabinetComponentTypeOptions.map((item) => [item.value, item])
) as Record<ElectricalCabinetComponentType, {
  title: string
  value: ElectricalCabinetComponentType
  icon: string
}>
const phaseOptions: Array<{ title: string; value: ElectricalPhase }> = [
  { title: 'L1', value: 'L1' },
  { title: 'L2', value: 'L2' },
  { title: 'L3', value: 'L3' },
  { title: 'N', value: 'N' },
  { title: 'PE', value: 'PE' }
]

const viewMode = ref<'compact' | 'expanded'>('compact')
const detailDrawer = ref(false)
const detailDevice = ref<ProtectiveDevice | null>(null)
const detailComponent = ref<ElectricalCabinetComponent | null>(null)
const detailAsset = ref<ElectricalAssetPlacement | null>(null)

const rcdOptions = computed(() => (distribution.value?.protective_devices ?? [])
  .filter((device) => device.device_type === 'rcd')
  .map((device) => ({
    id: device.id,
    title: `${device.asset.name} · ${device.asset.jarvis_code}`
  }))
  .sort((left, right) => left.title.localeCompare(right.title, 'de')))

const neutralRailOptions = computed(() => cabinetComponents.value
  .filter((component) => component.component_type === 'neutral_rail')
  .map((component) => ({
    id: component.id,
    title: component.linked_rcd_name
      ? `${component.name} · ${component.linked_rcd_name}`
      : component.name
  }))
  .sort((left, right) => left.title.localeCompare(right.title, 'de')))

const areaTypeOptions: Array<{ title: string; value: DistributionAreaType; icon: string }> = [
  { title: 'Geräte- und Reihenbereich', value: 'device_rows', icon: 'mdi-view-sequential-outline' },
  { title: 'Zählerfeld', value: 'meter', icon: 'mdi-meter-electric-outline' },
  { title: 'Anschlussfeld', value: 'connection', icon: 'mdi-connection' },
  { title: 'N-Schiene', value: 'neutral_rail', icon: 'mdi-minus-box-outline' },
  { title: 'PE-Schiene', value: 'protective_earth_rail', icon: 'mdi-earth' },
  { title: 'Technikbereich', value: 'technology', icon: 'mdi-memory' },
  { title: 'Reserve', value: 'reserve', icon: 'mdi-package-variant-closed' },
  { title: 'Abdeckung / Blindfeld', value: 'cover', icon: 'mdi-view-dashboard-outline' }
]

const areaTypeMeta = Object.fromEntries(
  areaTypeOptions.map((item) => [item.value, item])
) as Record<DistributionAreaType, { title: string; value: DistributionAreaType; icon: string }>

function suggestAreaSide() {
  if (areaForm.value.width !== 'half' || !targetSectionId.value) {
    areaForm.value.side = null
    return
  }
  const peers = sections.value.find((section) => section.id === targetSectionId.value)?.areas
    .filter((area) => area.id !== editingAreaId.value && area.position === areaForm.value.position) ?? []
  if (peers.some((area) => area.width === 'half' && area.side === 'left')) areaForm.value.side = 'right'
  else areaForm.value.side = 'left'
}

watch(
  () => [areaForm.value.width, areaForm.value.position, targetSectionId.value],
  suggestAreaSide
)

const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const positiveRule = (value: number | null) => value === null || value >= 1 || 'Wert muss mindestens 1 sein.'
const deviceOptions = computed(() => (distribution.value?.protective_devices ?? []).map((device) => ({
  id: device.id,
  title: `${device.asset.name} · ${device.asset.jarvis_code}`
})))
const deviceAreaOptions = computed(() => sections.value.flatMap((section) => section.areas
  .filter((area) => area.area_type === 'device_rows')
  .map((area) => ({ id: area.id, title: `${section.name} · ${area.name}` }))))
const placedAssetIds = computed(() => new Set(assetPlacements.value.map((placement) => placement.asset_id)))
const protectiveAssetIds = computed(() => new Set((distribution.value?.protective_devices ?? []).map((device) => device.asset_id)))
const nonElectricalMeterAssetIds = computed(() => new Set(
  consumptionMeters.value
    .filter((meter) => !isElectricalConsumptionMeterType(meter.meter_type))
    .map((meter) => meter.asset_id)
    .filter((id): id is string => Boolean(id))
))
const dinAssetOptions = computed(() => assets.value
  .filter((asset) => (
    asset.status === 'active' && Boolean(asset.effective_module_width)
      && !placedAssetIds.value.has(asset.id) && !protectiveAssetIds.value.has(asset.id)
      && !nonElectricalMeterAssetIds.value.has(asset.id)
      && !isNonElectricalMeterAssetType(asset.asset_type.name)
  ))
  .map((asset) => ({
    id: asset.id,
    title: `${asset.name} · ${asset.jarvis_code}`,
    moduleWidth: asset.effective_module_width
  }))
  .sort((left, right) => left.title.localeCompare(right.title, 'de')))
const assetPlacementOptions = computed(() => {
  const options = [...dinAssetOptions.value]
  const selectedId = assetPlacementAssetId.value
  if (selectedId && !options.some((item) => item.id === selectedId)) {
    const asset = assets.value.find((item) => item.id === selectedId)
    if (asset) {
      options.push({
        id: asset.id,
        title: `${asset.name} · ${asset.jarvis_code}`,
        moduleWidth: asset.effective_module_width
      })
    }
  }
  return options.sort((left, right) => left.title.localeCompare(right.title, 'de'))
})
const unassignedDevices = computed(() => (
  distribution.value?.protective_devices.filter((device) => (
    structuredLayout.value
      ? !device.area_id
      : device.row_number === null
        && device.start_position === null
        && device.module_width === null
  )) ?? []
))

const layoutCapacity = computed(() => {
  if (!distribution.value) return 0
  if (!structuredLayout.value) {
    return (distribution.value.rows ?? 0) * (distribution.value.modules_per_row ?? 0)
  }
  return sections.value.flatMap((section) => section.areas)
    .filter((area) => area.area_type === 'device_rows')
    .reduce((sum, area) => sum + (area.rows ?? 0) * (area.modules_per_row ?? 0), 0)
})

const occupiedModuleCount = computed(() => {
  const occupied = new Set<string>()
  const add = (areaId: string | null, row: number, start: number, width: number) => {
    for (let offset = 0; offset < width; offset += 1) {
      occupied.add(`${areaId ?? 'simple'}:${row}:${start + offset}`)
    }
  }
  for (const device of distribution.value?.protective_devices ?? []) {
    if (device.row_number && device.start_position && device.module_width) {
      add(device.area_id, device.row_number, device.start_position, device.module_width)
    }
  }
  for (const placement of assetPlacements.value) {
    add(placement.area_id, placement.row_number, placement.start_position, placement.module_width)
  }
  for (const component of cabinetComponents.value) {
    if (component.component_type !== 'busbar') {
      add(component.area_id, component.row_number, component.start_position, component.module_width)
    }
  }
  return occupied.size
})

const layoutWarnings = computed(() => {
  const messages = new Set<string>()
  for (const device of distribution.value?.protective_devices ?? []) {
    device.group_warnings.forEach((message) => messages.add(`${device.asset.name}: ${message}`))
  }
  for (const component of cabinetComponents.value) {
    if (component.component_type === 'busbar' && !component.linked_rcd_device_id) {
      messages.add(`${component.name}: noch keinem FI/RCD zugeordnet.`)
    }
    if (component.component_type === 'neutral_rail' && !component.linked_rcd_device_id) {
      messages.add(`${component.name}: noch keinem FI/RCD zugeordnet.`)
    }
  }
  return [...messages]
})

const freeModuleCount = computed(() => Math.max(0, layoutCapacity.value - occupiedModuleCount.value))
const unplacedCount = computed(() => unassignedDevices.value.length + dinAssetOptions.value.length)
const meterAreaOptions = computed(() => sections.value.flatMap((section) => section.areas
  .filter((area) => area.area_type === 'meter')
  .map((area) => ({ id: area.id, title: `${section.name} · ${area.name}` }))))
type MeterPlacementCandidate = {
  value: string
  sourceKind: 'consumption_meter' | 'asset'
  sourceId: string
  title: string
  subtitle: string
}

const meterOptions = computed<MeterPlacementCandidate[]>(() => {
  const linkedAssetIds = new Set(
    consumptionMeters.value
      .map((meter) => meter.asset_id)
      .filter((id): id is string => Boolean(id))
  )
  const meterCandidates = consumptionMeters.value
    .filter((meter) => isElectricalConsumptionMeterType(meter.meter_type))
    .map((meter) => ({
    value: `meter:${meter.id}`,
    sourceKind: 'consumption_meter' as const,
    sourceId: meter.id,
    title: meter.name,
    subtitle: [meter.asset_name, meter.serial_number, meter.location_path, meter.unit]
      .filter(Boolean)
      .join(' · ')
  }))
  const assetCandidates = assets.value
    .filter((asset) => (
      asset.status === 'active'
      && (() => {
        const typeName = asset.asset_type.name.trim().toLocaleLowerCase('de')
        return typeName.includes('stromzähler')
          || typeName.includes('stromzaehler')
          || typeName.includes('smart meter')
          || typeName.includes('smartmeter')
      })()
      && !linkedAssetIds.has(asset.id)
    ))
    .map((asset) => ({
      value: `asset:${asset.id}`,
      sourceKind: 'asset' as const,
      sourceId: asset.id,
      title: asset.name,
      subtitle: [asset.jarvis_code, asset.serial_number, asset.location?.name]
        .filter(Boolean)
        .join(' · ')
    }))
  return [...meterCandidates, ...assetCandidates].sort((left, right) => (
    left.title.localeCompare(right.title, 'de', { sensitivity: 'base', numeric: true })
  ))
})
const unassignedMeterCandidates = computed(() => {
  const assigned = new Set(meterPlacements.value.map(placementSourceKey))
  return meterOptions.value.filter((candidate) => !assigned.has(candidate.value))
})
function placementSourceKey(placement: ElectricalMeterPlacement): string {
  return placement.source_kind === 'asset'
    ? `asset:${placement.asset_id}`
    : `meter:${placement.meter_id}`
}

function metersForArea(areaId: string) {
  return meterPlacements.value
    .filter((item) => item.area_id === areaId)
    .sort((left, right) => left.position - right.position || left.meter_name.localeCompare(right.meter_name, 'de'))
}

function updateDragAvailability() {
  desktopDragEnabled.value = dragMediaQuery?.matches ?? false
}

onMounted(() => {
  dragMediaQuery = window.matchMedia('(min-width: 960px)')
  updateDragAvailability()
  dragMediaQuery.addEventListener('change', updateDragAvailability)
  void load()
})

onBeforeUnmount(() => {
  dragMediaQuery?.removeEventListener('change', updateDragAvailability)
})

async function load() {
  loading.value = true
  error.value = null
  topologyError.value = null
  try {
    const detail = await electricalApi.getDistribution(distributionId.value)
    distribution.value = detail

    const common = await Promise.all([
      electricalApi.topology().catch((reason) => {
        topologyError.value = reason instanceof Error
          ? reason.message
          : 'Versorgungsinformationen konnten nicht geladen werden.'
        return { nodes: [], connections: [], measurement_points: [] } satisfies ElectricalTopology
      }),
      electricalApi.cabinetComponents(distributionId.value),
      electricalApi.assetPlacements(distributionId.value),
      assetApi.allAssets()
    ])
    topology.value = common[0]
    cabinetComponents.value = common[1]
    assetPlacements.value = common[2]
    assets.value = common[3]

    if (detail.layout_mode !== 'sections') {
      sections.value = []
      meterPlacements.value = []
      consumptionMeters.value = []
      return
    }

    const [layout, placements, meterData] = await Promise.all([
      electricalApi.getLayout(distributionId.value),
      electricalApi.meterPlacements(distributionId.value),
      consumptionApi.meters()
    ])
    sections.value = layout
    meterPlacements.value = placements
    consumptionMeters.value = meterData
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Schrankaufteilung konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function optionalText(value: string | null): string | null {
  return value?.trim() || null
}

function optionalNumber(value: number | null): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function openSection(section?: DistributionSection) {
  editingSectionId.value = section?.id ?? null
  sectionForm.value = section
    ? { name: section.name, position: section.position, description: section.description }
    : { name: '', position: sections.value.length + 1, description: null }
  sectionDialog.value = true
}

async function saveSection() {
  saving.value = true
  error.value = null
  try {
    const payload: DistributionSectionWrite = {
      ...sectionForm.value,
      name: sectionForm.value.name.trim(),
      description: optionalText(sectionForm.value.description)
    }
    if (editingSectionId.value) {
      await electricalApi.updateSection(distributionId.value, editingSectionId.value, payload)
    } else {
      await electricalApi.createSection(distributionId.value, payload)
    }
    sectionDialog.value = false
    success.value = 'Feld wurde gespeichert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Feld konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archiveSection(section: DistributionSection) {
  if (!window.confirm(`Feld „${section.name}“ archivieren?`)) return
  try {
    await electricalApi.removeSection(distributionId.value, section.id)
    success.value = 'Feld wurde archiviert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Feld konnte nicht archiviert werden.'
  }
}

function openArea(sectionId: string, area?: DistributionArea) {
  targetSectionId.value = sectionId
  editingAreaId.value = area?.id ?? null
  areaForm.value = area
    ? {
        name: area.name,
        area_type: area.area_type,
        position: area.position,
        rows: area.rows,
        modules_per_row: area.modules_per_row,
        width: area.width,
        side: area.side,
        description: area.description
      }
    : {
        name: '', area_type: 'device_rows',
        position: (sections.value.find((section) => section.id === sectionId)?.areas.length ?? 0) + 1,
        rows: null, modules_per_row: null, width: 'full', side: null, description: null
      }
  areaDialog.value = true
}

async function saveArea() {
  if (!targetSectionId.value) return
  saving.value = true
  error.value = null
  try {
    const deviceRows = areaForm.value.area_type === 'device_rows'
    const payload: DistributionAreaWrite = {
      ...areaForm.value,
      name: areaForm.value.name.trim(),
      rows: deviceRows ? optionalNumber(areaForm.value.rows) : null,
      modules_per_row: deviceRows ? optionalNumber(areaForm.value.modules_per_row) : null,
      side: areaForm.value.width === 'half' ? areaForm.value.side : null,
      description: optionalText(areaForm.value.description)
    }
    if (editingAreaId.value) {
      await electricalApi.updateArea(distributionId.value, editingAreaId.value, payload)
    } else {
      await electricalApi.createArea(distributionId.value, targetSectionId.value, payload)
    }
    areaDialog.value = false
    success.value = 'Bereich wurde gespeichert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bereich konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function openMeterPlacement(
  candidate?: MeterPlacementCandidate,
  area?: DistributionArea,
  placement?: ElectricalMeterPlacement
) {
  const sourceKey = candidate?.value ?? (placement ? placementSourceKey(placement) : null)
  const existing = sourceKey
    ? meterPlacements.value.find((item) => placementSourceKey(item) === sourceKey)
    : null
  meterPlacementSourceKey.value = sourceKey
  meterPlacementAreaId.value = area?.id ?? existing?.area_id ?? meterAreaOptions.value[0]?.id ?? null
  meterPlacementPosition.value = existing?.position ?? (
    meterPlacementAreaId.value ? metersForArea(meterPlacementAreaId.value).length + 1 : 1
  )
  meterPlacementDialog.value = true
}

async function saveMeterPlacement() {
  if (!meterPlacementSourceKey.value || !meterPlacementAreaId.value) return
  saving.value = true
  error.value = null
  try {
    const [kind, sourceId = ''] = meterPlacementSourceKey.value.split(':', 2)
    if (!sourceId) throw new Error('Ungültige Zählerauswahl.')
    const payload = {
      area_id: meterPlacementAreaId.value,
      position: meterPlacementPosition.value
    }
    if (kind === 'asset') {
      await electricalApi.placeMeterAsset(distributionId.value, sourceId, payload)
    } else {
      await electricalApi.placeMeter(distributionId.value, sourceId, payload)
    }
    meterPlacementDialog.value = false
    success.value = 'Zähler wurde im Zählerfeld platziert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zähler konnte nicht platziert werden.'
  } finally {
    saving.value = false
  }
}

async function unplaceMeterPlacement(placement: ElectricalMeterPlacement) {
  try {
    if (placement.source_kind === 'asset' && placement.asset_id) {
      await electricalApi.unplaceMeterAsset(distributionId.value, placement.asset_id)
    } else if (placement.meter_id) {
      await electricalApi.unplaceMeter(distributionId.value, placement.meter_id)
    }
    success.value = 'Zähler wurde aus dem Schrankplan entfernt.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zählerplatzierung konnte nicht entfernt werden.'
  }
}

function formatMeterValue(value: number | null, unit: string) {
  return value === null ? 'Noch keine Ablesung' : `${new Intl.NumberFormat('de-DE', { maximumFractionDigits: 3 }).format(value)} ${unit}`
}

function openDeviceDetails(device: ProtectiveDevice) {
  detailDevice.value = device
  detailComponent.value = null
  detailAsset.value = null
  detailDrawer.value = true
}

function openComponentDetails(component: ElectricalCabinetComponent) {
  detailDevice.value = null
  detailComponent.value = component
  detailAsset.value = null
  detailDrawer.value = true
}

function openAssetDetails(placement: ElectricalAssetPlacement) {
  detailDevice.value = null
  detailComponent.value = null
  detailAsset.value = placement
  detailDrawer.value = true
}

function devicePhaseText(device: ProtectiveDevice): string {
  return device.calculated_phases.length ? device.calculated_phases.join(' / ') : 'Phase nicht ermittelt'
}

function componentGridStyle(component: ElectricalCabinetComponent) {
  return {
    gridColumn: `${component.start_position} / span ${component.module_width}`,
    gridRow: component.component_type === 'busbar' ? '3' : '2'
  }
}


function assetPlacementsForArea(areaId: string) {
  return assetPlacements.value
    .filter((placement) => placement.area_id === areaId)
    .sort((left, right) => left.row_number - right.row_number || left.start_position - right.start_position)
}

function openAssetPlacement(
  area?: DistributionArea,
  placement?: ElectricalAssetPlacement,
  assetId?: string
) {
  assetPlacementAssetId.value = placement?.asset_id ?? assetId ?? null
  const selectedAsset = placement
    ? null
    : dinAssetOptions.value.find((item) => item.id === assetPlacementAssetId.value)
  assetPlacementForm.value = {
    area_id: structuredLayout.value
      ? area?.id ?? placement?.area_id ?? deviceAreaOptions.value[0]?.id ?? null
      : null,
    row_number: placement?.row_number ?? 1,
    start_position: placement?.start_position ?? 1,
    module_width: placement?.module_width ?? selectedAsset?.moduleWidth ?? null
  }
  assetPlacementDialog.value = true
}

function applySelectedAssetWidth() {
  const selected = assetPlacementOptions.value.find((item) => item.id === assetPlacementAssetId.value)
  if (selected?.moduleWidth) assetPlacementForm.value.module_width = selected.moduleWidth
}

async function saveAssetPlacement() {
  if (
    !assetPlacementAssetId.value
    || (structuredLayout.value && !assetPlacementForm.value.area_id)
  ) {
    error.value = structuredLayout.value
      ? 'Bitte DIN-Asset und Gerätebereich auswählen.'
      : 'Bitte ein DIN-Asset auswählen.'
    return
  }
  saving.value = true
  error.value = null
  try {
    await electricalApi.placeAsset(distributionId.value, assetPlacementAssetId.value, assetPlacementForm.value)
    assetPlacementDialog.value = false
    success.value = 'DIN-Hutschienengerät wurde platziert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'DIN-Hutschienengerät konnte nicht platziert werden.'
  } finally {
    saving.value = false
  }
}

async function unplaceAsset(placement: ElectricalAssetPlacement) {
  try {
    await electricalApi.unplaceAsset(distributionId.value, placement.asset_id)
    success.value = 'DIN-Hutschienengerät wurde aus dem Plan entfernt.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Platzierung konnte nicht entfernt werden.'
  }
}

function liveValueText(placement: ElectricalAssetPlacement) {
  const value = placement.primary_live_value
  if (!value) return placement.live_warning || 'Kein Livewert zugeordnet'
  return value.available
    ? `${value.state}${value.unit ? ` ${value.unit}` : ''}`
    : `Nicht verfügbar${value.state ? ` · zuletzt ${value.state}${value.unit ? ` ${value.unit}` : ''}` : ''}`
}

function cabinetComponentsForArea(areaId: string) {
  return cabinetComponents.value
    .filter((component) => component.area_id === areaId)
    .sort((left, right) => left.row_number - right.row_number || left.start_position - right.start_position)
}

function simpleCabinetComponentsForRow(row: number) {
  return cabinetComponents.value
    .filter((component) => component.area_id === null && component.row_number === row)
    .sort((left, right) => left.start_position - right.start_position)
}

function simpleAssetPlacementsForRow(row: number) {
  return assetPlacements.value
    .filter((placement) => placement.area_id === null && placement.row_number === row)
    .sort((left, right) => left.start_position - right.start_position)
}

function openCabinetComponent(
  component?: ElectricalCabinetComponent,
  area?: DistributionArea,
  row?: number,
  start?: number
) {
  editingCabinetComponentId.value = component?.id ?? null
  cabinetComponentForm.value = component
    ? {
        name: component.name,
        component_type: component.component_type,
        area_id: component.area_id,
        row_number: component.row_number,
        start_position: component.start_position,
        module_width: component.module_width,
        phases: [...component.phases],
        rated_current_a: component.rated_current_a,
        max_cross_section_mm2: component.max_cross_section_mm2,
        outgoing_connections: component.outgoing_connections,
        linked_rcd_device_id: component.linked_rcd_device_id,
        start_phase: component.start_phase,
        description: component.description,
        notes: component.notes
      }
    : {
        name: 'Phasenverteilerblock L1/L2/L3',
        component_type: 'phase_distribution_block',
        area_id: structuredLayout.value
          ? area?.id ?? deviceAreaOptions.value[0]?.id ?? null
          : null,
        row_number: row ?? 1,
        start_position: start ?? 1,
        module_width: 4,
        phases: ['L1', 'L2', 'L3'],
        rated_current_a: null,
        max_cross_section_mm2: null,
        outgoing_connections: null,
        linked_rcd_device_id: null,
        start_phase: 'L1',
        description: null,
        notes: null
      }
  cabinetComponentDialog.value = true
}

function applyCabinetComponentPhaseSuggestion() {
  if (editingCabinetComponentId.value) return
  if (cabinetComponentForm.value.component_type === 'neutral_rail') {
    cabinetComponentForm.value.phases = ['N']
    cabinetComponentForm.value.start_phase = null
  } else if (cabinetComponentForm.value.component_type === 'protective_earth_rail') {
    cabinetComponentForm.value.phases = ['PE']
    cabinetComponentForm.value.start_phase = null
    cabinetComponentForm.value.linked_rcd_device_id = null
  } else if (
    cabinetComponentForm.value.component_type === 'phase_distribution_block'
    || cabinetComponentForm.value.component_type === 'busbar'
    || cabinetComponentForm.value.component_type === 'phase_rail'
  ) {
    cabinetComponentForm.value.phases = ['L1', 'L2', 'L3']
    cabinetComponentForm.value.start_phase = cabinetComponentForm.value.component_type === 'busbar' ? 'L1' : null
    if (cabinetComponentForm.value.component_type !== 'busbar') {
      cabinetComponentForm.value.linked_rcd_device_id = null
    }
  } else {
    cabinetComponentForm.value.start_phase = null
    cabinetComponentForm.value.linked_rcd_device_id = null
  }
}

async function saveCabinetComponent() {
  if (
    !cabinetComponentForm.value.name.trim()
    || (structuredLayout.value && !cabinetComponentForm.value.area_id)
  ) {
    error.value = structuredLayout.value
      ? 'Bitte Bezeichnung und Gerätebereich angeben.'
      : 'Bitte eine Bezeichnung angeben.'
    return
  }
  saving.value = true
  error.value = null
  try {
    const payload: ElectricalCabinetComponentWrite = {
      ...cabinetComponentForm.value,
      name: cabinetComponentForm.value.name.trim(),
      area_id: structuredLayout.value ? cabinetComponentForm.value.area_id : null,
      description: optionalText(cabinetComponentForm.value.description),
      notes: optionalText(cabinetComponentForm.value.notes)
    }
    if (editingCabinetComponentId.value) {
      await electricalApi.updateCabinetComponent(
        distributionId.value,
        editingCabinetComponentId.value,
        payload
      )
    } else {
      await electricalApi.createCabinetComponent(distributionId.value, payload)
    }
    cabinetComponentDialog.value = false
    success.value = editingCabinetComponentId.value
      ? 'Schrankkomponente wurde aktualisiert.'
      : 'Schrankkomponente wurde angelegt.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Schrankkomponente konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archiveCabinetComponent(component: ElectricalCabinetComponent) {
  if (!window.confirm(`Schrankkomponente „${component.name}“ archivieren?`)) return
  try {
    await electricalApi.removeCabinetComponent(distributionId.value, component.id)
    success.value = 'Schrankkomponente wurde archiviert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Schrankkomponente konnte nicht archiviert werden.'
  }
}

async function archiveArea(area: DistributionArea) {
  if (!window.confirm(`Bereich „${area.name}“ archivieren?`)) return
  try {
    await electricalApi.removeArea(distributionId.value, area.id)
    success.value = 'Bereich wurde archiviert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bereich konnte nicht archiviert werden.'
  }
}

function openPlacement(device?: ProtectiveDevice, area?: DistributionArea) {
  placementDeviceId.value = device?.id ?? null
  placementForm.value = {
    area_id: structuredLayout.value ? area?.id ?? device?.area_id ?? null : null,
    row_number: device?.row_number ?? null,
    start_position: device?.start_position ?? null,
    module_width: device ? protectiveDeviceWidth(device) : null,
    assigned_rcd_id: device?.assigned_rcd_id ?? null,
    neutral_rail_id: device?.neutral_rail_id ?? null
  }
  placementDialog.value = true
}

async function savePlacement() {
  if (!placementDeviceId.value || (structuredLayout.value && !placementForm.value.area_id)) {
    error.value = structuredLayout.value
      ? 'Bitte Schutzgerät und Gerätebereich auswählen.'
      : 'Bitte ein Schutzgerät auswählen.'
    return
  }
  saving.value = true
  error.value = null
  try {
    await electricalApi.placeDevice(distributionId.value, placementDeviceId.value, {
      area_id: structuredLayout.value ? placementForm.value.area_id : null,
      row_number: optionalNumber(placementForm.value.row_number),
      start_position: optionalNumber(placementForm.value.start_position),
      module_width: optionalNumber(placementForm.value.module_width),
      assigned_rcd_id: placementForm.value.assigned_rcd_id,
      neutral_rail_id: placementForm.value.neutral_rail_id
    })
    placementDialog.value = false
    success.value = 'Schutzgerät wurde platziert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Schutzgerät konnte nicht platziert werden.'
  } finally {
    saving.value = false
  }
}

async function unassignDevice(device: ProtectiveDevice) {
  try {
    await electricalApi.placeDevice(distributionId.value, device.id, {
      area_id: null, row_number: null, start_position: null, module_width: null,
      assigned_rcd_id: device.assigned_rcd_id, neutral_rail_id: device.neutral_rail_id
    })
    success.value = 'Schutzgerät ist jetzt ohne Position.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zuordnung konnte nicht entfernt werden.'
  }
}

async function archiveDevice(device: ProtectiveDevice) {
  if (!window.confirm(`Schutzgerät „${device.asset.name}“ archivieren?`)) return
  try {
    await electricalApi.removeProtectiveDevice(device.id)
    success.value = 'Schutzgerät wurde archiviert und ist jetzt unter Archiv sichtbar.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Schutzgerät konnte nicht archiviert werden.'
  }
}

function devicesForArea(areaId: string): ProtectiveDevice[] {
  return distribution.value?.protective_devices.filter((device) => device.area_id === areaId) ?? []
}

function groupsForArea(area: DistributionArea) {
  const groups = groupProtectiveDevices(devicesForArea(area.id), area.rows)
  const knownRows = new Set(groups.map((group) => group.row))
  const occupiedRows = [
    ...cabinetComponentsForArea(area.id).map((component) => component.row_number),
    ...assetPlacementsForArea(area.id).map((placement) => placement.row_number)
  ]
  for (const row of occupiedRows) {
    if (!knownRows.has(row)) {
      groups.push({ row, devices: [] })
      knownRows.add(row)
    }
  }
  return groups.sort((left, right) => (
    (left.row ?? Number.MAX_SAFE_INTEGER) - (right.row ?? Number.MAX_SAFE_INTEGER)
  ))
}

function findDevice(deviceId: string): ProtectiveDevice | undefined {
  return distribution.value?.protective_devices.find((device) => device.id === deviceId)
}

function dropTargetKey(areaId: string, row: number, start: number): string {
  return `${areaId}:${row}:${start}`
}

function beginDeviceDrag(event: DragEvent, device: ProtectiveDevice) {
  if (!desktopDragEnabled.value || !event.dataTransfer) {
    event.preventDefault()
    return
  }
  if (!protectiveDeviceWidth(device)) {
    event.preventDefault()
    error.value =
      'Das Schutzgeräte-Asset benötigt zuerst eine DIN-Breite am Asset oder Asset-Typ.'
    return
  }
  error.value = null
  success.value = null
  draggedAsset.value = null
  draggedDeviceId.value = device.id
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/x-docofhome-kind', 'protective_device')
  event.dataTransfer.setData('text/plain', device.id)
}

function beginAssetDrag(
  event: DragEvent,
  asset: { asset_id?: string; id?: string; asset_name?: string; title?: string; module_width?: number; moduleWidth?: number | null }
) {
  const assetId = asset.asset_id ?? asset.id
  const moduleWidth = asset.module_width ?? asset.moduleWidth
  if (!desktopDragEnabled.value || !event.dataTransfer || !assetId || !moduleWidth) {
    event.preventDefault()
    return
  }
  error.value = null
  success.value = null
  draggedDeviceId.value = null
  draggedAsset.value = {
    assetId,
    moduleWidth,
    name: asset.asset_name ?? asset.title ?? 'DIN-Asset'
  }
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/x-docofhome-kind', 'asset')
  event.dataTransfer.setData('text/plain', assetId)
}

function finishDeviceDrag() {
  draggedDeviceId.value = null
  draggedAsset.value = null
  activeDropTarget.value = null
}

function draggedDevice(): ProtectiveDevice | undefined {
  return draggedDeviceId.value ? findDevice(draggedDeviceId.value) : undefined
}

function placementProblem(
  areaId: string | null,
  row: number,
  start: number,
  width: number,
  excludeDeviceId: string | null,
  excludeAssetId: string | null = null
): string | null {
  const area = areaId
    ? sections.value.flatMap((section) => section.areas).find((item) => item.id === areaId)
    : null
  const modulesPerRow = area?.modules_per_row ?? distribution.value?.modules_per_row ?? null
  const end = start + width - 1
  if (modulesPerRow !== null && end > modulesPerRow) {
    return `Das Gerät endet bei TE ${end}; verfügbar sind nur ${modulesPerRow} TE.`
  }
  for (const device of distribution.value?.protective_devices ?? []) {
    if (
      device.id === excludeDeviceId
      || device.area_id !== areaId
      || device.row_number !== row
      || device.start_position === null
      || device.module_width === null
    ) continue
    const otherEnd = device.start_position + device.module_width - 1
    if (start <= otherEnd && end >= device.start_position) {
      return `Position ist durch ${device.asset.name} belegt.`
    }
  }
  for (const placement of assetPlacements.value) {
    if (
      placement.asset_id === excludeAssetId
      || placement.area_id !== areaId
      || placement.row_number !== row
    ) continue
    const otherEnd = placement.start_position + placement.module_width - 1
    if (start <= otherEnd && end >= placement.start_position) {
      return `Position ist durch ${placement.asset_name} belegt.`
    }
  }
  for (const component of cabinetComponents.value) {
    if (component.component_type === 'busbar' && excludeDeviceId !== null) continue
    if (component.area_id !== areaId || component.row_number !== row) continue
    const otherEnd = component.start_position + component.module_width - 1
    if (start <= otherEnd && end >= component.start_position) {
      return `Position ist durch ${component.name} belegt.`
    }
  }
  return null
}

function currentDragProblem(areaId: string | null, row: number, start: number): string | null {
  const device = draggedDevice()
  const deviceWidth = device ? protectiveDeviceWidth(device) : null
  if (device && deviceWidth) {
    return placementProblem(areaId, row, start, deviceWidth, device.id)
  }
  if (draggedAsset.value) {
    return placementProblem(
      areaId,
      row,
      start,
      draggedAsset.value.moduleWidth,
      null,
      draggedAsset.value.assetId
    )
  }
  return null
}

function moduleDropProblem(area: DistributionArea, row: number, start: number): string | null {
  return currentDragProblem(area.id, row, start)
}

function simpleModuleDropProblem(row: number, start: number): string | null {
  return currentDragProblem(null, row, start)
}

function activateDropTarget(
  event: DragEvent,
  area: DistributionArea,
  row: number,
  start: number
) {
  if (!desktopDragEnabled.value || (!draggedDeviceId.value && !draggedAsset.value)) return
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  activeDropTarget.value = dropTargetKey(area.id, row, start)
}

function dropCellClasses(area: DistributionArea, row: number, start: number) {
  const active = activeDropTarget.value === dropTargetKey(area.id, row, start)
  if (!active) return {}
  return moduleDropProblem(area, row, start)
    ? { 'drop-target-invalid': true }
    : { 'drop-target-valid': true }
}

async function placeDraggedItem(areaId: string | null, row: number, start: number) {
  const device = draggedDevice()
  const asset = draggedAsset.value
  if (!desktopDragEnabled.value || (!device && !asset)) {
    finishDeviceDrag()
    return
  }
  const deviceWidth = device ? protectiveDeviceWidth(device) : null
  if (device && !deviceWidth) {
    error.value =
      'Das Schutzgeräte-Asset benötigt zuerst eine DIN-Breite am Asset oder Asset-Typ.'
    finishDeviceDrag()
    return
  }
  const problem = currentDragProblem(areaId, row, start)
  if (problem) {
    error.value = problem
    finishDeviceDrag()
    return
  }
  saving.value = true
  error.value = null
  try {
    if (device && deviceWidth) {
      await electricalApi.placeDevice(distributionId.value, device.id, {
        area_id: areaId,
        row_number: row,
        start_position: start,
        module_width: deviceWidth,
        assigned_rcd_id: device.assigned_rcd_id,
        neutral_rail_id: device.neutral_rail_id
      })
      success.value = `${device.asset.name} wurde auf Reihe ${row}, TE ${start} verschoben.`
    } else if (asset) {
      await electricalApi.placeAsset(distributionId.value, asset.assetId, {
        area_id: areaId,
        row_number: row,
        start_position: start,
        module_width: asset.moduleWidth
      })
      success.value = `${asset.name} wurde auf Reihe ${row}, TE ${start} platziert.`
    }
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Das DIN-Gerät konnte nicht verschoben werden.'
  } finally {
    saving.value = false
    finishDeviceDrag()
  }
}

async function dropDevice(
  _event: DragEvent,
  area: DistributionArea,
  row: number,
  start: number
) {
  await placeDraggedItem(area.id, row, start)
}

function activateSimpleDropTarget(event: DragEvent, row: number, start: number) {
  if (!desktopDragEnabled.value || (!draggedDeviceId.value && !draggedAsset.value)) return
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  activeDropTarget.value = `simple:${row}:${start}`
}

function simpleDropCellClasses(row: number, start: number) {
  const active = activeDropTarget.value === `simple:${row}:${start}`
  if (!active) return {}
  return simpleModuleDropProblem(row, start)
    ? { 'drop-target-invalid': true }
    : { 'drop-target-valid': true }
}

async function dropDeviceSimple(_event: DragEvent, row: number, start: number) {
  await placeDraggedItem(null, row, start)
}

</script>

<template>
  <v-container class="layout-page pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" :to="`/electrical/distributions/${distributionId}`" class="mb-3">
      Zur Verteilung
    </v-btn>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
    <template v-else-if="distribution">
      <div class="d-flex flex-wrap justify-space-between align-start ga-3 mb-5">
        <div>
          <h1>Schrankaufteilung · {{ distribution.display_name }}</h1>
          <p class="text-medium-emphasis mb-0">
            {{ structuredLayout
              ? 'Felder nebeneinander, Bereiche innerhalb des Feldes untereinander.'
              : 'Einfache Reihen mit Modulpositionen und zugeordneten Schutzgeräten.' }}
          </p>
        </div>
        <div class="d-flex flex-wrap ga-2">
          <v-btn v-if="structuredLayout" prepend-icon="mdi-view-column-outline" color="primary" @click="openSection()">Feld anlegen</v-btn>
          <v-btn prepend-icon="mdi-shield-plus-outline" variant="tonal" @click="openPlacement()">Schutzgerät platzieren</v-btn>
          <v-btn
            prepend-icon="mdi-call-split"
            variant="tonal"
            :disabled="structuredLayout && !deviceAreaOptions.length"
            @click="openCabinetComponent()"
          >
            Schrankkomponente
          </v-btn>
          <v-btn prepend-icon="mdi-memory" variant="tonal" :disabled="structuredLayout && !deviceAreaOptions.length" @click="openAssetPlacement()">DIN-Asset platzieren</v-btn>
          <v-btn v-if="structuredLayout" prepend-icon="mdi-meter-electric-outline" variant="tonal" :disabled="!meterAreaOptions.length" @click="openMeterPlacement()">Zähler platzieren</v-btn>
          <v-btn prepend-icon="mdi-pencil" variant="text" :to="`/electrical/distributions/${distributionId}/edit`">Verteilung</v-btn>
        </div>
      </div>

      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="topologyError" type="warning" variant="tonal" density="compact" class="mb-4">
        Die Schrankaufteilung ist verfügbar, aber Phase und Versorgungsweg konnten nicht geladen werden:
        {{ topologyError }}
      </v-alert>
      <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = null">{{ success }}</v-alert>
      <v-alert
        v-if="!structuredLayout && !simpleLayoutConfigured"
        type="info"
        variant="tonal"
        class="mb-5"
        title="Noch keine Schrankaufteilung angelegt"
      >
        Für diese Verteilung sind noch keine Reihen, Modulplätze oder Schutzgeräte dokumentiert.
        Konfiguriere eine einfache Reihenaufteilung oder wechsle zur Feld-/Bereichsaufteilung.
        <template #append>
          <v-btn
            color="primary"
            variant="tonal"
            prepend-icon="mdi-pencil"
            :to="`/electrical/distributions/${distributionId}/edit`"
          >
            Aufteilung anlegen
          </v-btn>
        </template>
      </v-alert>

      <v-card class="mb-5 layout-summary" variant="outlined">
        <v-card-text>
          <div class="d-flex flex-wrap align-center justify-space-between ga-3">
            <div class="summary-metrics">
              <v-chip prepend-icon="mdi-view-dashboard-outline" variant="tonal">
                {{ occupiedModuleCount }} von {{ layoutCapacity || '–' }} TE belegt
              </v-chip>
              <v-chip prepend-icon="mdi-package-variant-closed" variant="tonal">
                {{ layoutCapacity ? freeModuleCount : '–' }} TE frei
              </v-chip>
              <v-chip prepend-icon="mdi-map-marker-question-outline" variant="tonal">
                {{ unplacedCount }} nicht platziert
              </v-chip>
              <v-chip
                :color="layoutWarnings.length ? 'warning' : 'success'"
                :prepend-icon="layoutWarnings.length ? 'mdi-alert-outline' : 'mdi-check-circle-outline'"
                variant="tonal"
              >
                {{ layoutWarnings.length }} Hinweise
              </v-chip>
            </div>
            <v-btn-toggle v-model="viewMode" mandatory density="compact" divided>
              <v-btn value="compact" prepend-icon="mdi-view-sequential-outline">Kompakt</v-btn>
              <v-btn value="expanded" prepend-icon="mdi-format-list-bulleted">Erweitert</v-btn>
            </v-btn-toggle>
          </div>
          <div class="cabinet-legend mt-3" aria-label="Farblegende der Gerätetypen">
            <span class="legend-item cabinet-type-mcb">LS / Sicherung</span>
            <span class="legend-item cabinet-type-rcd">FI / RCD</span>
            <span class="legend-item cabinet-type-smart-meter">Smart Meter</span>
            <span class="legend-item cabinet-type-electric-meter">Stromzähler</span>
            <span class="legend-item cabinet-type-impulse-switch">Stromstoßschalter</span>
            <span class="legend-item cabinet-type-busbar">Sammel-/Kammschiene</span>
            <span class="legend-item cabinet-type-passive">Passive Komponente</span>
          </div>
          <v-alert
            v-if="layoutWarnings.length"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-3"
            title="Hinweise zur FI- und Neutralleiter-Zuordnung"
          >
            <ul class="pl-5 mb-0">
              <li v-for="message in layoutWarnings" :key="message">{{ message }}</li>
            </ul>
          </v-alert>
        </v-card-text>
      </v-card>

      <v-card
        v-if="!structuredLayout && simpleLayoutConfigured"
        class="mb-5"
        title="Einfache Reihenaufteilung"
        prepend-icon="mdi-view-sequential-outline"
      >
        <v-card-text>
          <v-alert
            v-if="distribution.rows === null || distribution.modules_per_row === null"
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Die Kapazität ist noch nicht vollständig angegeben. Schutzgeräte werden trotzdem
            angezeigt; Reihen oder Modulnummern können in den Verteilungseinstellungen ergänzt werden.
          </v-alert>

          <section
            v-for="group in simpleDeviceGroups"
            :key="group.row ?? 'unknown'"
            class="mb-7"
          >
            <div class="d-flex align-center justify-space-between mb-3">
              <h2>{{ group.row === null ? 'Position unbekannt' : `Reihe ${group.row}` }}</h2>
              <v-chip size="small" variant="tonal">{{ group.devices.length }} Geräte</v-chip>
            </div>

            <div
              v-if="group.row !== null && distribution.modules_per_row"
              class="module-scroll"
            >
              <div
                class="module-board"
                :class="{ 'is-dragging': draggedDeviceId !== null || draggedAsset !== null, 'compact-view': viewMode === 'compact' }"
                :style="moduleBoardStyle(distribution.modules_per_row)"
              >
                <div
                  v-for="moduleNumber in simpleModuleLabels"
                  :key="`simple-module-${group.row}-${moduleNumber}`"
                  class="module-cell"
                  :style="{ gridColumn: moduleNumber }"
                >
                  {{ moduleNumber }}
                </div>
                <div
                  v-for="moduleNumber in simpleModuleLabels"
                  :key="`simple-drop-${group.row}-${moduleNumber}`"
                  class="module-drop-cell"
                  :class="simpleDropCellClasses(group.row, moduleNumber)"
                  :style="{ gridColumn: moduleNumber }"
                  :title="simpleModuleDropProblem(group.row, moduleNumber)
                    ?? `Auf Reihe ${group.row}, TE ${moduleNumber} ablegen`"
                  @dragover.prevent="activateSimpleDropTarget($event, group.row, moduleNumber)"
                  @drop.prevent="dropDeviceSimple($event, group.row, moduleNumber)"
                />
                <v-card
                  v-for="placement in modulePlacements(group.devices)"
                  :key="placement.device.id"
                  class="module-device"
                  :class="{
                    'drag-ready': desktopDragEnabled,
                    'drag-source': draggedDeviceId === placement.device.id,
                    'has-group-warning': placement.device.group_warnings.length > 0,
                    [protectiveDeviceCabinetClass(placement.device.device_type)]: true
                  }"
                  variant="tonal"
                  @click="openDeviceDetails(placement.device)"
                  :style="{ gridColumn: placement.gridColumn }"
                  :draggable="desktopDragEnabled"
                  @dragstart="beginDeviceDrag($event, placement.device)"
                  @dragend="finishDeviceDrag"
                >
                  <v-card-title class="module-device-title text-caption font-weight-bold">
                    {{ placement.device.asset.name }}
                  </v-card-title>
                  <div v-if="placement.device.asset.technical_short_label" class="module-compact-value">
                    {{ placement.device.asset.technical_short_label }}
                  </div>
                  <v-card-subtitle>{{ placement.device.asset.jarvis_code }}</v-card-subtitle>
                  <v-card-text class="pa-2 text-caption">
                    <div class="device-meta-row mb-2">
                      <span>{{ protectiveDeviceLabels[placement.device.device_type] }} · TE {{ placement.start }}–{{ placement.end }}</span>
                      <v-chip v-if="placement.device.calculated_phases.length" size="x-small" color="primary" variant="flat">
                        {{ devicePhaseText(placement.device) }}
                      </v-chip>
                    </div>
                    <div v-if="placement.device.effective_rcd_name" class="text-medium-emphasis">
                      FI: {{ placement.device.effective_rcd_name }}
                    </div>
                    <div v-if="placement.device.effective_neutral_rail_name" class="text-medium-emphasis">
                      N: {{ placement.device.effective_neutral_rail_name }}
                    </div>
                    <v-icon v-if="placement.device.group_warnings.length" icon="mdi-alert-outline" color="warning" size="small" class="mt-1" />
                    <ElectricalWiringSummary
                      v-if="viewMode === 'expanded'"
                      :topology="topology"
                      endpoint-kind="protective_device"
                      :endpoint-id="placement.device.id"
                      compact
                    />
                  </v-card-text>
                  <v-card-actions class="module-device-actions pa-1">
                    <v-btn icon="mdi-map-marker-path" size="x-small" variant="text" title="Position bearbeiten" @click.stop="openPlacement(placement.device)" />
                    <v-btn icon="mdi-pencil" size="x-small" variant="text" :to="`/electrical/protective-devices/${placement.device.id}/edit`" title="Schutzgerät bearbeiten" @click.stop />
                    <v-btn icon="mdi-link-off" size="x-small" variant="text" title="Position entfernen" @click.stop="unassignDevice(placement.device)" />
                  </v-card-actions>
                </v-card>
                <v-card
                  v-for="component in simpleCabinetComponentsForRow(group.row)"
                  :key="component.id"
                  class="module-device cabinet-component-card"
                  :class="{ 'busbar-card': component.component_type === 'busbar', [cabinetComponentClass(component.component_type)]: true }"
                  variant="outlined"
                  :style="componentGridStyle(component)"
                  @click="openComponentDetails(component)"
                >
                  <v-card-title class="module-device-title text-caption font-weight-bold">
                    {{ component.name }}
                  </v-card-title>
                  <v-card-text class="pa-2 text-caption">
                    <div>{{ cabinetComponentTypeMeta[component.component_type].title }} · TE {{ component.start_position }}–{{ component.start_position + component.module_width - 1 }}</div>
                    <div v-if="component.linked_rcd_name" class="mt-1">FI: {{ component.linked_rcd_name }}</div>
                    <div v-if="component.component_type === 'busbar'" class="busbar-phase-sequence mt-1">
                      <span v-for="(phase, index) in busbarPhasePattern(component)" :key="`${component.id}-${index}`">{{ phase }}</span>
                    </div>
                    <div v-else-if="component.phases.length" class="mt-1">Leiter: {{ component.phases.join(', ') }}</div>
                    <ElectricalWiringSummary
                      v-if="viewMode === 'expanded'"
                      :topology="topology"
                      endpoint-kind="cabinet_component"
                      :endpoint-id="component.id"
                      compact
                    />
                  </v-card-text>
                  <v-card-actions class="module-device-actions pa-1">
                    <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Schrankkomponente bearbeiten" @click.stop="openCabinetComponent(component)" />
                    <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" title="Schrankkomponente archivieren" @click.stop="archiveCabinetComponent(component)" />
                  </v-card-actions>
                </v-card>
                <v-card
                  v-for="placement in simpleAssetPlacementsForRow(group.row)"
                  :key="placement.id"
                  class="module-device"
                  :class="{
                    'drag-ready': desktopDragEnabled,
                    'drag-source': draggedAsset?.assetId === placement.asset_id,
                    [assetCabinetClass(placement.asset_type_name || 'Asset')]: true
                  }"
                  variant="outlined"
                  :style="{ gridColumn: `${placement.start_position} / span ${placement.module_width}` }"
                  :draggable="desktopDragEnabled"
                  @click="openAssetDetails(placement)"
                  @dragstart="beginAssetDrag($event, placement)"
                  @dragend="finishDeviceDrag"
                >
                  <v-card-title class="module-device-title text-caption font-weight-bold">{{ placement.asset_name }}</v-card-title>
                  <div v-if="placement.primary_live_value || placement.technical_short_label" class="module-compact-value">
                    {{ placement.primary_live_value ? liveValueText(placement) : placement.technical_short_label }}
                  </div>
                  <v-card-text class="pa-2 text-caption">
                    <div>{{ placement.product_name || placement.asset_code }} · TE {{ placement.start_position }}–{{ placement.start_position + placement.module_width - 1 }}</div>
                    <div>{{ liveValueText(placement) }}</div>
                    <ElectricalWiringSummary
                      v-if="viewMode === 'expanded'"
                      :topology="topology"
                      endpoint-kind="asset"
                      :endpoint-id="placement.asset_id"
                      compact
                    />
                  </v-card-text>
                  <v-card-actions class="module-device-actions pa-1">
                    <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Platzierung bearbeiten" @click.stop="openAssetPlacement(undefined, placement)" />
                    <v-btn icon="mdi-link-off" size="x-small" variant="text" title="Aus Plan entfernen" @click.stop="unplaceAsset(placement)" />
                  </v-card-actions>
                </v-card>
              </div>
              <div
                v-if="devicesWithoutModulePlacement(group.devices).length"
                class="device-list ga-2 mt-3"
              >
                <v-chip
                  v-for="device in devicesWithoutModulePlacement(group.devices)"
                  :key="device.id"
                  prepend-icon="mdi-map-marker-question-outline"
                  :class="{ 'drag-ready': desktopDragEnabled }"
                  :draggable="desktopDragEnabled"
                  @click="openPlacement(device)"
                  @dragstart="beginDeviceDrag($event, device)"
                  @dragend="finishDeviceDrag"
                >
                  {{ device.asset.name }} · Modulposition ergänzen
                </v-chip>
              </div>
            </div>

            <div v-else-if="group.devices.length" class="device-list ga-2">
              <v-chip
                v-for="device in group.devices"
                :key="device.id"
                prepend-icon="mdi-shield-outline"
                :class="{ 'drag-ready': desktopDragEnabled }"
                :draggable="desktopDragEnabled"
                @click="openPlacement(device)"
                @dragstart="beginDeviceDrag($event, device)"
                @dragend="finishDeviceDrag"
              >
                {{ device.asset.name }} · {{ device.asset.jarvis_code }}
              </v-chip>
            </div>
            <p v-else class="text-medium-emphasis mb-0">Noch keine Geräte in dieser Reihe.</p>
          </section>

          <div class="d-flex flex-wrap ga-2">
            <v-btn
              color="primary"
              prepend-icon="mdi-shield-plus-outline"
              :to="`/electrical/protective-devices/new?distribution=${distributionId}`"
            >
              Schutzgerät hinzufügen
            </v-btn>
            <v-btn variant="tonal" prepend-icon="mdi-call-split" @click="openCabinetComponent()">
              Verteilerblock / Schiene
            </v-btn>
            <v-btn variant="tonal" prepend-icon="mdi-memory" @click="openAssetPlacement()">
              DIN-Asset platzieren
            </v-btn>
            <v-btn
              variant="tonal"
              prepend-icon="mdi-view-column-outline"
              :to="`/electrical/distributions/${distributionId}/edit`"
            >
              Aufbau ändern
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
      <v-alert
        v-if="desktopDragEnabled && (structuredLayout || simpleLayoutConfigured)"
        type="info"
        variant="tonal"
        density="compact"
        icon="mdi-drag-horizontal-variant"
        class="mb-4"
        title="Drag-and-drop aktiv"
      >
        Ziehe ein Schutzgerät oder DIN-Asset auf die gewünschte Teilungseinheit. Bereits platzierte
        Geräte lassen sich ebenso verschieben. Ohne DIN-Breite ist keine Platzierung möglich.
      </v-alert>

      <v-alert v-if="structuredLayout && sections.length === 0" type="info" variant="tonal" class="mb-5">
        Noch keine Felder angelegt. Lege zunächst ein Feld und darin die benötigten Bereiche an.
      </v-alert>

      <div v-if="structuredLayout" class="layout-grid">
        <v-card v-for="section in sections" :key="section.id" class="section-card" variant="outlined">
          <v-card-title class="d-flex align-center ga-2">
            <v-icon icon="mdi-view-column-outline" color="primary" />
            <span class="text-wrap">{{ section.name }}</span>
            <v-spacer />
            <v-btn icon="mdi-plus" size="small" variant="text" aria-label="Bereich anlegen" title="Bereich anlegen" @click="openArea(section.id)" />
            <v-btn icon="mdi-pencil" size="small" variant="text" aria-label="Feld bearbeiten" title="Feld bearbeiten" @click="openSection(section)" />
            <v-btn icon="mdi-archive-arrow-down-outline" size="small" color="warning" variant="text" aria-label="Feld archivieren" title="Feld archivieren" @click="archiveSection(section)" />
          </v-card-title>
          <v-card-subtitle v-if="section.description">{{ section.description }}</v-card-subtitle>
          <v-card-text class="area-grid">
            <v-alert v-if="section.areas.length === 0" density="compact" type="info" variant="tonal">Noch keine Bereiche.</v-alert>
            <v-card v-for="area in section.areas" :key="area.id" class="area-card" :class="{ 'area-half': area.width === 'half', 'area-left': area.side === 'left', 'area-right': area.side === 'right' }" variant="tonal">
              <v-card-title class="d-flex align-center ga-2 text-body-1 font-weight-bold">
                <v-icon :icon="areaTypeMeta[area.area_type].icon" size="small" />
                <span class="text-wrap">{{ area.name }}</span>
                <v-spacer />
                <v-btn v-if="area.area_type === 'device_rows'" icon="mdi-call-split" size="x-small" variant="text" aria-label="Schrankkomponente platzieren" title="Verteilerblock oder Schiene platzieren" @click="openCabinetComponent(undefined, area)" />
                <v-btn v-if="area.area_type === 'device_rows'" icon="mdi-memory" size="x-small" variant="text" aria-label="DIN-Asset platzieren" title="DIN-Asset platzieren" @click="openAssetPlacement(area)" />
                <v-btn v-if="area.area_type === 'device_rows'" icon="mdi-shield-plus-outline" size="x-small" variant="text" aria-label="Schutzgerät platzieren" title="Schutzgerät platzieren" @click="openPlacement(undefined, area)" />
                <v-btn v-if="area.area_type === 'meter'" icon="mdi-meter-electric-outline" size="x-small" variant="text" aria-label="Zähler platzieren" title="Zähler platzieren" @click="openMeterPlacement(undefined, area)" />
                <v-btn icon="mdi-pencil" size="x-small" variant="text" aria-label="Bereich bearbeiten" title="Bereich bearbeiten" @click="openArea(section.id, area)" />
                <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" aria-label="Bereich archivieren" title="Bereich archivieren" @click="archiveArea(area)" />
              </v-card-title>
              <v-card-subtitle>
                Ebene {{ area.position }} · {{ areaTypeMeta[area.area_type].title }}
                <span v-if="area.width === 'half'"> · {{ area.side === 'right' ? 'rechts' : 'links' }}</span>
              </v-card-subtitle>
              <v-card-text>
                <p v-if="area.description" class="text-body-2 mb-3">{{ area.description }}</p>
                <template v-if="area.area_type === 'device_rows'">
                  <div
                    v-if="devicesForArea(area.id).length === 0 && assetPlacementsForArea(area.id).length === 0 && cabinetComponentsForArea(area.id).length === 0"
                    class="text-medium-emphasis text-body-2"
                  >
                    Keine Geräte platziert.
                  </div>
                  <section v-for="group in groupsForArea(area)" :key="group.row ?? 'unknown'" class="mb-4">
                    <div class="d-flex align-center justify-space-between mb-2">
                      <strong>{{ group.row === null ? 'Position unbekannt' : `Reihe ${group.row}` }}</strong>
                      <v-chip size="x-small">{{ group.devices.length }}</v-chip>
                    </div>
                    <div v-if="group.row !== null && area.modules_per_row" class="module-scroll">
                      <div
                        class="module-board"
                        :class="{ 'is-dragging': draggedDeviceId !== null || draggedAsset !== null, 'compact-view': viewMode === 'compact' }"
                        :style="moduleBoardStyle(area.modules_per_row)"
                      >
                        <div v-for="number in moduleNumbers(area.modules_per_row)" :key="number" class="module-cell" :style="{ gridColumn: number }">{{ number }}</div>
                        <div
                          v-for="number in moduleNumbers(area.modules_per_row)"
                          :key="`drop-${number}`"
                          class="module-drop-cell"
                          :class="dropCellClasses(area, group.row, number)"
                          :style="{ gridColumn: number }"
                          :title="moduleDropProblem(area, group.row, number)
                            ?? `Auf Reihe ${group.row}, Modul ${number} ablegen`"
                          @dragover.prevent="activateDropTarget($event, area, group.row, number)"
                          @drop.prevent="dropDevice($event, area, group.row, number)"
                        />
                        <v-card
                          v-for="placement in modulePlacements(group.devices)"
                          :key="placement.device.id"
                          class="module-device"
                          :class="{
                            'drag-ready': desktopDragEnabled,
                            'drag-source': draggedDeviceId === placement.device.id,
                            'has-group-warning': placement.device.group_warnings.length > 0,
                            [protectiveDeviceCabinetClass(placement.device.device_type)]: true
                          }"
                          :style="{ gridColumn: placement.gridColumn }"
                          variant="outlined"
                          @click="openDeviceDetails(placement.device)"
                          :draggable="desktopDragEnabled"
                          @dragstart="beginDeviceDrag($event, placement.device)"
                          @dragend="finishDeviceDrag"
                        >
                          <v-card-title class="module-device-title text-caption font-weight-bold">{{ placement.device.asset.name }}</v-card-title>
                          <div v-if="placement.device.asset.technical_short_label" class="module-compact-value">
                            {{ placement.device.asset.technical_short_label }}
                          </div>
                          <v-card-text class="pa-2 text-caption">
                            <div class="device-meta-row mb-2">
                              <span>{{ protectiveDeviceLabels[placement.device.device_type] }} · TE {{ placement.start }}–{{ placement.end }}</span>
                              <v-chip v-if="placement.device.calculated_phases.length" size="x-small" color="primary" variant="flat">
                                {{ devicePhaseText(placement.device) }}
                              </v-chip>
                            </div>
                            <div v-if="placement.device.effective_rcd_name" class="text-medium-emphasis">FI: {{ placement.device.effective_rcd_name }}</div>
                            <div v-if="placement.device.effective_neutral_rail_name" class="text-medium-emphasis">N: {{ placement.device.effective_neutral_rail_name }}</div>
                            <v-icon v-if="placement.device.group_warnings.length" icon="mdi-alert-outline" color="warning" size="small" class="mt-1" />
                            <ElectricalWiringSummary
                              v-if="viewMode === 'expanded'"
                              :topology="topology"
                              endpoint-kind="protective_device"
                              :endpoint-id="placement.device.id"
                              compact
                            />
                          </v-card-text>
                          <v-card-actions class="module-device-actions pa-1">
                            <v-btn icon="mdi-map-marker-path" size="x-small" variant="text" aria-label="Position bearbeiten" title="Position bearbeiten" @click.stop="openPlacement(placement.device, area)" />
                            <v-btn icon="mdi-pencil" size="x-small" variant="text" aria-label="Technische Daten bearbeiten" title="Technische Daten bearbeiten" :to="`/electrical/protective-devices/${placement.device.id}/edit`" @click.stop />
                            <v-btn icon="mdi-link-off" size="x-small" variant="text" aria-label="Position entfernen" title="Position aus dem Plan entfernen" @click.stop="unassignDevice(placement.device)" />
                            <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" aria-label="Schutzgerät archivieren" title="Schutzgerät archivieren" @click.stop="archiveDevice(placement.device)" />
                          </v-card-actions>
                        </v-card>
                        <v-card
                          v-for="component in cabinetComponentsForArea(area.id).filter((item) => item.row_number === group.row)"
                          :key="component.id"
                          class="module-device cabinet-component-card"
                          :class="{ 'busbar-card': component.component_type === 'busbar', [cabinetComponentClass(component.component_type)]: true }"
                          variant="tonal"
                          :style="componentGridStyle(component)"
                          @click="openComponentDetails(component)"
                        >
                          <v-card-title class="module-device-title text-caption font-weight-bold">{{ component.name }}</v-card-title>
                          <v-card-text class="pa-2 text-caption">
                            <div>{{ cabinetComponentTypeMeta[component.component_type].title }} · TE {{ component.start_position }}–{{ component.start_position + component.module_width - 1 }}</div>
                            <div v-if="component.linked_rcd_name" class="mt-1">FI: {{ component.linked_rcd_name }}</div>
                            <div v-if="component.component_type === 'busbar'" class="busbar-phase-sequence mt-1">
                              <span v-for="(phase, index) in busbarPhasePattern(component)" :key="`${component.id}-${index}`">{{ phase }}</span>
                            </div>
                            <div v-else-if="component.phases.length" class="mt-1">Leiter: {{ component.phases.join(', ') }}</div>
                            <ElectricalWiringSummary
                              v-if="viewMode === 'expanded'"
                              :topology="topology"
                              endpoint-kind="cabinet_component"
                              :endpoint-id="component.id"
                              compact
                            />
                          </v-card-text>
                          <v-card-actions class="module-device-actions pa-1">
                            <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Schrankkomponente bearbeiten" @click.stop="openCabinetComponent(component, area)" />
                            <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" title="Schrankkomponente archivieren" @click.stop="archiveCabinetComponent(component)" />
                          </v-card-actions>
                        </v-card>
                        <v-card
                          v-for="placement in assetPlacementsForArea(area.id).filter((item) => item.row_number === group.row)"
                          :key="placement.id"
                          class="module-device"
                          :class="{
                            'drag-ready': desktopDragEnabled,
                            'drag-source': draggedAsset?.assetId === placement.asset_id,
                            [assetCabinetClass(placement.asset_type_name || 'Asset')]: true
                          }"
                          variant="outlined"
                          :style="{ gridColumn: `${placement.start_position} / span ${placement.module_width}` }"
                          :draggable="desktopDragEnabled"
                          @click="openAssetDetails(placement)"
                          @dragstart="beginAssetDrag($event, placement)"
                          @dragend="finishDeviceDrag"
                        >
                          <v-card-title class="module-device-title text-caption font-weight-bold">{{ placement.asset_name }}</v-card-title>
                          <div v-if="placement.primary_live_value || placement.technical_short_label" class="module-compact-value">
                            {{ placement.primary_live_value ? liveValueText(placement) : placement.technical_short_label }}
                          </div>
                          <v-card-text class="pa-2 text-caption">
                            <div>{{ placement.product_name || placement.asset_code }} · TE {{ placement.start_position }}–{{ placement.start_position + placement.module_width - 1 }}</div>
                            <div>{{ liveValueText(placement) }}</div>
                            <ElectricalWiringSummary
                              v-if="viewMode === 'expanded'"
                              :topology="topology"
                              endpoint-kind="asset"
                              :endpoint-id="placement.asset_id"
                              compact
                            />
                          </v-card-text>
                          <v-card-actions class="module-device-actions pa-1">
                            <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Platzierung bearbeiten" @click.stop="openAssetPlacement(area, placement)" />
                            <v-btn icon="mdi-link-off" size="x-small" variant="text" title="Aus Plan entfernen" @click.stop="unplaceAsset(placement)" />
                          </v-card-actions>
                        </v-card>
                      </div>
                    </div>
                    <div v-else class="device-list">
                      <span
                        v-for="device in group.devices"
                        :key="device.id"
                        class="d-inline-flex align-center ga-1 ma-1"
                        :class="{ 'drag-ready': desktopDragEnabled }"
                        :draggable="desktopDragEnabled"
                        :title="desktopDragEnabled ? 'Auf eine Modulposition ziehen' : undefined"
                        @dragstart="beginDeviceDrag($event, device)"
                        @dragend="finishDeviceDrag"
                      >
                        <v-chip closable @click="openPlacement(device, area)" @click:close="unassignDevice(device)">
                          {{ device.asset.name }}
                        </v-chip>
                        <ElectricalWiringSummary
                          :topology="topology"
                          endpoint-kind="protective_device"
                          :endpoint-id="device.id"
                          compact
                        />
                        <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" aria-label="Schutzgerät archivieren" title="Schutzgerät archivieren" @click="archiveDevice(device)" />
                      </span>
                    </div>
                  </section>
                  <div v-if="cabinetComponentsForArea(area.id).length && !area.modules_per_row" class="mt-4">
                    <div class="text-subtitle-2 mb-2">Schrankkomponenten</div>
                    <v-card v-for="component in cabinetComponentsForArea(area.id)" :key="component.id" variant="outlined" class="mb-2">
                      <v-card-text class="d-flex align-center ga-3">
                        <v-icon :icon="cabinetComponentTypeMeta[component.component_type].icon" color="primary" />
                        <div class="flex-grow-1">
                          <strong>{{ component.name }}</strong>
                          <div class="text-caption text-medium-emphasis">
                            {{ cabinetComponentTypeMeta[component.component_type].title }} · Reihe {{ component.row_number }} · TE {{ component.start_position }}–{{ component.start_position + component.module_width - 1 }}
                          </div>
                          <ElectricalWiringSummary :topology="topology" endpoint-kind="cabinet_component" :endpoint-id="component.id" compact />
                        </div>
                        <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Schrankkomponente bearbeiten" @click="openCabinetComponent(component, area)" />
                        <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" title="Schrankkomponente archivieren" @click="archiveCabinetComponent(component)" />
                      </v-card-text>
                    </v-card>
                  </div>
                  <div v-if="assetPlacementsForArea(area.id).length && !area.modules_per_row" class="mt-4">
                    <div class="text-subtitle-2 mb-2">DIN-Hutschienengeräte ohne Modulraster</div>
                    <v-card v-for="placement in assetPlacementsForArea(area.id)" :key="placement.id" variant="outlined" class="mb-2">
                      <v-card-text class="d-flex align-center ga-3">
                        <v-icon icon="mdi-memory" color="primary" />
                        <div class="flex-grow-1">
                          <strong>{{ placement.asset_name }}</strong>
                          <div class="text-caption text-medium-emphasis">
                            {{ placement.product_name || placement.asset_code }} · Reihe {{ placement.row_number }} · TE {{ placement.start_position }}–{{ placement.start_position + placement.module_width - 1 }}
                          </div>
                          <div class="text-h6">{{ liveValueText(placement) }}</div>
                          <div v-if="placement.primary_live_value?.last_updated" class="text-caption text-medium-emphasis">
                            Stand {{ new Date(placement.primary_live_value.last_updated).toLocaleString() }}
                          </div>
                        </div>
                        <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Platzierung bearbeiten" @click="openAssetPlacement(area, placement)" />
                        <v-btn icon="mdi-link-off" size="x-small" variant="text" title="Aus Plan entfernen" @click="unplaceAsset(placement)" />
                      </v-card-text>
                    </v-card>
                  </div>
                </template>
                <template v-else-if="area.area_type === 'meter'">
                  <div v-if="metersForArea(area.id).length" class="d-flex flex-column ga-2">
                    <v-card v-for="placement in metersForArea(area.id)" :key="placement.id" variant="outlined">
                      <v-card-text class="d-flex align-center ga-3">
                        <v-icon icon="mdi-meter-electric-outline" color="primary" size="32" />
                        <div class="flex-grow-1">
                          <strong>{{ placement.meter_name }}</strong>
                          <div class="text-caption text-medium-emphasis">
                            {{ [placement.serial_number, placement.asset_name, placement.asset_code, placement.location_path].filter(Boolean).join(' · ') || placement.meter_type }}
                          </div>
                          <div>{{ formatMeterValue(placement.latest_value, placement.unit) }}</div>
                        </div>
                        <v-btn icon="mdi-pencil" size="x-small" variant="text" title="Platzierung bearbeiten" @click="openMeterPlacement(undefined, area, placement)" />
                        <v-btn icon="mdi-link-off" size="x-small" variant="text" title="Aus Zählerfeld entfernen" @click="unplaceMeterPlacement(placement)" />
                      </v-card-text>
                    </v-card>
                  </div>
                  <div v-else class="area-placeholder"><span class="text-medium-emphasis">Keine Zähler platziert.</span></div>
                </template>
                <div v-else class="area-placeholder">
                  <v-icon :icon="areaTypeMeta[area.area_type].icon" size="36" color="secondary" />
                  <strong v-if="area.area_type === 'neutral_rail'">N</strong>
                  <strong v-if="area.area_type === 'protective_earth_rail'">PE</strong>
                </div>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </div>

      <v-card v-if="unassignedDevices.length" class="mt-5" title="Noch nicht platzierte Schutzgeräte" prepend-icon="mdi-map-marker-question-outline">
        <v-card-text>
          <span
            v-for="device in unassignedDevices"
            :key="device.id"
            class="d-inline-flex align-center ga-1 ma-1"
            :class="{ 'drag-ready': desktopDragEnabled }"
            :draggable="desktopDragEnabled"
            :title="desktopDragEnabled ? 'Auf eine Modulposition ziehen' : undefined"
            @dragstart="beginDeviceDrag($event, device)"
            @dragend="finishDeviceDrag"
          >
            <v-chip @click="openPlacement(device)">
              {{ device.asset.name }} · {{ device.asset.jarvis_code }}
            </v-chip>
            <ElectricalWiringSummary
              :topology="topology"
              endpoint-kind="protective_device"
              :endpoint-id="device.id"
              compact
            />
            <v-btn icon="mdi-archive-arrow-down-outline" size="x-small" color="warning" variant="text" aria-label="Schutzgerät archivieren" title="Schutzgerät archivieren" @click="archiveDevice(device)" />
          </span>
        </v-card-text>
      </v-card>

      <v-card v-if="dinAssetOptions.length" class="mt-5" title="Noch nicht platzierte DIN-Assets" prepend-icon="mdi-memory">
        <v-card-text>
          <v-chip
            v-for="asset in dinAssetOptions"
            :key="asset.id"
            class="ma-1"
            prepend-icon="mdi-memory"
            :class="{ 'drag-ready': desktopDragEnabled }"
            :draggable="desktopDragEnabled"
            :title="desktopDragEnabled ? 'Auf eine freie Teilungseinheit ziehen' : undefined"
            @click="openAssetPlacement(undefined, undefined, asset.id)"
            @dragstart="beginAssetDrag($event, asset)"
            @dragend="finishDeviceDrag"
          >
            {{ asset.title }} · {{ asset.moduleWidth }} TE
          </v-chip>
        </v-card-text>
      </v-card>

      <v-card v-if="unassignedMeterCandidates.length" class="mt-5" title="Noch nicht platzierte Zähler" prepend-icon="mdi-meter-electric-outline">
        <v-card-text>
          <v-chip
            v-for="candidate in unassignedMeterCandidates"
            :key="candidate.value"
            class="ma-1"
            prepend-icon="mdi-meter-electric-outline"
            @click="openMeterPlacement(candidate)"
          >
            {{ candidate.title }}<span v-if="candidate.subtitle"> · {{ candidate.subtitle }}</span>
          </v-chip>
        </v-card-text>
      </v-card>
    </template>

    <v-navigation-drawer v-model="detailDrawer" location="right" temporary width="420">
      <div class="pa-4">
        <div class="d-flex align-center mb-4">
          <h2 class="text-h6">Details</h2>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" size="small" @click="detailDrawer = false" />
        </div>
        <template v-if="detailDevice">
          <v-icon icon="mdi-shield-outline" color="primary" size="36" class="mb-2" />
          <h3>{{ detailDevice.asset.name }}</h3>
          <p class="text-medium-emphasis">{{ detailDevice.asset.jarvis_code }}</p>
          <v-list density="compact">
            <v-list-item title="Position" :subtitle="detailDevice.row_number ? `Reihe ${detailDevice.row_number}, TE ${detailDevice.start_position}–${(detailDevice.start_position ?? 1) + (detailDevice.module_width ?? 1) - 1}` : 'Nicht platziert'" />
            <v-list-item title="Phase" :subtitle="devicePhaseText(detailDevice)" />
            <v-list-item title="FI/RCD" :subtitle="detailDevice.effective_rcd_name || 'Nicht zugeordnet'" />
            <v-list-item title="Neutralleiter" :subtitle="detailDevice.effective_neutral_rail_name || 'Nicht zugeordnet'" />
            <v-list-item title="Sammelschiene" :subtitle="detailDevice.busbar_component_name || 'Keine'" />
          </v-list>
          <v-alert v-if="detailDevice.group_warnings.length" type="warning" variant="tonal" density="compact" class="my-3">
            <div v-for="message in detailDevice.group_warnings" :key="message">{{ message }}</div>
          </v-alert>
          <div class="d-flex flex-wrap ga-2 mt-4">
            <v-btn color="primary" prepend-icon="mdi-pencil" :to="`/assets/${detailDevice.asset.id}/edit`">Asset bearbeiten</v-btn>
            <v-btn variant="tonal" prepend-icon="mdi-map-marker-path" @click="openPlacement(detailDevice)">Position / Gruppe</v-btn>
            <v-btn variant="tonal" prepend-icon="mdi-tune" :to="`/electrical/protective-devices/${detailDevice.id}/edit`">Technische Daten</v-btn>
          </div>
        </template>
        <template v-else-if="detailComponent">
          <v-icon :icon="cabinetComponentTypeMeta[detailComponent.component_type].icon" color="primary" size="36" class="mb-2" />
          <h3>{{ detailComponent.name }}</h3>
          <p class="text-medium-emphasis">{{ cabinetComponentTypeMeta[detailComponent.component_type].title }}</p>
          <v-list density="compact">
            <v-list-item title="Position" :subtitle="`Reihe ${detailComponent.row_number}, TE ${detailComponent.start_position}–${detailComponent.start_position + detailComponent.module_width - 1}`" />
            <v-list-item title="Leiter" :subtitle="detailComponent.phases.join(', ') || 'Keine'" />
            <v-list-item v-if="detailComponent.component_type === 'busbar'" title="Phasenfolge" :subtitle="busbarPhasePattern(detailComponent).join(' – ')" />
            <v-list-item title="FI/RCD" :subtitle="detailComponent.linked_rcd_name || 'Nicht zugeordnet'" />
            <v-list-item v-if="detailComponent.outgoing_connections" title="Abgänge" :subtitle="String(detailComponent.outgoing_connections)" />
          </v-list>
          <v-btn class="mt-4" color="primary" prepend-icon="mdi-pencil" @click="openCabinetComponent(detailComponent)">Bearbeiten</v-btn>
        </template>
        <template v-else-if="detailAsset">
          <v-icon icon="mdi-memory" color="primary" size="36" class="mb-2" />
          <h3>{{ detailAsset.asset_name }}</h3>
          <p class="text-medium-emphasis">{{ detailAsset.product_name || detailAsset.asset_code }}</p>
          <v-list density="compact">
            <v-list-item title="Position" :subtitle="`Reihe ${detailAsset.row_number}, TE ${detailAsset.start_position}–${detailAsset.start_position + detailAsset.module_width - 1}`" />
            <v-list-item title="DIN-Breite" :subtitle="`${detailAsset.module_width} TE`" />
            <v-list-item title="Livewert" :subtitle="liveValueText(detailAsset)" />
          </v-list>
          <div class="d-flex flex-wrap ga-2 mt-4">
            <v-btn color="primary" prepend-icon="mdi-pencil" :to="`/assets/${detailAsset.asset_id}/edit`">Asset bearbeiten</v-btn>
            <v-btn variant="tonal" prepend-icon="mdi-map-marker-path" @click="openAssetPlacement(undefined, detailAsset)">Position bearbeiten</v-btn>
          </div>
        </template>
      </div>
    </v-navigation-drawer>

    <v-dialog v-model="sectionDialog" max-width="560">
      <v-card :title="editingSectionId ? 'Feld bearbeiten' : 'Feld anlegen'">
        <v-card-text>
          <v-text-field v-model="sectionForm.name" label="Name" :rules="[requiredRule]" />
          <v-text-field v-model.number="sectionForm.position" label="Position von links" type="number" min="1" max="50" :rules="[positiveRule]" />
          <v-textarea v-model="sectionForm.description" label="Beschreibung (optional)" rows="2" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="sectionDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveSection">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="areaDialog" max-width="620">
      <v-card :title="editingAreaId ? 'Bereich bearbeiten' : 'Bereich anlegen'">
        <v-card-text>
          <v-text-field v-model="areaForm.name" label="Name" :rules="[requiredRule]" />
          <v-select v-model="areaForm.area_type" label="Bereichstyp" :items="areaTypeOptions" item-title="title" item-value="value" />
          <v-text-field v-model.number="areaForm.position" label="Ebene / Zeile" type="number" min="1" max="100" :rules="[positiveRule]" />
          <v-select v-model="areaForm.width" label="Breite" :items="[{ value: 'full', title: 'Volle Spaltenbreite' }, { value: 'half', title: 'Halbe Spaltenbreite' }]" hint="Zwei halbe Bereiche können dieselbe Ebene links und rechts belegen." persistent-hint />
          <v-select v-if="areaForm.width === 'half'" v-model="areaForm.side" label="Seite" :items="[{ value: 'left', title: 'Links' }, { value: 'right', title: 'Rechts' }]" />
          <v-row v-if="areaForm.area_type === 'device_rows'">
            <v-col cols="6"><v-text-field v-model.number="areaForm.rows" label="Reihen" type="number" min="1" clearable /></v-col>
            <v-col cols="6"><v-text-field v-model.number="areaForm.modules_per_row" label="Module je Reihe" type="number" min="1" clearable /></v-col>
          </v-row>
          <v-textarea v-model="areaForm.description" label="Beschreibung (optional)" rows="2" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="areaDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveArea">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="meterPlacementDialog" max-width="620">
      <v-card title="Zähler im Zählerschrank platzieren" prepend-icon="mdi-meter-electric-outline">
        <v-card-text>
          <v-autocomplete
            v-model="meterPlacementSourceKey"
            :items="meterOptions"
            item-title="title"
            item-value="value"
            label="Zähler oder Zähler-Asset"
            hint="Verbrauchszähler werden bevorzugt. Nicht verknüpfte Assets vom Typ Zähler können direkt platziert werden."
            persistent-hint
          >
            <template #item="{ props: itemProps, item }">
              <v-list-item v-bind="itemProps" :subtitle="item.raw.subtitle" />
            </template>
          </v-autocomplete>
          <v-select v-model="meterPlacementAreaId" :items="meterAreaOptions" item-title="title" item-value="id" label="Zählerfeld" />
          <v-text-field v-model.number="meterPlacementPosition" type="number" min="1" max="100" label="Position im Feld" />
          <v-alert type="info" variant="tonal" density="compact">
            Verbrauchszähler zeigen Ablesungen und Livewerte. Nicht verknüpfte Assets vom Typ „Zähler“ können ebenfalls direkt platziert werden.
          </v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="meterPlacementDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!meterPlacementSourceKey || !meterPlacementAreaId" @click="saveMeterPlacement">Platzieren</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="cabinetComponentDialog" max-width="720">
      <v-card :title="editingCabinetComponentId ? 'Schrankkomponente bearbeiten' : 'Schrankkomponente platzieren'" prepend-icon="mdi-call-split">
        <v-card-text>
          <v-text-field v-model="cabinetComponentForm.name" label="Bezeichnung" :rules="[requiredRule]" />
          <v-select
            v-model="cabinetComponentForm.component_type"
            label="Komponententyp"
            :items="cabinetComponentTypeOptions"
            item-title="title"
            item-value="value"
            @update:model-value="applyCabinetComponentPhaseSuggestion"
          />
          <v-select v-if="structuredLayout" v-model="cabinetComponentForm.area_id" label="Gerätebereich" :items="deviceAreaOptions" item-title="title" item-value="id" />
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">Diese Komponente gehört zur einfachen Reihenaufteilung und ist kein Asset.</v-alert>
          <v-row>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.row_number" label="Reihe" type="number" min="1" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.start_position" label="Startposition (TE)" type="number" min="1" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.module_width"  :label="cabinetComponentForm.component_type === 'busbar' ? 'Überspannte TE' : 'Breite (TE)'" type="number" min="1" /></v-col>
          </v-row>
          <v-select
            v-model="cabinetComponentForm.phases"
            label="Leiter / Potentiale"
            :items="phaseOptions"
            item-title="title"
            item-value="value"
            multiple
            chips
            closable-chips
            hint="Diese Leiter stehen anschließend bei der Verkabelung zur Verfügung."
            persistent-hint
          />
          <v-row v-if="cabinetComponentForm.component_type === 'busbar' || cabinetComponentForm.component_type === 'neutral_rail'">
            <v-col cols="12" :sm="cabinetComponentForm.component_type === 'busbar' ? 8 : 12">
              <v-select
                v-model="cabinetComponentForm.linked_rcd_device_id"
                label="Zugehöriger FI/RCD"
                :items="rcdOptions"
                item-title="title"
                item-value="id"
                clearable
                hint="Sicherungen unter der Sammelschiene übernehmen diese FI-Gruppe automatisch."
                persistent-hint
              />
            </v-col>
            <v-col v-if="cabinetComponentForm.component_type === 'busbar'" cols="12" sm="4">
              <v-select
                v-model="cabinetComponentForm.start_phase"
                label="Startphase"
                :items="phaseOptions.filter((item) => item.value === 'L1' || item.value === 'L2' || item.value === 'L3')"
                item-title="title"
                item-value="value"
              />
            </v-col>
          </v-row>
          <v-alert v-if="cabinetComponentForm.component_type === 'busbar'" type="info" variant="tonal" density="compact" class="mb-3">
            Die Breite beschreibt die überspannten TE. Die ausgewählten Phasen werden ab der Startphase wiederholt, zum Beispiel L1 – L2 – L3 – L1.
          </v-alert>
          <v-alert v-if="cabinetComponentForm.component_type === 'neutral_rail'" type="info" variant="tonal" density="compact" class="mb-3">
            Diese N-Schiene wird der ausgewählten FI-Gruppe zugeordnet. Einzelne Klemmen müssen nicht gepflegt werden.
          </v-alert>
          <v-row>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.rated_current_a" label="Bemessungsstrom (A)" type="number" min="1" clearable /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.max_cross_section_mm2" label="Max. Querschnitt (mm²)" type="number" min="0" step="0.1" clearable /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="cabinetComponentForm.outgoing_connections" label="Abgänge" type="number" min="1" clearable /></v-col>
          </v-row>
          <v-textarea v-model="cabinetComponentForm.description" label="Beschreibung (optional)" rows="2" />
          <v-textarea v-model="cabinetComponentForm.notes" label="Notizen (optional)" rows="2" />
          <v-alert type="info" variant="tonal" density="compact">
            Verteilerblöcke, Sammelschienen und Klemmen sind interne Schrankobjekte. Nach dem Speichern können sie als Quelle oder Ziel einer elektrischen Verbindung ausgewählt werden.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="cabinetComponentDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveCabinetComponent">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="assetPlacementDialog" max-width="620">
      <v-card title="DIN-Hutschienengerät platzieren" prepend-icon="mdi-memory">
        <v-card-text>
          <v-autocomplete
            v-model="assetPlacementAssetId"
            label="Asset"
            :items="assetPlacementOptions"
            item-title="title"
            item-value="id"
            :disabled="Boolean(assetPlacements.find((item) => item.asset_id === assetPlacementAssetId))"
            @update:model-value="applySelectedAssetWidth"
          />
          <v-select v-if="structuredLayout" v-model="assetPlacementForm.area_id" label="Gerätebereich" :items="deviceAreaOptions" item-title="title" item-value="id" />
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">Die Platzierung erfolgt direkt über Reihe und TE der einfachen Aufteilung.</v-alert>
          <v-row>
            <v-col cols="4"><v-text-field v-model.number="assetPlacementForm.row_number" label="Reihe" type="number" min="1" /></v-col>
            <v-col cols="4"><v-text-field v-model.number="assetPlacementForm.start_position" label="Startmodul" type="number" min="1" /></v-col>
            <v-col cols="4"><v-text-field v-model.number="assetPlacementForm.module_width" label="Breite TE" type="number" min="1" readonly /></v-col>
          </v-row>
          <v-alert type="info" variant="tonal" density="compact">Die TE-Breite wird direkt am Asset oder ersatzweise aus Produkt bzw. Asset-Typ übernommen. Ein als „primäre Live-Anzeige“ zugeordneter HA-Wert erscheint direkt im Schrank.</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="assetPlacementDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveAssetPlacement">Platzieren</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="placementDialog" max-width="620">
      <v-card title="Schutzgerät platzieren">
        <v-card-text>
          <v-select v-model="placementDeviceId" label="Schutzgerät" :items="deviceOptions" item-title="title" item-value="id" />
          <v-select v-if="structuredLayout" v-model="placementForm.area_id" label="Gerätebereich" :items="deviceAreaOptions" item-title="title" item-value="id" />
          <v-row>
            <v-col cols="4"><v-text-field v-model.number="placementForm.row_number" label="Reihe" type="number" min="1" clearable /></v-col>
            <v-col cols="4"><v-text-field v-model.number="placementForm.start_position" label="Startmodul" type="number" min="1" clearable /></v-col>
            <v-col cols="4"><v-text-field v-model.number="placementForm.module_width" label="Breite TE" type="number" min="1" readonly hint="Wird aus Asset, Asset-Typ oder DIN-Produkt übernommen." persistent-hint /></v-col>
          </v-row>
          <v-row>
            <v-col cols="12" sm="6">
              <v-select
                v-model="placementForm.assigned_rcd_id"
                label="FI/RCD (optional)"
                :items="rcdOptions"
                item-title="title"
                item-value="id"
                clearable
                hint="Leer lassen, um die Zuordnung der Sammelschiene zu übernehmen."
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="placementForm.neutral_rail_id"
                label="N-Schiene (optional)"
                :items="neutralRailOptions"
                item-title="title"
                item-value="id"
                clearable
                hint="Leer lassen, um die N-Schiene der FI-Gruppe zu übernehmen."
                persistent-hint
              />
            </v-col>
          </v-row>
          <v-alert type="info" variant="tonal" density="compact">
            {{ structuredLayout
              ? 'Alle drei Positionswerte können leer bleiben, wenn nur der Bereich bekannt ist.'
              : 'Reihe, Startmodul und Breite legen die Position in der einfachen Reihenaufteilung fest.' }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="placementDeviceId"
            variant="text"
            prepend-icon="mdi-pencil"
            :to="`/electrical/protective-devices/${placementDeviceId}/edit`"
          >
            Technische Daten
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="placementDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="saving" @click="savePlacement">Platzieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.layout-page { max-width: 1920px; }
h1 { font-size: clamp(1.6rem, 4vw, 2.2rem); }
.layout-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; align-items: start; }
.section-card { min-width: 0; }
.area-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.area-card { overflow: hidden; grid-column: span 2; }
.area-card.area-half { grid-column: span 1; }
@media (max-width: 900px) { .area-card.area-half { grid-column: span 2; } .layout-grid { grid-template-columns: minmax(0, 1fr); } }
.area-placeholder { min-height: 72px; display: grid; place-items: center; border: 1px dashed rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 8px; }
.module-scroll { overflow-x: auto; padding-bottom: 6px; }
.module-board { display: grid; gap: 4px; width: 100%; align-items: stretch; grid-template-rows: auto minmax(132px, auto) auto; }
.module-cell { grid-row: 1; min-width: 48px; text-align: center; font-size: 0.7rem; opacity: 0.65; border-bottom: 1px solid currentColor; }
.module-drop-cell { grid-row: 2 / span 2; min-height: 150px; border: 2px dashed transparent; border-radius: 6px; transition: background-color 120ms ease, border-color 120ms ease; }
.module-board.is-dragging .module-drop-cell { border-color: rgba(var(--v-theme-primary), 0.35); background: rgba(var(--v-theme-primary), 0.06); }
.module-board.is-dragging .module-device { pointer-events: none; opacity: 0.72; }
.module-board.is-dragging .drop-target-valid { border-color: rgb(var(--v-theme-success)); background: rgba(var(--v-theme-success), 0.2); }
.module-board.is-dragging .drop-target-invalid { border-color: rgb(var(--v-theme-error)); background: rgba(var(--v-theme-error), 0.2); }
.module-device { grid-row: 2; min-width: 0; z-index: 2; overflow: hidden; cursor: pointer; border-width: 2px; }
.module-device-title { padding: 10px 8px 4px; line-height: 1.2; min-height: 2.8rem; overflow: hidden; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; word-break: normal; overflow-wrap: break-word; hyphens: auto; }
.module-compact-value { padding: 0 8px 8px; font-size: 0.78rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.module-board.compact-view .module-device :deep(.v-card-subtitle),
.module-board.compact-view .module-device :deep(.v-card-text),
.module-board.compact-view .module-device-actions { display: none; }
.module-board.compact-view .module-device { min-height: 92px; }
.cabinet-legend { display: flex; flex-wrap: wrap; gap: 8px; }
.legend-item { display: inline-flex; align-items: center; min-height: 30px; padding: 4px 10px; border-radius: 999px; border: 2px solid transparent; font-size: 0.75rem; font-weight: 700; }
.cabinet-type-fuse, .cabinet-type-mcb { border-color: #607d8b !important; background: rgba(96, 125, 139, 0.16) !important; }
.cabinet-type-rcd { border-color: #3949ab !important; background: rgba(57, 73, 171, 0.16) !important; }
.cabinet-type-rcbo { border-color: #7e57c2 !important; background: rgba(126, 87, 194, 0.16) !important; }
.cabinet-type-spd { border-color: #ef6c00 !important; background: rgba(239, 108, 0, 0.16) !important; }
.cabinet-type-smart-meter { border-color: #00897b !important; background: rgba(0, 137, 123, 0.16) !important; }
.cabinet-type-electric-meter { border-color: #00838f !important; background: rgba(0, 131, 143, 0.16) !important; }
.cabinet-type-impulse-switch { border-color: #039be5 !important; background: rgba(3, 155, 229, 0.16) !important; }
.cabinet-type-busbar { border-color: #f9a825 !important; background: rgba(249, 168, 37, 0.18) !important; }
.cabinet-type-neutral { border-color: #1565c0 !important; background: rgba(21, 101, 192, 0.14) !important; }
.cabinet-type-pe { border-color: #2e7d32 !important; background: rgba(46, 125, 50, 0.14) !important; }
.cabinet-type-passive, .cabinet-type-asset { border-color: #757575 !important; background: rgba(117, 117, 117, 0.12) !important; }
.module-device-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(28px, 1fr)); width: 100%; gap: 0; }
.module-device-actions :deep(.v-btn) { min-width: 28px; width: 100%; }
.layout-summary { position: sticky; top: 8px; z-index: 5; backdrop-filter: blur(8px); }
.summary-metrics { display: flex; flex-wrap: wrap; gap: 8px; }
.device-meta-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; flex-wrap: wrap; }
.has-group-warning { outline: 2px solid rgba(var(--v-theme-warning), 0.65); }
.cabinet-component-card { border-style: dashed; }
.busbar-card { min-height: 34px; z-index: 3; border-style: solid; border-width: 2px; background: rgba(var(--v-theme-primary), 0.12); }
.busbar-card :deep(.v-card-title) { padding-block: 4px; }
.busbar-card :deep(.v-card-text) { padding-top: 2px !important; padding-bottom: 4px !important; }
.busbar-phase-sequence { display: grid; grid-template-columns: repeat(auto-fit, minmax(24px, 1fr)); gap: 2px; font-weight: 700; text-align: center; }
.busbar-phase-sequence span { border-radius: 3px; background: rgba(var(--v-theme-primary), 0.14); padding: 1px 2px; }

.drag-ready { cursor: grab; }
.drag-ready:active, .drag-source { cursor: grabbing; }
.device-list { display: flex; flex-wrap: wrap; }
</style>

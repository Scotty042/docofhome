<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { assetApi } from '../services/assetApi'
import { homeAssistantApi } from '../services/homeAssistantApi'
import { buildHomeAssistantAssetDraft } from '../services/homeAssistantAssetDraft'
import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationOptions'
import {
  normalizeSelectedEntityIds,
  toggleSelectedEntity
} from '../services/homeAssistantSelection'
import { useSettingsStore } from '../stores/settings'
import type { Asset, AssetType, AssetWrite } from '../types/assets'
import type { Location } from '../types/locations'
import type {
  HomeAssistantAssetLink,
  HomeAssistantDevice,
  HomeAssistantEntity,
  HomeAssistantObjectType,
  HomeAssistantOverview,
  HomeAssistantSelectionMode
} from '../types/homeAssistant'

const settings = useSettingsStore()
const overview = ref<HomeAssistantOverview | null>(null)
const devices = ref<HomeAssistantDevice[]>([])
const entities = ref<HomeAssistantEntity[]>([])
const links = ref<HomeAssistantAssetLink[]>([])
const deviceTotal = ref(0)
const entityTotal = ref(0)
const devicePage = ref(1)
const entityPage = ref(1)
const devicePageSize = 50
const entityPageSize = 100
const loading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const activeTab = ref<'devices' | 'entities'>('devices')
const deviceSearch = ref('')
const entitySearch = ref('')
const areaFilter = ref<string | null>(null)
const domainFilter = ref<string | null>(null)
const availabilityFilter = ref<'all' | 'available' | 'unavailable'>('all')
const deviceClassFilter = ref<string | null>(null)
const unitFilter = ref<string | null>(null)
const selectedDeviceId = ref<string | null>(null)
const linkDialog = ref(false)
const linkObjectType = ref<HomeAssistantObjectType>('device')
const linkExternalId = ref('')
const linkObjectName = ref('')
const selectedAssetId = ref<string | null>(null)
const assetSearch = ref('')
const assetOptions = ref<Asset[]>([])
const assetLoading = ref(false)
const linkSaving = ref(false)
const createAssetDialog = ref(false)
const createAssetSaving = ref(false)
const createAssetLoading = ref(false)
const createAssetTypes = ref<AssetType[]>([])
const createAssetLocations = ref<Location[]>([])
const createAssetForm = ref<AssetWrite>({
  name: '', description: null, asset_type_id: '', product_id: null, location_id: null,
  serial_number: null, inventory_number: null, module_width: null, status: 'active', label_ids: []
})
const selectionDialog = ref(false)
const selectionLoading = ref(false)
const selectionSaving = ref(false)
const selectionEntities = ref<HomeAssistantEntity[]>([])
const selectionTotal = ref(0)
const selectionPage = ref(1)
const selectionPageSize = 100
const selectionSearch = ref('')
const selectionDomain = ref<string | null>(null)
const selectionSelectedOnly = ref(false)
const selectionDraftMode = ref<HomeAssistantSelectionMode>('all')
const selectionDraftIds = ref<Set<string>>(new Set())
let deviceTimer: ReturnType<typeof setTimeout> | undefined
let entityTimer: ReturnType<typeof setTimeout> | undefined
let assetTimer: ReturnType<typeof setTimeout> | undefined
let selectionTimer: ReturnType<typeof setTimeout> | undefined

const integrationEnabled = computed(() => Boolean(
  settings.configuration?.integrations.find((item) => item.kind === 'home_assistant')?.enabled
))
const areaOptions = computed(() => [
  { title: 'Alle Bereiche', value: null },
  ...(overview.value?.areas.map((area) => ({ title: area.name, value: area.area_id })) ?? [])
])
const domainOptions = computed(() => [
  { title: 'Alle Domains', value: null },
  ...(overview.value?.domains.map((domain) => ({ title: domain, value: domain })) ?? [])
])
const deviceClassOptions = computed(() => [
  { title: 'Alle Geräteklassen', value: null },
  ...(overview.value?.device_classes.map((value) => ({ title: value, value })) ?? [])
])
const unitOptions = computed(() => [
  { title: 'Alle Einheiten', value: null },
  ...(overview.value?.units.map((value) => ({ title: value, value })) ?? [])
])
const selectedDevice = computed(() => devices.value.find(
  (device) => device.device_id === selectedDeviceId.value
) ?? null)
const linkMap = computed(() => new Map(
  links.value.map((link) => [`${link.object_type}:${link.external_id}`, link])
))
const currentLink = computed(() => linkFor(linkObjectType.value, linkExternalId.value))
const linkedParentDevice = computed(() => {
  if (linkObjectType.value !== 'entity') return null
  const entity = entities.value.find((item) => item.entity_id === linkExternalId.value)
  if (!entity?.device_id) return null
  const link = linkFor('device', entity.device_id)
  return link ? { entity, link } : null
})
const entityHasParentDevice = computed(() => {
  if (linkObjectType.value !== 'entity') return false
  return Boolean(entities.value.find((item) => item.entity_id === linkExternalId.value)?.device_id)
})
const assetItems = computed(() => assetOptions.value.map((asset) => ({
  title: `${asset.jarvis_code} · ${asset.name}`,
  value: asset.id,
  subtitle: [asset.asset_type.name, asset.location?.name].filter(Boolean).join(' · ')
})))
const createAssetTypeItems = computed(() => createAssetTypes.value.map((type) => ({
  title: type.name, value: type.id
})))
const createAssetLocationItems = computed(() => createAssetLocations.value.map((location) => ({
  title: location.path, value: location.id
})))
const linkSource = computed<HomeAssistantDevice | HomeAssistantEntity | null>(() => {
  if (linkObjectType.value === 'device') {
    return devices.value.find((device) => device.device_id === linkExternalId.value) ?? null
  }
  return entities.value.find((entity) => entity.entity_id === linkExternalId.value) ?? null
})
const selectionDomainOptions = computed(() => [
  { title: 'Alle Domains', value: null },
  ...(overview.value?.domains.map((domain) => ({ title: domain, value: domain })) ?? [])
])
const filteredSelectionEntities = computed(() => selectionSelectedOnly.value
  ? selectionEntities.value.filter((entity) => selectionDraftIds.value.has(entity.entity_id))
  : selectionEntities.value
)
const devicePages = computed(() => Math.max(1, Math.ceil(deviceTotal.value / devicePageSize)))
const entityPages = computed(() => Math.max(1, Math.ceil(entityTotal.value / entityPageSize)))
const selectionPages = computed(() => Math.max(1, Math.ceil(selectionTotal.value / selectionPageSize)))
const selectionModeLabel = computed(() => (
  overview.value?.summary.selection_mode === 'selected'
    ? `${overview.value.summary.selected_entity_count} ausgewählt`
    : 'Alle Entitäten'
))

onMounted(async () => {
  if (!settings.configuration) {
    try {
      await settings.fetchConfiguration()
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'Einstellungen konnten nicht geladen werden.'
      return
    }
  }
  if (integrationEnabled.value) await refreshAll(false)
})

watch(deviceSearch, () => {
  devicePage.value = 1
  clearTimeout(deviceTimer)
  deviceTimer = setTimeout(() => void loadDevices(), 300)
})
watch([entitySearch, domainFilter, availabilityFilter, deviceClassFilter, unitFilter], () => {
  entityPage.value = 1
  clearTimeout(entityTimer)
  entityTimer = setTimeout(() => void loadEntities(), 300)
})
watch(areaFilter, () => {
  devicePage.value = 1
  entityPage.value = 1
  void loadDevices()
  if (activeTab.value === 'entities') void loadEntities()
})
watch(devicePage, () => void loadDevices())
watch(entityPage, () => {
  if (activeTab.value === 'entities') void loadEntities()
})
watch(activeTab, (tab) => {
  if (tab === 'entities' && entities.value.length === 0) void loadEntities()
})
watch([selectionSearch, selectionDomain], () => {
  if (!selectionDialog.value) return
  selectionPage.value = 1
  clearTimeout(selectionTimer)
  selectionTimer = setTimeout(() => void loadSelectionCandidates(), 300)
})
watch(selectionPage, () => {
  if (selectionDialog.value) void loadSelectionCandidates()
})
watch(integrationEnabled, (enabled) => {
  if (enabled && !overview.value) void refreshAll(false)
})
watch(assetSearch, () => {
  if (!linkDialog.value) return
  clearTimeout(assetTimer)
  assetTimer = setTimeout(() => void loadAssetOptions(), 300)
})

async function refreshAll(refresh = true) {
  loading.value = true
  error.value = null
  try {
    overview.value = await homeAssistantApi.overview(refresh)
    await Promise.all([
      loadDevices(false),
      loadLinks(),
      activeTab.value === 'entities' ? loadEntities(false) : Promise.resolve()
    ])
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Home Assistant konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadDevices(refresh = false) {
  if (!integrationEnabled.value) return
  try {
    const result = await homeAssistantApi.devices({
      search: deviceSearch.value || undefined,
      area_id: areaFilter.value || undefined,
      offset: (devicePage.value - 1) * devicePageSize,
      limit: devicePageSize,
      refresh,
      selection_scope: 'visible'
    })
    devices.value = result.items
    deviceTotal.value = result.total
    if (devicePage.value > devicePages.value) devicePage.value = devicePages.value
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Geräte konnten nicht geladen werden.'
  }
}

async function loadEntities(refresh = false) {
  if (!integrationEnabled.value) return
  try {
    const available = availabilityFilter.value === 'all'
      ? undefined
      : availabilityFilter.value === 'available'
    const result = await homeAssistantApi.entities({
      search: entitySearch.value || undefined,
      domain: domainFilter.value || undefined,
      device_id: selectedDeviceId.value || undefined,
      area_id: areaFilter.value || undefined,
      available,
      device_class: deviceClassFilter.value || undefined,
      unit: unitFilter.value || undefined,
      offset: (entityPage.value - 1) * entityPageSize,
      limit: entityPageSize,
      refresh,
      selection_scope: 'visible'
    })
    entities.value = result.items
    entityTotal.value = result.total
    if (entityPage.value > entityPages.value) entityPage.value = entityPages.value
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Entitäten konnten nicht geladen werden.'
  }
}

async function openSelectionDialog() {
  selectionDialog.value = true
  selectionLoading.value = true
  selectionSearch.value = ''
  selectionDomain.value = null
  selectionSelectedOnly.value = false
  selectionPage.value = 1
  error.value = null
  try {
    const selection = await homeAssistantApi.selection()
    selectionDraftMode.value = selection.mode
    selectionDraftIds.value = new Set(selection.entity_ids)
    await loadSelectionCandidates()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Entitätsauswahl konnte nicht geladen werden.'
    selectionDialog.value = false
  } finally {
    selectionLoading.value = false
  }
}

async function loadSelectionCandidates() {
  if (!selectionDialog.value) return
  selectionLoading.value = true
  try {
    const result = await homeAssistantApi.entities({
      search: selectionSearch.value.trim() || undefined,
      domain: selectionDomain.value || undefined,
      offset: (selectionPage.value - 1) * selectionPageSize,
      limit: selectionPageSize,
      selection_scope: 'all'
    })
    selectionEntities.value = result.items
    selectionTotal.value = result.total
    if (selectionPage.value > selectionPages.value) selectionPage.value = selectionPages.value
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Entitäten konnten nicht geladen werden.'
  } finally {
    selectionLoading.value = false
  }
}

function toggleSelection(entityId: string) {
  selectionDraftIds.value = toggleSelectedEntity(selectionDraftIds.value, entityId)
}

function selectFilteredEntities() {
  selectionDraftIds.value = new Set([
    ...selectionDraftIds.value,
    ...filteredSelectionEntities.value.map((entity) => entity.entity_id)
  ])
}

function clearFilteredEntities() {
  const filteredIds = new Set(
    filteredSelectionEntities.value.map((entity) => entity.entity_id)
  )
  selectionDraftIds.value = new Set(
    [...selectionDraftIds.value].filter((entityId) => !filteredIds.has(entityId))
  )
}

async function saveSelection() {
  selectionSaving.value = true
  error.value = null
  try {
    const saved = await homeAssistantApi.updateSelection({
      mode: selectionDraftMode.value,
      entity_ids: normalizeSelectedEntityIds(selectionDraftIds.value)
    })
    selectionDialog.value = false
    success.value = saved.mode === 'all'
      ? 'DocOfHome zeigt wieder alle Home-Assistant-Entitäten.'
      : `${saved.selected_count} Home-Assistant-Entitäten wurden ausgewählt.`
    await refreshAll(false)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Entitätsauswahl konnte nicht gespeichert werden.'
  } finally {
    selectionSaving.value = false
  }
}

async function loadLinks() {
  try {
    links.value = (await homeAssistantApi.links()).items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset-Zuordnungen konnten nicht geladen werden.'
  }
}

async function showDeviceEntities(device: HomeAssistantDevice) {
  selectedDeviceId.value = device.device_id
  entityPage.value = 1
  activeTab.value = 'entities'
  await loadEntities()
}

async function clearDeviceFilter() {
  selectedDeviceId.value = null
  entityPage.value = 1
  await loadEntities()
}

function linkFor(
  objectType: HomeAssistantObjectType,
  externalId: string
): HomeAssistantAssetLink | undefined {
  return linkMap.value.get(`${objectType}:${externalId}`)
}

async function openLinkDialog(
  objectType: HomeAssistantObjectType,
  externalId: string,
  objectName: string
) {
  linkObjectType.value = objectType
  linkExternalId.value = externalId
  linkObjectName.value = objectName
  const existingLink = linkFor(objectType, externalId)
  const entity = objectType === 'entity'
    ? entities.value.find((item) => item.entity_id === externalId)
    : null
  const parentDeviceLink = entity?.device_id
    ? linkFor('device', entity.device_id)
    : undefined
  selectedAssetId.value = existingLink?.asset_id ?? parentDeviceLink?.asset_id ?? null
  assetSearch.value = ''
  success.value = null
  linkDialog.value = true
  await loadAssetOptions()
}

async function loadAssetOptions() {
  assetLoading.value = true
  try {
    const result = await assetApi.list({
      page: 1,
      page_size: 50,
      search: assetSearch.value || undefined,
      sort_by: 'name',
      sort_order: 'asc'
    })
    assetOptions.value = result.items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Assets konnten nicht geladen werden.'
  } finally {
    assetLoading.value = false
  }
}


async function openCreateAssetDialog() {
  const source = linkSource.value
  if (!source) return
  createAssetDialog.value = true
  createAssetLoading.value = true
  error.value = null
  try {
    const [assetTypes, locationTree] = await Promise.all([
      assetApi.allAssetTypes(),
      locationApi.tree()
    ])
    createAssetTypes.value = assetTypes
    createAssetLocations.value = flattenLocationTree(locationTree)
    createAssetForm.value = buildHomeAssistantAssetDraft(
      linkObjectType.value, source, assetTypes, createAssetLocations.value
    )
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Asset-Stammdaten konnten nicht geladen werden.'
    createAssetDialog.value = false
  } finally {
    createAssetLoading.value = false
  }
}

async function createAndLinkAsset() {
  if (!createAssetForm.value.name.trim() || !createAssetForm.value.asset_type_id) return
  createAssetSaving.value = true
  error.value = null
  let created: Asset | null = null
  try {
    created = await assetApi.create({
      ...createAssetForm.value,
      name: createAssetForm.value.name.trim(),
      description: createAssetForm.value.description?.trim() || null,
      serial_number: createAssetForm.value.serial_number?.trim() || null,
      inventory_number: createAssetForm.value.inventory_number?.trim() || null
    })
    assetOptions.value = [created, ...assetOptions.value.filter((asset) => asset.id !== created?.id)]
    selectedAssetId.value = created.id
    const saved = await homeAssistantApi.upsertLink(
      linkObjectType.value, linkExternalId.value, created.id
    )
    replaceLink(saved)
    createAssetDialog.value = false
    linkDialog.value = false
    success.value = `${created.jarvis_code} · ${created.name} wurde angelegt und direkt verknüpft.`
  } catch (reason) {
    const detail = reason instanceof Error ? reason.message : 'Unbekannter Fehler'
    if (created) {
      createAssetDialog.value = false
      error.value = `${created.jarvis_code} · ${created.name} wurde angelegt, aber die Home-Assistant-Verknüpfung ist fehlgeschlagen: ${detail}. Das Asset ist im Auswahlfeld bereits markiert und kann dort erneut verknüpft werden.`
    } else {
      error.value = detail
    }
  } finally {
    createAssetSaving.value = false
  }
}

async function saveLink() {
  if (!selectedAssetId.value) return
  linkSaving.value = true
  error.value = null
  try {
    const saved = await homeAssistantApi.upsertLink(
      linkObjectType.value,
      linkExternalId.value,
      selectedAssetId.value
    )
    replaceLink(saved)
    success.value = `${linkObjectName.value} wurde dem Asset ${saved.asset_code} zugeordnet.`
    linkDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset-Zuordnung konnte nicht gespeichert werden.'
  } finally {
    linkSaving.value = false
  }
}

async function removeCurrentLink() {
  if (!currentLink.value) return
  linkSaving.value = true
  error.value = null
  try {
    await homeAssistantApi.removeLink(linkObjectType.value, linkExternalId.value)
    links.value = links.value.filter((link) => link.id !== currentLink.value?.id)
    success.value = `Die Asset-Zuordnung für ${linkObjectName.value} wurde entfernt.`
    linkDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset-Zuordnung konnte nicht entfernt werden.'
  } finally {
    linkSaving.value = false
  }
}

function replaceLink(saved: HomeAssistantAssetLink) {
  const index = links.value.findIndex((link) => (
    link.object_type === saved.object_type && link.external_id === saved.external_id
  ))
  if (index === -1) links.value.push(saved)
  else links.value.splice(index, 1, saved)
}

function formatState(entity: HomeAssistantEntity): string {
  return entity.unit ? `${entity.state} ${entity.unit}` : entity.state
}

function normalizedEntityIcon(icon: string | null): string {
  if (!icon) return 'mdi-access-point'
  return icon.startsWith('mdi:') ? icon.replace('mdi:', 'mdi-') : icon
}

function formatTimestamp(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '–'
}
</script>

<template>
  <v-container class="smart-home-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center ga-3 mb-6">
      <div>
        <h1>Smart Home</h1>
        <p class="text-medium-emphasis mb-0">
          Lies Geräte, Entitäten und aktuelle Zustände aus Home Assistant. DocOfHome sendet keine Schaltbefehle.
        </p>
      </div>
      <v-spacer />
      <v-chip
        v-if="overview"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-filter-check-outline"
      >
        {{ selectionModeLabel }}
      </v-chip>
      <v-btn
        variant="tonal"
        prepend-icon="mdi-format-list-checks"
        :disabled="!integrationEnabled"
        @click="openSelectionDialog"
      >
        Entitäten auswählen
      </v-btn>
      <v-btn
        color="primary"
        prepend-icon="mdi-refresh"
        :loading="loading"
        :disabled="!integrationEnabled"
        @click="refreshAll(true)"
      >
        Live aktualisieren
      </v-btn>
    </div>

    <v-alert
      v-if="!integrationEnabled"
      type="info"
      variant="tonal"
      class="mb-5"
      title="Home Assistant ist noch nicht aktiviert"
    >
      Hinterlege unter Einstellungen die interne Home-Assistant-URL und ein Long-Lived Access Token,
      aktiviere die Integration und führe dort den Verbindungstest aus.
    </v-alert>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-5" @click:close="error = null">
      {{ error }}
    </v-alert>
    <v-alert v-if="success" type="success" variant="tonal" closable class="mb-5" @click:close="success = null">
      {{ success }}
    </v-alert>

    <template v-if="integrationEnabled">
      <v-skeleton-loader v-if="loading && !overview" type="card, card, card, table" />

      <template v-else-if="overview">
        <v-alert
          v-if="overview.summary.warning"
          type="warning"
          variant="tonal"
          class="mb-5"
        >
          {{ overview.summary.warning }}
        </v-alert>

        <v-row class="mb-3">
          <v-col cols="12" sm="6" lg="3">
            <v-card prepend-icon="mdi-home-assistant" title="Home Assistant" height="100%">
              <v-card-text>
                <div class="text-h6">{{ overview.summary.location_name || 'Installation' }}</div>
                <div class="text-medium-emphasis">
                  Version {{ overview.summary.version || 'unbekannt' }}
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" lg="3">
            <v-card prepend-icon="mdi-devices" title="Geräte" height="100%">
              <v-card-text>
                <div class="text-h4">{{ overview.summary.visible_device_count }}</div>
                <div
                  v-if="overview.summary.selection_mode === 'selected'"
                  class="text-caption text-medium-emphasis"
                >
                  von {{ overview.summary.device_count }} insgesamt
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" lg="3">
            <v-card prepend-icon="mdi-access-point" title="Entitäten" height="100%">
              <v-card-text>
                <div class="text-h4">{{ overview.summary.visible_entity_count }}</div>
                <div
                  v-if="overview.summary.selection_mode === 'selected'"
                  class="text-caption text-medium-emphasis"
                >
                  von {{ overview.summary.entity_count }} insgesamt
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" lg="3">
            <v-card prepend-icon="mdi-link-variant" title="Asset-Zuordnungen" height="100%">
              <v-card-text class="text-h4">{{ links.length }}</v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-card>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="5">
                <v-text-field
                  v-if="activeTab === 'devices'"
                  v-model="deviceSearch"
                  label="Geräte durchsuchen"
                  prepend-inner-icon="mdi-magnify"
                  clearable
                  hide-details
                />
                <v-text-field
                  v-else
                  v-model="entitySearch"
                  label="Entitäten durchsuchen"
                  prepend-inner-icon="mdi-magnify"
                  clearable
                  hide-details
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="areaFilter"
                  label="Bereich"
                  :items="areaOptions"
                  hide-details
                />
              </v-col>
              <v-col v-if="activeTab === 'entities'" cols="12" md="2">
                <v-select
                  v-model="domainFilter"
                  label="Domain"
                  :items="domainOptions"
                  hide-details
                />
              </v-col>
              <v-col v-if="activeTab === 'entities'" cols="12" sm="6" md="3">
                <v-select v-model="deviceClassFilter" label="Geräteklasse" :items="deviceClassOptions" hide-details />
              </v-col>
              <v-col v-if="activeTab === 'entities'" cols="12" sm="6" md="3">
                <v-select v-model="unitFilter" label="Einheit" :items="unitOptions" hide-details />
              </v-col>
              <v-col v-if="activeTab === 'entities'" cols="12" md="2">
                <v-select
                  v-model="availabilityFilter"
                  label="Status"
                  :items="[
                    { title: 'Alle', value: 'all' },
                    { title: 'Verfügbar', value: 'available' },
                    { title: 'Nicht verfügbar', value: 'unavailable' }
                  ]"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-card-text>

          <v-tabs v-model="activeTab" color="primary">
            <v-tab value="devices">Geräte ({{ deviceTotal }})</v-tab>
            <v-tab value="entities">Entitäten ({{ entityTotal }})</v-tab>
          </v-tabs>

          <v-window v-model="activeTab">
            <v-window-item value="devices">
              <v-card-text>
                <v-alert v-if="devices.length === 0" type="info" variant="tonal">
                  Keine Geräte für die aktuelle Auswahl gefunden.
                </v-alert>
                <v-row v-else>
                  <v-col v-for="device in devices" :key="device.device_id" cols="12" md="6" xl="4">
                    <v-card variant="outlined" height="100%">
                      <v-card-title class="d-flex align-center ga-2">
                        <v-icon icon="mdi-devices" color="primary" />
                        <span class="text-truncate">{{ device.name }}</span>
                      </v-card-title>
                      <v-card-text>
                        <div class="d-flex flex-wrap ga-2 mb-3">
                          <v-chip v-if="device.area_name" size="small" prepend-icon="mdi-map-marker-outline">
                            {{ device.area_name }}
                          </v-chip>
                          <v-chip size="small" prepend-icon="mdi-access-point">
                            {{ device.entity_count }} Entitäten
                          </v-chip>
                          <v-chip v-if="device.disabled" size="small" color="warning" variant="tonal">
                            Deaktiviert
                          </v-chip>
                          <v-chip
                            v-if="linkFor('device', device.device_id)"
                            size="small"
                            :color="linkFor('device', device.device_id)?.asset_archived ? 'warning' : 'success'"
                            variant="tonal"
                            prepend-icon="mdi-link-variant"
                          >
                            {{ linkFor('device', device.device_id)?.asset_code }} ·
                            {{ linkFor('device', device.device_id)?.asset_name }}
                          </v-chip>
                        </div>
                        <div v-if="device.manufacturer"><strong>Hersteller:</strong> {{ device.manufacturer }}</div>
                        <div v-if="device.model"><strong>Modell:</strong> {{ device.model }}</div>
                        <div v-if="device.sw_version"><strong>Software:</strong> {{ device.sw_version }}</div>
                        <div class="text-caption text-medium-emphasis mt-2">{{ device.device_id }}</div>
                      </v-card-text>
                      <v-card-actions>
                        <v-btn
                          variant="text"
                          prepend-icon="mdi-link-variant"
                          @click="openLinkDialog('device', device.device_id, device.name)"
                        >
                          Asset zuordnen
                        </v-btn>
                        <v-spacer />
                        <v-btn
                          variant="tonal"
                          prepend-icon="mdi-format-list-bulleted"
                          @click="showDeviceEntities(device)"
                        >
                          Entitäten anzeigen
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
                <div v-if="devicePages > 1" class="d-flex justify-center mt-4">
                  <v-pagination v-model="devicePage" :length="devicePages" :total-visible="7" />
                </div>
              </v-card-text>
            </v-window-item>

            <v-window-item value="entities">
              <v-card-text>
                <v-alert
                  v-if="selectedDevice"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mb-4"
                >
                  <div class="d-flex align-center ga-2">
                    <span>Gefiltert nach Gerät: <strong>{{ selectedDevice.name }}</strong></span>
                    <v-spacer />
                    <v-btn size="small" variant="text" @click="clearDeviceFilter">Filter entfernen</v-btn>
                  </div>
                </v-alert>
                <v-alert v-if="entities.length === 0" type="info" variant="tonal">
                  Keine Entitäten für die aktuelle Auswahl gefunden.
                </v-alert>
                <v-list v-else lines="three" class="entity-list">
                  <v-list-item v-for="entity in entities" :key="entity.entity_id">
                    <template #prepend>
                      <v-avatar :color="entity.available ? 'primary' : 'error'" variant="tonal">
                        <v-icon :icon="normalizedEntityIcon(entity.icon)" />
                      </v-avatar>
                    </template>
                    <v-list-item-title class="d-flex flex-wrap align-center ga-2">
                      <span>{{ entity.name }}</span>
                      <v-chip size="x-small" variant="tonal">{{ entity.domain }}</v-chip>
                      <v-chip v-if="entity.disabled" size="x-small" color="warning" variant="tonal">
                        Deaktiviert
                      </v-chip>
                      <v-chip
                        v-if="linkFor('entity', entity.entity_id)"
                        size="x-small"
                        :color="linkFor('entity', entity.entity_id)?.asset_archived ? 'warning' : 'success'"
                        variant="tonal"
                        prepend-icon="mdi-link-variant"
                      >
                        {{ linkFor('entity', entity.entity_id)?.asset_code }} ·
                        {{ linkFor('entity', entity.entity_id)?.asset_name }}
                      </v-chip>
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{ entity.entity_id }}
                      <template v-if="entity.device_name"> · {{ entity.device_name }}</template>
                      <template v-if="entity.area_name"> · {{ entity.area_name }}</template>
                    </v-list-item-subtitle>
                    <v-list-item-subtitle>
                      Letzte Aktualisierung: {{ formatTimestamp(entity.last_updated) }}
                    </v-list-item-subtitle>
                    <template #append>
                      <div class="d-flex align-center ga-2 entity-actions">
                        <v-btn
                          icon="mdi-link-variant"
                          variant="text"
                          size="small"
                          aria-label="Entität einem Asset zuordnen"
                          title="Entität einem Asset zuordnen"
                          @click="openLinkDialog('entity', entity.entity_id, entity.name)"
                        />
                        <v-chip
                          :color="entity.available ? 'success' : 'error'"
                          variant="tonal"
                          class="state-chip"
                        >
                          {{ formatState(entity) }}
                        </v-chip>
                      </div>
                    </template>
                  </v-list-item>
                </v-list>
                <div v-if="entityPages > 1" class="d-flex justify-center mt-4">
                  <v-pagination v-model="entityPage" :length="entityPages" :total-visible="7" />
                </div>
              </v-card-text>
            </v-window-item>
          </v-window>
        </v-card>
      </template>
    </template>

    <v-dialog v-model="linkDialog" max-width="680">
      <v-card title="Home Assistant mit Asset verknüpfen" prepend-icon="mdi-link-variant">
        <v-card-text>
          <p class="mb-1"><strong>{{ linkObjectName }}</strong></p>
          <p class="text-caption text-medium-emphasis mb-4">{{ linkExternalId }}</p>
          <v-alert v-if="currentLink?.asset_archived" type="warning" variant="tonal" class="mb-4">
            Das aktuell verknüpfte Asset ist archiviert. Die historische Zuordnung bleibt sichtbar,
            kann aber nur auf ein aktives Asset geändert oder vollständig getrennt werden.
          </v-alert>
          <v-alert
            v-if="linkedParentDevice"
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Diese Entität gehört zum Home-Assistant-Gerät
            <strong>{{ linkedParentDevice.entity.device_name }}</strong>. Das Gerät ist bereits mit
            <strong>{{ linkedParentDevice.link.asset_code }} · {{ linkedParentDevice.link.asset_name }}</strong>
            verknüpft. Dieses Asset wurde deshalb automatisch vorgeschlagen; die Entität wird dort als
            dynamische Eigenschaft angezeigt.
          </v-alert>
          <v-alert
            v-else-if="linkObjectType === 'entity' && entityHasParentDevice"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Diese Entität gehört zu einem Home-Assistant-Gerät, das noch keinem Asset zugeordnet ist.
            Für ein physisches Gerät sollte zuerst das Gerät als Asset verknüpft werden. Die Entitäten
            werden anschließend als Eigenschaften desselben Assets zugeordnet.
          </v-alert>
          <v-autocomplete
            v-model="selectedAssetId"
            v-model:search="assetSearch"
            :items="assetItems"
            :loading="assetLoading"
            label="DocOfHome-Asset"
            placeholder="Name, DocOfHome-Code, Serien- oder Inventarnummer suchen"
            prepend-inner-icon="mdi-magnify"
            clearable
            no-filter
            hide-details="auto"
          >
            <template #item="{ props: itemProps, item }">
              <v-list-item v-bind="itemProps" :subtitle="item.raw.subtitle" />
            </template>
          </v-autocomplete>
          <v-alert type="info" variant="tonal" density="compact" class="mt-4">
            Ein physisches Home-Assistant-Gerät entspricht normalerweise einem DocOfHome-Asset.
            Sensoren, Messwerte und Schalter dieses Geräts werden als Home-Assistant-Eigenschaften
            am Asset angezeigt. Home Assistant selbst wird dabei nicht verändert.
          </v-alert>
        </v-card-text>
        <v-card-actions class="flex-wrap">
          <v-btn
            v-if="linkObjectType === 'device' || !entityHasParentDevice"
            variant="tonal"
            prepend-icon="mdi-package-variant"
            :disabled="createAssetLoading"
            @click="openCreateAssetDialog"
          >
            Neues Asset anlegen
          </v-btn>
          <v-btn
            v-if="currentLink"
            color="error"
            variant="text"
            prepend-icon="mdi-link-variant-off"
            :loading="linkSaving"
            @click="removeCurrentLink"
          >
            Zuordnung trennen
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="linkDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            :disabled="!selectedAssetId"
            :loading="linkSaving"
            @click="saveLink"
          >
            Zuordnung speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="createAssetDialog" max-width="760" persistent>
      <v-card title="Asset aus Home Assistant anlegen" prepend-icon="mdi-package-variant">
        <v-progress-linear v-if="createAssetLoading" indeterminate />
        <v-card-text>
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            Die erkannten Home-Assistant-Daten werden als Vorschlag übernommen. Das neue Asset wird
            nach dem Speichern sofort mit <strong>{{ linkObjectName }}</strong> verknüpft.
          </v-alert>
          <v-text-field v-model="createAssetForm.name" label="Asset-Name" maxlength="255" />
          <v-select
            v-model="createAssetForm.asset_type_id"
            :items="createAssetTypeItems"
            label="Asset-Typ"
            prepend-inner-icon="mdi-shape-outline"
          />
          <v-alert
            v-if="!createAssetLoading && createAssetTypes.length === 0"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Es ist noch kein aktiver Asset-Typ vorhanden. Lege zuerst einen Asset-Typ in den
            Stammdaten an.
            <template #append><v-btn variant="text" to="/master-data">Stammdaten</v-btn></template>
          </v-alert>
          <v-autocomplete
            v-model="createAssetForm.location_id"
            :items="createAssetLocationItems"
            label="Bereich oder Raum (optional)"
            clearable
            prepend-inner-icon="mdi-map-marker-outline"
          />
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="createAssetForm.serial_number" label="Seriennummer (optional)" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="createAssetForm.inventory_number" label="Inventarnummer (optional)" />
            </v-col>
          </v-row>
          <v-textarea v-model="createAssetForm.description" label="Beschreibung" rows="5" />
          <div class="text-caption text-medium-emphasis">
            Produkt, Labels, Bilder und weitere Details können anschließend in der Asset-Detailansicht ergänzt werden.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="createAssetSaving" @click="createAssetDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            :loading="createAssetSaving"
            :disabled="createAssetLoading || !createAssetForm.name.trim() || !createAssetForm.asset_type_id"
            @click="createAndLinkAsset"
          >
            Anlegen und verknüpfen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="selectionDialog" max-width="980" scrollable>
      <v-card prepend-icon="mdi-format-list-checks" title="Home-Assistant-Entitäten auswählen">
        <v-card-text>
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            Die Auswahl wird nur in DocOfHome gespeichert. Home Assistant und bestehende
            Asset-Zuordnungen werden nicht verändert.
          </v-alert>

          <v-radio-group v-model="selectionDraftMode" inline hide-details class="mb-4">
            <v-radio label="Alle Entitäten anzeigen" value="all" />
            <v-radio label="Nur ausgewählte Entitäten anzeigen" value="selected" />
          </v-radio-group>

          <v-row class="mb-2">
            <v-col cols="12" md="6">
              <v-text-field
                v-model="selectionSearch"
                label="Entitäten durchsuchen"
                prepend-inner-icon="mdi-magnify"
                clearable
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="selectionDomain"
                label="Domain"
                :items="selectionDomainOptions"
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6" md="3" class="d-flex align-center">
              <v-checkbox
                v-model="selectionSelectedOnly"
                label="Nur ausgewählte"
                hide-details
              />
            </v-col>
          </v-row>

          <div class="d-flex flex-wrap align-center ga-2 mb-3">
            <v-chip color="primary" variant="tonal">
              {{ selectionDraftIds.size }} ausgewählt
            </v-chip>
            <v-chip variant="tonal">
              {{ selectionTotal }} Treffer · Seite {{ selectionPage }}
            </v-chip>
            <v-spacer />
            <v-btn size="small" variant="text" @click="selectFilteredEntities">
              Sichtbare auswählen
            </v-btn>
            <v-btn size="small" variant="text" @click="clearFilteredEntities">
              Sichtbare abwählen
            </v-btn>
          </div>

          <v-skeleton-loader v-if="selectionLoading" type="list-item@8" />
          <v-alert
            v-else-if="filteredSelectionEntities.length === 0"
            type="info"
            variant="tonal"
          >
            Keine Entitäten für den aktuellen Filter gefunden.
          </v-alert>
          <v-list v-else class="selection-list" lines="two">
            <v-list-item
              v-for="entity in filteredSelectionEntities"
              :key="entity.entity_id"
              @click="toggleSelection(entity.entity_id)"
            >
              <template #prepend>
                <v-checkbox-btn
                  :model-value="selectionDraftIds.has(entity.entity_id)"
                  :aria-label="`${entity.name} auswählen`"
                  @click.stop="toggleSelection(entity.entity_id)"
                />
              </template>
              <v-list-item-title class="d-flex flex-wrap align-center ga-2">
                <span>{{ entity.name }}</span>
                <v-chip size="x-small" variant="tonal">{{ entity.domain }}</v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="selection-entity-id">
                {{ entity.entity_id }}
                <template v-if="entity.device_name"> · {{ entity.device_name }}</template>
                <template v-if="entity.area_name"> · {{ entity.area_name }}</template>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <div v-if="selectionPages > 1" class="d-flex justify-center mt-4">
            <v-pagination v-model="selectionPage" :length="selectionPages" :total-visible="7" />
          </div>

          <v-alert
            v-if="selectionDraftMode === 'selected' && selectionDraftIds.size === 0"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-4"
          >
            Mit dieser Einstellung zeigt die Smart-Home-Ansicht bewusst keine Entitäten oder Geräte.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" :disabled="selectionSaving" @click="selectionDialog = false">
            Abbrechen
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            :loading="selectionSaving"
            :disabled="selectionLoading"
            @click="saveSelection"
          >
            Auswahl speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.smart-home-page { max-width: 1500px; }
h1 { font-size: clamp(1.8rem, 4vw, 2.25rem); }
.entity-list { background: transparent; }
.state-chip { max-width: 240px; }
.entity-actions { min-width: 170px; justify-content: flex-end; }
.selection-list { max-height: 58vh; overflow-y: auto; }
.selection-entity-id { overflow-wrap: anywhere; }
@media (max-width: 700px) {
  .entity-actions { min-width: 0; flex-direction: column; align-items: flex-end; }
}
</style>

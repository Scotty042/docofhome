<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { readInventoryQuery, writeInventoryQuery } from '../services/inventoryNavigation'
import AssetDuplicateDialog from '../components/AssetDuplicateDialog.vue'
import { assetApi } from '../services/assetApi'
import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationOptions'
import type { Asset, AssetStatus, AssetType, Label, Location } from '../types/assets'

const router = useRouter()
const route = useRoute()
const initialState = readInventoryQuery(route.query)
const filtersOpen = ref(false)
const filterError = ref<string | null>(null)
let loadSequence = 0
const assets = ref<Asset[]>([])
const assetTypes = ref<AssetType[]>([])
const locations = ref<Location[]>([])
const labels = ref<Label[]>([])
const total = ref(0)
const pages = ref(0)
const page = ref(initialState.page)
const pageSize = ref(initialState.pageSize)
const search = ref(initialState.search)
const status = ref<AssetStatus | ''>(initialState.status)
const assetTypeId = ref(initialState.assetTypeId)
const locationId = ref(initialState.locationId)
const labelId = ref(initialState.labelId)
const sort = ref(initialState.sort)
const showArchived = ref(initialState.showArchived)
const loading = ref(true)
const error = ref<string | null>(null)
const duplicateOpen = ref(false)
const duplicateAsset = ref<Asset | null>(null)
let searchTimer: ReturnType<typeof setTimeout> | undefined

const statusItems = [
  { title: 'Alle Status', value: '' },
  { title: 'Aktiv', value: 'active' },
  { title: 'Inaktiv', value: 'inactive' },
  { title: 'Wartung', value: 'maintenance' },
  { title: 'Ausgemustert', value: 'retired' }
]
const sortItems = [
  { title: 'Name A–Z', value: 'name:asc' },
  { title: 'Name Z–A', value: 'name:desc' },
  { title: 'Neueste zuerst', value: 'created_at:desc' },
  { title: 'Zuletzt geändert', value: 'updated_at:desc' }
]
const statusText: Record<AssetStatus, string> = {
  active: 'Aktiv', inactive: 'Inaktiv', maintenance: 'Wartung', retired: 'Ausgemustert'
}
const statusColor: Record<AssetStatus, string> = {
  active: 'success', inactive: 'secondary', maintenance: 'warning', retired: 'error'
}

const activeFilterCount = computed(() => [status.value, assetTypeId.value, locationId.value, labelId.value, showArchived.value].filter(Boolean).length)
function detailLocation(asset: Asset) {
  return { path: `/assets/${asset.id}`, query: { return_to: route.fullPath, ...(asset.deleted_at ? { archived: '1' } : {}) } }
}
function resetFilters() {
  status.value = ''; assetTypeId.value = ''; locationId.value = ''; labelId.value = ''; showArchived.value = false
  reloadFromFirstPage()
}
async function updateLocation(resetPage = false) {
  if (resetPage) page.value = 1
  const query = writeInventoryQuery({ search: search.value, status: status.value, assetTypeId: assetTypeId.value, locationId: locationId.value, labelId: labelId.value, sort: sort.value, page: page.value, pageSize: pageSize.value, showArchived: showArchived.value })
  const next = router.resolve({ path: '/assets', query }).fullPath
  if (next === route.fullPath) await load()
  else await router.replace({ path: '/assets', query })
}
function restoreFromLocation() {
  const state = readInventoryQuery(route.query)
  search.value = state.search; status.value = state.status; assetTypeId.value = state.assetTypeId
  locationId.value = state.locationId; labelId.value = state.labelId; sort.value = state.sort
  page.value = state.page; pageSize.value = state.pageSize; showArchived.value = state.showArchived
}


async function load() {
  const sequence = ++loadSequence
  loading.value = true
  error.value = null
  const [sortBy, sortOrder] = sort.value.split(':') as [string, 'asc' | 'desc']
  try {
    const result = await assetApi.list({
      page: page.value,
      page_size: pageSize.value,
      search: (search.value || '').trim(),
      sort_by: sortBy,
      sort_order: sortOrder,
      include_deleted: showArchived.value,
      status: status.value,
      asset_type_id: assetTypeId.value,
      location_id: locationId.value,
      label_id: labelId.value
    })
    if (sequence !== loadSequence) return
    assets.value = result.items
    total.value = result.total
    pages.value = result.pages
  } catch (reason) {
    if (sequence === loadSequence) error.value = reason instanceof Error ? reason.message : 'Inventar konnte nicht geladen werden.'
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}


function openDuplicate(asset: Asset) {
  duplicateAsset.value = asset
  duplicateOpen.value = true
}

function reloadFromFirstPage() { void updateLocation(true) }
function scheduleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reloadFromFirstPage, 250)
}
watch(() => route.fullPath, () => {
  if (route.path === '/assets') { restoreFromLocation(); void load() }
})
onBeforeUnmount(() => { clearTimeout(searchTimer); loadSequence++ })

onMounted(async () => {
  try {
    const [types, locationPage, labelPage] = await Promise.all([
      assetApi.assetTypes(), locationApi.tree(), assetApi.labels()
    ])
    assetTypes.value = types.items
    locations.value = flattenLocationTree(locationPage)
    labels.value = labelPage.items
  } catch (reason) {
    filterError.value = reason instanceof Error ? reason.message : 'Filter konnten nicht geladen werden.'
  }
  await load()
})
</script>

<template>
  <v-container class="asset-container" fluid>
    <div class="home-page-header"><div><div class="home-eyebrow">ZUHAUSE / INVENTAR</div><h1>Alles an seinem Platz.</h1><p>Geräte und Installationen deines Zuhauses.</p></div><v-btn color="primary" prepend-icon="mdi-plus" :to="{ path: '/assets/new', query: { return_to: route.fullPath } }">Gerät erfassen</v-btn></div>
    <v-alert v-if="filterError" type="warning" variant="tonal" class="mb-4">{{ filterError }}</v-alert>
    <div class="home-filter-bar">
      <v-text-field v-model="search" label="Inventar durchsuchen" placeholder="Name, Typ oder Kennung" prepend-inner-icon="mdi-magnify" clearable hide-details class="home-search-input" maxlength="200" @update:model-value="scheduleSearch" />
      <v-btn variant="outlined" prepend-icon="mdi-filter-variant" :aria-expanded="filtersOpen" @click="filtersOpen = !filtersOpen">Filter<span v-if="activeFilterCount" class="ml-2">{{ activeFilterCount }}</span></v-btn>
      <v-select v-model="sort" label="Sortierung" :items="sortItems" hide-details class="inventory-sort" @update:model-value="reloadFromFirstPage" />
    </div>
    <v-expand-transition><v-card v-show="filtersOpen" class="mb-5 inventory-filters"><v-card-text><v-row dense>
      <v-col cols="12" sm="6" lg="3"><v-select v-model="status" label="Status" :items="statusItems" hide-details @update:model-value="reloadFromFirstPage"/></v-col>
      <v-col cols="12" sm="6" lg="3"><v-select v-model="assetTypeId" label="Typ" :items="[{ name: 'Alle Typen', id: '' }, ...assetTypes]" item-title="name" item-value="id" hide-details @update:model-value="reloadFromFirstPage"/></v-col>
      <v-col cols="12" sm="6" lg="3"><v-select v-model="locationId" label="Ort" :items="[{ name: 'Alle Orte', path: 'Alle Orte', id: '' }, ...locations]" item-title="path" item-value="id" hide-details @update:model-value="reloadFromFirstPage"/></v-col>
      <v-col cols="12" sm="6" lg="3"><v-select v-model="labelId" label="Label" :items="[{ name: 'Alle Labels', id: '' }, ...labels]" item-title="name" item-value="id" hide-details @update:model-value="reloadFromFirstPage"/></v-col>
    </v-row><div class="home-inline-actions mt-4"><v-switch v-model="showArchived" label="Archivierte einbeziehen" color="primary" hide-details inset @update:model-value="reloadFromFirstPage"/><v-spacer/><v-btn variant="text" @click="resetFilters">Filter zurücksetzen</v-btn><v-btn color="primary" variant="tonal" @click="filtersOpen = false">Fertig</v-btn></div></v-card-text></v-card></v-expand-transition>
    <div class="home-results-label d-flex align-center justify-space-between"><span>{{ total }} Gerät{{ total === 1 ? '' : 'e' }}<span v-if="activeFilterCount"> · {{ activeFilterCount }} Filter aktiv</span></span><v-btn v-if="activeFilterCount" size="small" variant="text" append-icon="mdi-close" @click="resetFilters">Filter löschen</v-btn></div>
    <v-alert v-if="showArchived" type="info" variant="tonal" class="mb-4">Archivierte Einträge bleiben als schreibgeschützte Datensätze erhalten.</v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}<template #append><v-btn variant="text" @click="load">Erneut versuchen</v-btn></template></v-alert>
    <v-card>
      <v-progress-linear v-if="loading" indeterminate color="primary" aria-label="Inventar wird geladen"/>
      <v-card-text v-if="!loading && !assets.length" class="home-empty"><v-icon icon="mdi-package-variant-closed" size="48"/><h2>{{ search || activeFilterCount ? 'Keine passenden Geräte' : 'Deine Hausakte beginnt hier.' }}</h2><p>{{ search || activeFilterCount ? 'Versuche einen anderen Suchbegriff oder setze die Filter zurück.' : 'Erfasse dein erstes Gerät und halte alle Informationen an einem Ort fest.' }}</p><v-btn v-if="search || activeFilterCount" variant="text" color="primary" class="mt-3" @click="search = ''; resetFilters()">Suche zurücksetzen</v-btn><v-btn v-else color="primary" class="mt-3" to="/assets/new">Gerät erfassen</v-btn></v-card-text>
      <div v-else class="d-none d-md-block"><v-table hover><thead><tr><th>Gerät</th><th>Typ</th><th>Ort</th><th>Status</th><th>Labels</th><th><span class="sr-only">Aktionen</span></th></tr></thead><tbody><tr v-for="asset in assets" :key="asset.id" :class="{ 'archived-row': asset.deleted_at }"><td><router-link :to="detailLocation(asset)" class="inventory-name-link"><v-avatar rounded="lg" size="44" color="surface-variant"><v-img v-if="asset.effective_image_url || asset.product_image_url" :src="asset.effective_image_url || asset.product_image_url || undefined" :alt="`Bild von ${asset.name}`" contain/><v-icon v-else icon="mdi-package-variant"/></v-avatar><span><strong>{{ asset.name }}</strong><small class="jarvis-code">{{ asset.jarvis_code }}</small></span></router-link></td><td>{{ asset.asset_type.name }}</td><td>{{ asset.location?.name || '–' }}</td><td><v-chip v-if="asset.deleted_at" color="secondary" size="small" variant="tonal">Archiviert</v-chip><v-chip v-else :color="statusColor[asset.status]" size="small" variant="tonal">{{ statusText[asset.status] }}</v-chip></td><td><v-chip v-for="label in asset.labels.slice(0,2)" :key="label.id" size="x-small" class="mr-1">{{ label.name }}</v-chip><span v-if="asset.labels.length > 2" class="text-caption">+{{ asset.labels.length - 2 }}</span></td><td class="text-right"><v-menu><template #activator="{ props }"><v-btn v-bind="props" icon="mdi-dots-horizontal" variant="text" :aria-label="`Aktionen für ${asset.name}`"/></template><v-list><v-list-item title="Gerät öffnen" :to="detailLocation(asset)" prepend-icon="mdi-open-in-new"/><v-list-item v-if="!asset.deleted_at" title="Duplizieren" prepend-icon="mdi-content-copy" @click="openDuplicate(asset)"/></v-list></v-menu></td></tr></tbody></v-table></div>
      <div class="d-md-none inventory-mobile-list"><article v-for="asset in assets" :key="asset.id" class="inventory-mobile-item" :class="{ 'archived-row': asset.deleted_at }"><router-link :to="detailLocation(asset)" class="inventory-mobile-link"><v-avatar rounded="lg" size="44" color="surface-variant"><v-img v-if="asset.effective_image_url || asset.product_image_url" :src="asset.effective_image_url || asset.product_image_url || undefined" :alt="`Bild von ${asset.name}`" contain/><v-icon v-else icon="mdi-package-variant"/></v-avatar><div><strong>{{ asset.name }}</strong><small>{{ asset.asset_type.name }} · {{ asset.location?.name || 'Kein Ort' }}</small><small class="jarvis-code">{{ asset.jarvis_code }}</small></div><v-icon icon="mdi-chevron-right" size="18"/></router-link><div class="inventory-mobile-meta"><v-chip size="x-small" :color="asset.deleted_at ? 'secondary' : statusColor[asset.status]">{{ asset.deleted_at ? 'Archiviert' : statusText[asset.status] }}</v-chip><v-btn v-if="!asset.deleted_at" icon="mdi-content-copy" variant="text" size="small" :aria-label="`${asset.name} duplizieren`" @click="openDuplicate(asset)"/></div></article></div>
      <v-divider v-if="total"/><v-card-actions v-if="total" class="inventory-pagination"><v-select v-model="pageSize" :items="[10,25,50]" label="Pro Seite" density="compact" hide-details class="inventory-page-size" @update:model-value="reloadFromFirstPage"/><v-pagination v-model="page" :length="pages" :total-visible="3" density="comfortable" aria-label="Inventarseiten" @update:model-value="updateLocation()"/></v-card-actions>
    </v-card>
    <AssetDuplicateDialog v-model="duplicateOpen" :asset="duplicateAsset" @saved="load"/>
  </v-container>
</template>

<style scoped>
.asset-container{max-width:1440px}.inventory-sort{flex:0 0 195px}.inventory-name-link{display:flex;align-items:center;gap:15px;color:inherit;text-decoration:none;min-height:78px;padding-block:10px}.inventory-name-link:hover strong{text-decoration:underline;color:rgb(var(--v-theme-primary))}.inventory-name-link strong{font-size:17px;line-height:1.3;display:block}.inventory-name-link small{display:block;margin-top:5px}.jarvis-code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:11px;color:var(--home-muted);letter-spacing:.5px}.archived-row{opacity:.75}.inventory-pagination{justify-content:space-between;gap:12px;padding:18px}.inventory-page-size{flex:0 0 110px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.inventory-mobile-item{padding:16px;border-bottom:1px solid var(--home-rule)}.inventory-mobile-link{display:flex;gap:12px;align-items:flex-start;color:inherit;text-decoration:none}.inventory-mobile-link>div:not(.v-avatar){flex:1;min-width:0}.inventory-mobile-link>.v-avatar{flex:0 0 44px}.inventory-mobile-link strong{font-size:17px;line-height:1.3;display:block;overflow-wrap:anywhere}.inventory-mobile-link small{display:block;font-size:12px;color:var(--home-muted);margin-top:5px;line-height:1.4}.inventory-mobile-link .jarvis-code{font-size:10px}.inventory-mobile-meta{display:flex;align-items:center;justify-content:space-between;padding-left:56px;margin-top:8px}.inventory-mobile-list:empty{display:none}
@media(max-width:599px){.inventory-sort{flex:1 1 160px}.inventory-pagination{padding:12px;gap:8px;justify-content:center}.inventory-page-size{flex:0 1 94px}.inventory-pagination :deep(.v-pagination__item){margin-inline:2px}.inventory-name-link strong{font-size:15px}}
</style>

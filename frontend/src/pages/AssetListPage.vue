<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AssetDuplicateDialog from '../components/AssetDuplicateDialog.vue'
import { assetApi } from '../services/assetApi'
import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationOptions'
import type { Asset, AssetStatus, AssetType, Label, Location } from '../types/assets'

const router = useRouter()
const assets = ref<Asset[]>([])
const assetTypes = ref<AssetType[]>([])
const locations = ref<Location[]>([])
const labels = ref<Label[]>([])
const total = ref(0)
const pages = ref(0)
const page = ref(1)
const pageSize = ref(10)
const search = ref('')
const status = ref<AssetStatus | ''>('')
const assetTypeId = ref('')
const locationId = ref('')
const labelId = ref('')
const sort = ref('name:asc')
const showArchived = ref(false)
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

function detailLocation(asset: Asset) {
  return asset.deleted_at ? { path: `/assets/${asset.id}`, query: { archived: '1' } } : `/assets/${asset.id}`
}

async function load() {
  loading.value = true
  error.value = null
  const [sortBy, sortOrder] = sort.value.split(':') as [string, 'asc' | 'desc']
  try {
    const result = await assetApi.list({
      page: page.value,
      page_size: pageSize.value,
      search: search.value.trim(),
      sort_by: sortBy,
      sort_order: sortOrder,
      include_deleted: showArchived.value,
      status: status.value,
      asset_type_id: assetTypeId.value,
      location_id: locationId.value,
      label_id: labelId.value
    })
    assets.value = result.items
    total.value = result.total
    pages.value = result.pages
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Assets konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}


function openDuplicate(asset: Asset) {
  duplicateAsset.value = asset
  duplicateOpen.value = true
}

function reloadFromFirstPage() {
  page.value = 1
  void load()
}

function scheduleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reloadFromFirstPage, 250)
}

watch(showArchived, reloadFromFirstPage)

onMounted(async () => {
  try {
    const [types, locationPage, labelPage] = await Promise.all([
      assetApi.assetTypes(), locationApi.tree(), assetApi.labels()
    ])
    assetTypes.value = types.items
    locations.value = flattenLocationTree(locationPage)
    labels.value = labelPage.items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Filter konnten nicht geladen werden.'
  }
  await load()
})
</script>

<template>
  <v-container class="asset-container pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Assets</h1>
        <p class="text-medium-emphasis mb-0">Inventar des digitalen Zuhauses verwalten.</p>
      </div>
      <div class="d-flex flex-wrap align-center ga-3">
        <v-switch
          v-model="showArchived"
          label="Archivierte anzeigen"
          color="primary"
          hide-details
          inset
        />
        <v-btn color="primary" prepend-icon="mdi-plus" to="/assets/new">Asset erfassen</v-btn>
      </div>
    </div>

    <v-alert v-if="showArchived" type="info" variant="tonal" class="mb-5">
      Archivierte Assets werden gemeinsam mit aktiven Einträgen angezeigt. Sie sind historische,
      schreibgeschützte Datensätze und werden mit einem Archiv-Symbol markiert.
    </v-alert>

    <v-card class="mb-5" title="Suchen und filtern" prepend-icon="mdi-filter-variant">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              label="Name, DocOfHome-Code oder Kennung suchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              @update:model-value="scheduleSearch"
            />
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-select
              v-model="status"
              label="Status"
              :items="statusItems"
              hide-details
              @update:model-value="reloadFromFirstPage"
            />
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-select
              v-model="assetTypeId"
              label="Typ"
              :items="[{ name: 'Alle Typen', id: '' }, ...assetTypes]"
              item-title="name"
              item-value="id"
              hide-details
              @update:model-value="reloadFromFirstPage"
            />
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-select
              v-model="locationId"
              label="Ort"
              :items="[{ name: 'Alle Orte', path: 'Alle Orte', id: '' }, ...locations]"
              item-title="path"
              item-value="id"
              hide-details
              @update:model-value="reloadFromFirstPage"
            />
          </v-col>
          <v-col cols="6" sm="6" md="2">
            <v-select
              v-model="labelId"
              label="Label"
              :items="[{ name: 'Alle Labels', id: '' }, ...labels]"
              item-title="name"
              item-value="id"
              hide-details
              @update:model-value="reloadFromFirstPage"
            />
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-select
              v-model="sort"
              label="Sortierung"
              :items="sortItems"
              hide-details
              @update:model-value="reloadFromFirstPage"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-5" closable>
      {{ error }}
    </v-alert>

    <v-card>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-card-text v-if="!loading && assets.length === 0" class="empty-state text-center py-12">
        <v-icon icon="mdi-package-variant-closed" size="56" color="secondary" />
        <h2 class="mt-3">Keine Assets gefunden</h2>
        <p class="text-medium-emphasis">Passe die Filter an oder erfasse das erste Asset.</p>
      </v-card-text>

      <div v-else class="d-none d-md-block">
        <v-table hover>
          <thead><tr><th>Name</th><th>Typ</th><th>Ort</th><th>Status</th><th>Labels</th><th /></tr></thead>
          <tbody>
            <tr
              v-for="asset in assets"
              :key="asset.id"
              class="asset-row"
              :class="{ 'archived-row': asset.deleted_at }"
              @click="router.push(detailLocation(asset))"
            >
              <td>
                <div class="d-flex align-center ga-2">
                  <v-avatar rounded="lg" size="38" color="surface-variant">
                    <v-img
                      v-if="asset.product_image_url"
                      :src="asset.product_image_url"
                      :alt="`Produktbild ${asset.name}`"
                      contain
                    />
                    <v-icon v-else icon="mdi-package-variant" />
                  </v-avatar>
                  <v-icon v-if="asset.deleted_at" icon="mdi-archive-outline" color="secondary" />
                  <div><strong>{{ asset.name }}</strong><div class="jarvis-code text-caption">{{ asset.jarvis_code }}</div></div>
                </div>
              </td>
              <td>{{ asset.asset_type.name }}</td>
              <td>{{ asset.location?.name || '–' }}</td>
              <td>
                <v-chip v-if="asset.deleted_at" color="secondary" size="small" variant="tonal">Archiviert</v-chip>
                <v-chip v-else :color="statusColor[asset.status]" size="small" variant="tonal">{{ statusText[asset.status] }}</v-chip>
              </td>
              <td><v-chip v-for="label in asset.labels.slice(0, 2)" :key="label.id" size="x-small" class="mr-1">{{ label.name }}</v-chip></td>
              <td class="text-right">
                <v-btn v-if="!asset.deleted_at" icon="mdi-content-copy" variant="text" aria-label="Asset duplizieren" title="Asset duplizieren" @click.stop="openDuplicate(asset)" />
                <v-btn icon="mdi-chevron-right" variant="text" :to="detailLocation(asset)" aria-label="Asset öffnen" title="Asset öffnen" @click.stop />
              </td>
            </tr>
          </tbody>
        </v-table>
      </div>

      <v-card-text class="d-md-none pa-3">
        <v-card
          v-for="asset in assets"
          :key="asset.id"
          class="mb-3"
          :class="{ 'archived-row': asset.deleted_at }"
          variant="tonal"
          :to="detailLocation(asset)"
        >
          <v-card-title class="d-flex align-center justify-space-between">
            <span class="d-flex align-center ga-2">
              <v-avatar rounded="lg" size="38" color="surface-variant">
                <v-img
                  v-if="asset.product_image_url"
                  :src="asset.product_image_url"
                  :alt="`Produktbild ${asset.name}`"
                  contain
                />
                <v-icon v-else icon="mdi-package-variant" />
              </v-avatar>
              <v-icon v-if="asset.deleted_at" icon="mdi-archive-outline" />{{ asset.name }}
            </span>
            <v-chip v-if="asset.deleted_at" color="secondary" size="small">Archiviert</v-chip>
            <v-chip v-else :color="statusColor[asset.status]" size="small">{{ statusText[asset.status] }}</v-chip>
          </v-card-title>
          <v-card-text>
            <div>{{ asset.asset_type.name }} · {{ asset.location?.name || 'Kein Ort' }}</div>
            <div class="jarvis-code text-caption mt-1">{{ asset.jarvis_code }}</div>
          </v-card-text>
          <v-card-actions v-if="!asset.deleted_at">
            <v-btn prepend-icon="mdi-content-copy" variant="text" @click.prevent.stop="openDuplicate(asset)">Duplizieren</v-btn>
          </v-card-actions>
        </v-card>
      </v-card-text>

      <v-divider v-if="total" />
      <v-card-actions v-if="total" class="flex-wrap justify-space-between px-4 py-3">
        <span class="text-body-2 text-medium-emphasis">{{ total }} Asset{{ total === 1 ? '' : 's' }}</span>
        <div class="d-flex align-center ga-3">
          <v-select v-model="pageSize" :items="[10, 25, 50]" density="compact" hide-details style="width: 90px" aria-label="Einträge pro Seite" @update:model-value="reloadFromFirstPage" />
          <v-pagination v-model="page" :length="pages" :total-visible="5" density="comfortable" @update:model-value="load" />
        </div>
      </v-card-actions>
    </v-card>

    <AssetDuplicateDialog
      v-model="duplicateOpen"
      :asset="duplicateAsset"
      @saved="load"
    />
  </v-container>
</template>

<style scoped>
.asset-container { max-width: 1440px; }
h1 { font-size: clamp(1.7rem, 4vw, 2.2rem); }
.asset-row { cursor: pointer; }
.archived-row { opacity: 0.72; }
.empty-state { min-height: 280px; }
.jarvis-code { color: rgb(var(--v-theme-primary)); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-weight: 700; }
</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { electricalApi } from '../services/electricalApi'
import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationOptions'
import {
  filterDistributionTree,
  flattenDistributionTree
} from '../services/electricalPresentation'
import type { Distribution, DistributionTreeNode, DistributionType } from '../types/electrical'
import type { Location } from '../types/locations'

const tree = ref<DistributionTreeNode[]>([])
const locationOrder = ref<Location[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const search = ref('')
const distributionType = ref<DistributionType | ''>('')
const locationId = ref('')
const showArchived = ref(false)

const typeItems = [
  { title: 'Alle Typen', value: '' },
  { title: 'Hauptverteilungen', value: 'main' },
  { title: 'Unterverteilungen', value: 'sub' }
]
const locations = computed(() => {
  const used = new Map<string, string>()
  flattenDistributionTree(tree.value).forEach(({ distribution }) => {
    used.set(distribution.asset.location_id, distribution.asset.location_path)
  })
  const ordered = locationOrder.value
    .filter((location) => used.has(location.id))
    .map((location) => ({ id: location.id, path: used.get(location.id) ?? location.path }))
  const known = new Set(ordered.map((location) => location.id))
  const fallback = [...used.entries()]
    .filter(([id]) => !known.has(id))
    .map(([id, path]) => ({ id, path }))
    .sort((left, right) => left.path.localeCompare(right.path, 'de'))
  return [...ordered, ...fallback]
})
const visibleRows = computed(() => flattenDistributionTree(
  filterDistributionTree(tree.value, search.value, distributionType.value)
).filter(({ distribution }) => !locationId.value || distribution.asset.location_id === locationId.value))
const distributionCount = computed(() => flattenDistributionTree(tree.value).length)
const deviceCount = computed(() => flattenDistributionTree(tree.value).reduce(
  (total, { distribution }) => total + distribution.direct_protective_device_count,
  0
))

function distributionLocation(distribution: Distribution) {
  return distribution.deleted_at
    ? { path: `/electrical/distributions/${distribution.id}`, query: { archived: '1' } }
    : `/electrical/distributions/${distribution.id}`
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [distributionTree, locationsTree] = await Promise.all([
      electricalApi.distributionTree(showArchived.value),
      locationApi.tree()
    ])
    tree.value = distributionTree
    locationOrder.value = flattenLocationTree(locationsTree)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Elektroverteilungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

watch(showArchived, () => void load())
onMounted(load)
</script>

<template>
  <v-container class="electrical-container pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Elektro</h1>
        <p class="text-medium-emphasis mb-0">
          Verteilungen und Schutzgeräte dokumentieren – vollständig offline.
        </p>
      </div>
      <div class="d-flex flex-wrap align-center ga-3">
        <v-btn variant="tonal" prepend-icon="mdi-source-branch" to="/electrical/topology">
          Versorgungswege
        </v-btn>
        <v-switch
          v-model="showArchived"
          label="Archivierte anzeigen"
          color="primary"
          hide-details
          inset
        />
        <v-btn color="primary" prepend-icon="mdi-plus" to="/electrical/distributions/new">
          Verteilung anlegen
        </v-btn>
      </div>
    </div>

    <v-alert v-if="showArchived" type="info" variant="tonal" class="mb-5">
      Archivierte Verteilungen werden zusammen mit aktiven Einträgen angezeigt und sind nur lesbar.
      Archivierte Schutzgeräte findest du gesammelt unter „Archiv“ im unteren Menübereich.
    </v-alert>

    <v-row class="mb-2">
      <v-col cols="6" sm="3">
        <v-card variant="tonal">
          <v-card-text>
            <div class="text-h5">{{ distributionCount }}</div>
            <div class="text-medium-emphasis">Verteilungen</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card variant="tonal">
          <v-card-text>
            <div class="text-h5">{{ deviceCount }}</div>
            <div class="text-medium-emphasis">aktive Sicherungs-/Schutzgeräte</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="mb-5" title="Suchen und filtern" prepend-icon="mdi-filter-variant">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="search"
              label="Bezeichnung, Asset, DocOfHome-Code oder Standort"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="6" md="3">
            <v-select
              v-model="distributionType"
              label="Typ"
              :items="typeItems"
              hide-details
            />
          </v-col>
          <v-col cols="6" md="3">
            <v-select
              v-model="locationId"
              label="Standort"
              :items="[{ id: '', path: 'Alle Standorte' }, ...locations]"
              item-title="path"
              item-value="id"
              hide-details
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-5" closable>
      {{ error }}
      <template #append><v-btn variant="text" @click="load">Erneut laden</v-btn></template>
    </v-alert>

    <v-card>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-card-text v-if="!loading && visibleRows.length === 0" class="text-center py-12">
        <v-icon icon="mdi-electric-switch" size="56" color="secondary" />
        <h2 class="mt-3">Keine Verteilungen gefunden</h2>
        <p class="text-medium-emphasis">
          Passe die Filter an oder dokumentiere die erste Verteilung.
        </p>
      </v-card-text>

      <div v-else class="d-none d-md-block">
        <v-table hover>
          <thead>
            <tr><th>Hierarchie</th><th>Asset</th><th>Standort</th><th>Kapazität</th><th /></tr>
          </thead>
          <tbody>
            <tr
              v-for="row in visibleRows"
              :key="row.distribution.id"
              :class="{ 'archived-row': row.distribution.deleted_at }"
            >
              <td>
                <div class="d-flex align-center" :style="{ paddingLeft: `${row.depth * 28}px` }">
                  <v-icon
                    :icon="row.distribution.deleted_at ? 'mdi-archive-outline' : row.distribution.distribution_type === 'main' ? 'mdi-electric-switch' : 'mdi-electric-switch-closed'"
                    color="secondary"
                    class="mr-2"
                  />
                  <div>
                    <div class="d-flex align-center ga-2">
                      <strong>{{ row.distribution.display_name }}</strong>
                      <v-chip v-if="row.distribution.deleted_at" size="x-small" variant="tonal">Archiviert</v-chip>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      {{ row.distribution.distribution_type === 'main' ? 'Hauptverteilung' : 'Unterverteilung' }}
                      · {{ row.distribution.direct_protective_device_count }} aktive Sicherungs-/Schutzgeräte
                    </div>
                  </div>
                </div>
              </td>
              <td>
                {{ row.distribution.asset.name }}
                <div class="jarvis-code text-caption">{{ row.distribution.asset.jarvis_code }}</div>
              </td>
              <td>{{ row.distribution.asset.location_path }}</td>
              <td>
                {{ row.distribution.rows ?? '?' }} × {{ row.distribution.modules_per_row ?? '?' }} Module
              </td>
              <td class="text-right">
                <v-btn
                  icon="mdi-chevron-right"
                  variant="text"
                  :to="distributionLocation(row.distribution)"
                  aria-label="Verteilung öffnen"
                  title="Verteilung öffnen"
                />
              </td>
            </tr>
          </tbody>
        </v-table>
      </div>

      <v-card-text class="d-md-none pa-3">
        <v-card
          v-for="row in visibleRows"
          :key="row.distribution.id"
          class="mb-3"
          :class="{ 'archived-row': row.distribution.deleted_at }"
          variant="tonal"
          :to="distributionLocation(row.distribution)"
          :style="{ marginLeft: `${Math.min(row.depth, 3) * 12}px` }"
        >
          <v-card-title class="d-flex align-center ga-2 text-wrap">
            <v-icon v-if="row.distribution.deleted_at" icon="mdi-archive-outline" />
            {{ row.distribution.display_name }}
            <v-chip v-if="row.distribution.deleted_at" size="x-small">Archiviert</v-chip>
          </v-card-title>
          <v-card-subtitle>{{ row.distribution.asset.jarvis_code }}</v-card-subtitle>
          <v-card-text>
            <div>{{ row.distribution.asset.location_path }}</div>
            <div class="text-medium-emphasis mt-1">
              {{ row.distribution.direct_subdistribution_count }} Unterverteilungen ·
              {{ row.distribution.direct_protective_device_count }} aktive Sicherungs-/Schutzgeräte
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<style scoped>
.electrical-container { max-width: 1440px; }
h1 { font-size: clamp(1.7rem, 4vw, 2.2rem); }
.archived-row { opacity: 0.72; }
.jarvis-code {
  color: rgb(var(--v-theme-primary));
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-weight: 700;
}
</style>

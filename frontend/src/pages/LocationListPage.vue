<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import LocationTreeItem from '../components/LocationTreeItem.vue'
import { LocationApiError, locationApi } from '../services/locationApi'
import {
  filterLocationTree,
  flattenLocationTree,
  locationTypeIcon,
  locationTypeItems,
  locationTypeLabel
} from '../services/locationPresentation'
import type { LocationTreeNode, LocationType } from '../types/locations'

const tree = ref<LocationTreeNode[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const errorStatus = ref<number | null>(null)
const search = ref('')
const typeFilter = ref<LocationType | ''>('')
const includeArchived = ref(false)

const filteredTree = computed(() => filterLocationTree(tree.value, search.value, typeFilter.value))
const mobileLocations = computed(() => flattenLocationTree(filteredTree.value))
const totalLocations = computed(() => flattenLocationTree(tree.value).length)
const unavailable = computed(() => errorStatus.value === 0 || (errorStatus.value ?? 0) >= 500)

async function load() {
  loading.value = true
  error.value = null
  errorStatus.value = null
  try {
    tree.value = await locationApi.tree(includeArchived.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bereiche konnten nicht geladen werden.'
    errorStatus.value = reason instanceof LocationApiError ? reason.status : 0
  } finally {
    loading.value = false
  }
}

watch(includeArchived, () => void load())
onMounted(load)
</script>

<template>
  <v-container class="location-container pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Bereiche & Räume</h1>
        <p class="text-medium-emphasis mb-0">
          Räumliche Struktur des Hauses und Zuordnung der Assets.
        </p>
      </div>
      <div class="d-flex flex-wrap ga-2">
        <v-btn variant="tonal" prepend-icon="mdi-wizard-hat" to="/locations/setup">
          Geführt einrichten
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" to="/locations/new">
          Bereich anlegen
        </v-btn>
      </div>
    </div>

    <v-card class="mb-5" title="Suchen und filtern" prepend-icon="mdi-filter-variant">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="search"
              label="Name oder vollständigen Pfad suchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="7" md="4">
            <v-select
              v-model="typeFilter"
              label="Location-Typ"
              :items="[{ title: 'Alle Typen', value: '' }, ...locationTypeItems]"
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="5" md="2" class="d-flex align-center">
            <v-switch v-model="includeArchived" label="Archivierte" hide-details color="primary" />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-alert v-if="error" :type="unavailable ? 'warning' : 'error'" variant="tonal" class="mb-5">
      <strong>{{ unavailable ? 'Backend nicht erreichbar' : 'Standorte konnten nicht geladen werden' }}</strong>
      <div>{{ error }}</div>
      <v-btn class="mt-2" size="small" variant="outlined" @click="load">Erneut versuchen</v-btn>
    </v-alert>

    <v-card v-if="!error">
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-card-text v-if="!loading && filteredTree.length === 0" class="text-center py-12">
        <v-icon icon="mdi-home-search-outline" size="56" color="secondary" />
        <h2 class="mt-3">Keine Bereiche gefunden</h2>
        <p class="text-medium-emphasis">
          {{ totalLocations ? 'Passe Suche oder Filter an.' : 'Lege den ersten Bereich im Haus an.' }}
        </p>
      </v-card-text>

      <template v-else-if="!loading">
        <div class="d-none d-md-block pa-4">
          <LocationTreeItem v-for="node in filteredTree" :key="node.id" :node="node" />
        </div>

        <v-card-text class="d-md-none pa-3">
          <v-card
            v-for="entry in mobileLocations"
            :key="entry.location.id"
            class="mb-3"
            variant="tonal"
            :to="`/locations/${entry.location.id}`"
            :style="{ marginLeft: `${Math.min(entry.depth * 14, 42)}px` }"
          >
            <v-card-title class="d-flex align-center ga-2">
              <v-icon :icon="locationTypeIcon(entry.location.location_type)" color="secondary" />
              <span class="flex-grow-1">{{ entry.location.name }}</span>
              <v-chip v-if="entry.location.deleted_at" color="warning" size="x-small">
                Archiviert
              </v-chip>
            </v-card-title>
            <v-card-text>
              <div class="text-caption text-medium-emphasis">
                {{ locationTypeLabel(entry.location.location_type) }} · {{ entry.location.path }}
              </div>
              <div class="mt-2">
                {{ entry.location.direct_asset_count }} direkt ·
                {{ entry.location.descendant_asset_count }} untergeordnet
              </div>
            </v-card-text>
          </v-card>
        </v-card-text>
      </template>
    </v-card>
  </v-container>
</template>

<style scoped>
.location-container { max-width: 1280px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.4rem); }
</style>

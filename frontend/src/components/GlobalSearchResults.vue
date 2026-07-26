<script setup lang="ts">
import { computed } from 'vue'

import type { SearchResponse, SearchResult, SearchResultType } from '../types/search'

const props = defineProps<{
  query: string
  loading: boolean
  error: string | null
  response: SearchResponse | null
  activeIndex: number
}>()

const emit = defineEmits<{
  select: [result: SearchResult]
  activate: [index: number]
}>()

const icons: Record<SearchResultType, string> = {
  asset: 'mdi-package-variant-closed',
  location: 'mdi-map-marker-outline',
  electrical_distribution: 'mdi-electric-switch',
  electrical_protective_device: 'mdi-toggle-switch',
  electrical_circuit: 'mdi-transmission-tower',
  wiki_page: 'mdi-book-open-page-variant',
  network_device: 'mdi-server-network',
  network_segment: 'mdi-ip-network-outline',
  consumption_meter: 'mdi-counter',
  document: 'mdi-file-document-outline'
}

const normalizedLength = computed(() => props.query.trim().length)
const indexedGroups = computed(() => {
  let index = 0
  return (props.response?.groups ?? []).map((group) => ({
    ...group,
    results: group.results.map((result) => ({ result, index: index++ }))
  }))
})
</script>

<template>
  <div class="global-search-results" role="listbox" aria-label="Globale Suchergebnisse">
    <v-card-text v-if="normalizedLength < 2" class="search-state text-medium-emphasis">
      <v-icon icon="mdi-form-textbox" class="mr-2" />
      Mindestens zwei Zeichen eingeben.
    </v-card-text>

    <template v-else>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-card-text v-if="loading" class="search-state text-medium-emphasis">
        Suche läuft …
      </v-card-text>

      <v-alert v-else-if="error" type="error" variant="tonal" density="compact" class="ma-3">
        {{ error }}
      </v-alert>

      <v-card-text v-else-if="response?.total === 0" class="search-state text-medium-emphasis">
        <v-icon icon="mdi-magnify" class="mr-2" />
        Keine Treffer für „{{ response.query }}“.
      </v-card-text>

      <template v-else-if="response">
        <template v-for="group in indexedGroups" :key="group.result_type">
          <template v-if="group.results.length">
            <v-list-subheader class="search-group-header">
              {{ group.label }}
              <v-chip size="x-small" variant="tonal" class="ml-2">{{ group.total }}</v-chip>
            </v-list-subheader>
            <v-list density="compact" lines="three" class="py-0">
              <v-list-item
                v-for="entry in group.results"
                :key="`${entry.result.result_type}-${entry.result.id}`"
                :prepend-icon="icons[entry.result.result_type]"
                :active="activeIndex === entry.index"
                :aria-selected="activeIndex === entry.index"
                role="option"
                class="search-result-item"
                @mouseenter="emit('activate', entry.index)"
                @focus="emit('activate', entry.index)"
                @click="emit('select', entry.result)"
              >
                <template #title>{{ entry.result.title }}</template>
                <template #subtitle>
                  <div>{{ entry.result.subtitle }}</div>
                  <div
                    v-if="entry.result.description"
                    class="result-description text-caption text-medium-emphasis"
                  >
                    {{ entry.result.description }}
                  </div>
                  <div class="d-flex flex-wrap ga-1 mt-1">
                    <v-chip
                      v-if="entry.result.archived"
                      size="x-small"
                      color="warning"
                      variant="tonal"
                      prepend-icon="mdi-archive-outline"
                    >
                      Archiviert
                    </v-chip>
                    <v-chip
                      v-for="field in entry.result.matched_fields.slice(0, 3)"
                      :key="field"
                      size="x-small"
                      variant="outlined"
                    >
                      {{ field }}
                    </v-chip>
                  </div>
                </template>
                <template #append>
                  <v-icon icon="mdi-arrow-right" size="small" />
                </template>
              </v-list-item>
            </v-list>
          </template>
        </template>
      </template>

      <v-card-text v-else class="search-state text-medium-emphasis">
        Die Suche startet nach einer kurzen Eingabepause.
      </v-card-text>
    </template>
  </div>
</template>

<style scoped>
.global-search-results {
  max-height: min(68vh, 620px);
  overflow-y: auto;
  overflow-x: hidden;
}

.search-state {
  display: flex;
  align-items: center;
  min-height: 72px;
}

.search-group-header {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.search-result-item {
  border-top: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * 0.55));
}

.result-description {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  white-space: normal;
}
</style>

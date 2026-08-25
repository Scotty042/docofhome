<script setup lang="ts">
import { ref, watch } from 'vue'

import { electricalApi } from '../services/electricalApi'
import type { ElectricalCircuit } from '../types/electrical'

const props = defineProps<{
  distributionId: string
  distributionDeleted: boolean
}>()

const circuits = ref<ElectricalCircuit[]>([])
const loading = ref(false)
const deleting = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const page = ref(1)
const pages = ref(0)
const total = ref(0)
const circuitToArchive = ref<ElectricalCircuit | null>(null)

async function loadCircuits() {
  if (!props.distributionId) return
  loading.value = true
  error.value = null
  try {
    const result = await electricalApi.listCircuits({
      distribution_id: props.distributionId,
      page: page.value,
      page_size: 25,
      search: search.value.trim() || undefined,
      sort_by: 'circuit_number',
      sort_order: 'asc'
    })
    circuits.value = result.items
    pages.value = result.pages
    total.value = result.total
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Stromkreise konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function applySearch() {
  page.value = 1
  void loadCircuits()
}

async function archiveCircuit() {
  if (!circuitToArchive.value) return
  deleting.value = true
  error.value = null
  try {
    await electricalApi.removeCircuit(circuitToArchive.value.id)
    circuitToArchive.value = null
    if (circuits.value.length === 1 && page.value > 1) page.value -= 1
    await loadCircuits()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Stromkreis konnte nicht archiviert werden.'
  } finally {
    deleting.value = false
  }
}

watch(() => props.distributionId, () => {
  page.value = 1
  void loadCircuits()
}, { immediate: true })
watch(page, () => void loadCircuits())
</script>

<template>
  <v-card class="mt-4" title="Stromkreise" prepend-icon="mdi-transmission-tower">
    <template v-if="!distributionDeleted" #append>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        :to="`/electrical/circuits/new?distribution=${distributionId}`"
      >
        Stromkreis
      </v-btn>
    </template>

    <v-card-text>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert
        type="info"
        variant="tonal"
        density="compact"
        icon="mdi-information-outline"
        class="mb-4"
        title="Was ist ein Stromkreis?"
      >
        Ein Stromkreis beschreibt einen Versorgungszweig, zum Beispiel „Steckdosen Küche“ oder
        „Licht Obergeschoss“. Er gehört zu dieser Verteilung, kann einem Schutzgerät zugeordnet
        werden und zeigt die darüber versorgten Assets. Er dokumentiert den Bestand, ersetzt aber
        keine elektrische Berechnung oder Prüfung.
      </v-alert>
      <v-text-field
        v-model="search"
        label="Stromkreise durchsuchen"
        prepend-inner-icon="mdi-magnify"
        clearable
        hide-details
        class="mb-4"
        @keyup.enter="applySearch"
        @click:clear="applySearch"
      />
      <v-skeleton-loader v-if="loading" type="list-item-two-line, list-item-two-line" />
      <div v-else-if="circuits.length === 0" class="text-center py-8">
        <v-icon icon="mdi-transmission-tower-off" size="46" color="secondary" />
        <h2 class="mt-3">Keine Stromkreise dokumentiert</h2>
        <p class="text-medium-emphasis mb-0">
          Stromkreise können auch ohne Schutzgerätezuordnung erfasst werden.
        </p>
      </div>
      <div v-else class="circuit-grid">
        <v-card v-for="circuit in circuits" :key="circuit.id" variant="outlined">
          <v-card-title class="text-wrap d-flex align-center ga-2">
            <v-chip v-if="circuit.circuit_number" size="small" color="primary" variant="tonal">
              {{ circuit.circuit_number }}
            </v-chip>
            <span>{{ circuit.name }}</span>
          </v-card-title>
          <v-card-subtitle v-if="circuit.protective_device_name" class="text-wrap">
            {{ circuit.protective_device_name }} · {{ circuit.protective_device_code }}
          </v-card-subtitle>
          <v-card-text v-if="circuit.description || circuit.notes">
            <p v-if="circuit.description" class="mb-1">{{ circuit.description }}</p>
            <p v-if="circuit.notes" class="text-medium-emphasis mb-0">{{ circuit.notes }}</p>
          </v-card-text>
          <v-card-actions>
            <v-btn
              variant="text"
              prepend-icon="mdi-open-in-new"
              :to="`/electrical/circuits/${circuit.id}`"
            >
              Öffnen
            </v-btn>
            <v-btn
              v-if="!distributionDeleted"
              variant="text"
              prepend-icon="mdi-pencil"
              :to="`/electrical/circuits/${circuit.id}/edit`"
            >
              Bearbeiten
            </v-btn>
            <v-spacer />
            <v-btn
              v-if="!distributionDeleted"
              icon="mdi-archive-arrow-down-outline"
              color="warning"
              variant="text"
              aria-label="Stromkreis archivieren"
              title="Stromkreis archivieren"
              @click="circuitToArchive = circuit"
            />
          </v-card-actions>
        </v-card>
      </div>

      <div v-if="pages > 1" class="d-flex flex-wrap align-center justify-space-between ga-3 mt-5">
        <span class="text-caption text-medium-emphasis">{{ total }} Stromkreise</span>
        <v-pagination v-model="page" :length="pages" density="comfortable" />
      </div>
    </v-card-text>

    <v-dialog
      :model-value="circuitToArchive !== null"
      max-width="520"
      @update:model-value="circuitToArchive = null"
    >
      <v-card title="Stromkreis archivieren?">
        <v-card-text>Die historische Dokumentation bleibt lesbar.</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="circuitToArchive = null">Abbrechen</v-btn>
          <v-btn color="warning" :loading="deleting" @click="archiveCircuit">Archivieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<style scoped>
.circuit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
  gap: 1rem;
}
</style>

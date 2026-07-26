<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NotesCard from '../components/NotesCard.vue'
import { assetApi } from '../services/assetApi'
import { electricalApi } from '../services/electricalApi'
import type { Asset, AssetStatus } from '../types/assets'
import type { ElectricalCircuit, ElectricalCircuitAsset } from '../types/electrical'

const route = useRoute()
const circuitId = computed(() => String(route.params.id))
const circuit = ref<ElectricalCircuit | null>(null)
const assignments = ref<ElectricalCircuitAsset[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const pickerOpen = ref(false)
const pickerLoading = ref(false)
const pickerError = ref<string | null>(null)
const search = ref('')
const assets = ref<Asset[]>([])
const assetPage = ref(1)
const assetPages = ref(0)
const assetTotal = ref(0)
const changingAssetId = ref<string | null>(null)
const assignmentToRemove = ref<ElectricalCircuitAsset | null>(null)

const linkedAssetIds = computed(() => new Set(assignments.value.map((item) => item.asset_id)))
const isReadOnly = computed(() => Boolean(circuit.value?.deleted_at))
const statusText: Record<AssetStatus, string> = {
  active: 'Aktiv',
  inactive: 'Inaktiv',
  maintenance: 'Wartung',
  retired: 'Ausgemustert'
}
const statusColor: Record<AssetStatus, string> = {
  active: 'success',
  inactive: 'secondary',
  maintenance: 'warning',
  retired: 'error'
}

function assignmentStatus(item: ElectricalCircuitAsset) {
  if (item.asset_deleted_at) return 'Archiviert'
  return statusText[item.asset_status as AssetStatus] ?? item.asset_status
}

function assignmentColor(item: ElectricalCircuitAsset) {
  if (item.asset_deleted_at) return 'warning'
  return statusColor[item.asset_status as AssetStatus] ?? 'secondary'
}

async function loadDetail() {
  loading.value = true
  error.value = null
  try {
    const [record, linked] = await Promise.all([
      electricalApi.getCircuit(circuitId.value, true),
      electricalApi.listCircuitAssets(circuitId.value)
    ])
    circuit.value = record
    assignments.value = linked
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Stromkreis konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadAssets() {
  pickerLoading.value = true
  pickerError.value = null
  try {
    const result = await assetApi.list({
      page: assetPage.value,
      page_size: 25,
      search: search.value.trim() || undefined,
      sort_by: 'name',
      sort_order: 'asc'
    })
    assets.value = result.items
    assetPages.value = result.pages
    assetTotal.value = result.total
  } catch (reason) {
    pickerError.value = reason instanceof Error
      ? reason.message
      : 'Assets konnten nicht geladen werden.'
  } finally {
    pickerLoading.value = false
  }
}

function openPicker() {
  pickerOpen.value = true
  assetPage.value = 1
  void loadAssets()
}

function applySearch() {
  assetPage.value = 1
  void loadAssets()
}

async function assignAsset(asset: Asset) {
  changingAssetId.value = asset.id
  pickerError.value = null
  try {
    const assigned = await electricalApi.assignCircuitAsset(circuitId.value, asset.id)
    assignments.value = [...assignments.value, assigned].sort((left, right) => (
      left.asset_name.localeCompare(right.asset_name, 'de')
    ))
  } catch (reason) {
    pickerError.value = reason instanceof Error
      ? reason.message
      : 'Asset konnte nicht zugeordnet werden.'
  } finally {
    changingAssetId.value = null
  }
}

async function removeAssignment() {
  if (!assignmentToRemove.value) return
  const item = assignmentToRemove.value
  changingAssetId.value = item.asset_id
  error.value = null
  try {
    await electricalApi.removeCircuitAsset(circuitId.value, item.asset_id)
    assignments.value = assignments.value.filter((entry) => entry.asset_id !== item.asset_id)
    assignmentToRemove.value = null
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Zuordnung konnte nicht entfernt werden.'
  } finally {
    changingAssetId.value = null
  }
}

onMounted(loadDetail)
</script>

<template>
  <v-container class="pa-4 pa-sm-6" fluid>
    <v-btn
      variant="text"
      prepend-icon="mdi-arrow-left"
      :to="circuit ? `/electrical/distributions/${circuit.distribution_id}` : '/electrical'"
      class="mb-3"
    >
      Zur Verteilung
    </v-btn>

    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
    <v-alert v-else-if="error && !circuit" type="error" variant="tonal">{{ error }}</v-alert>

    <template v-else-if="circuit">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="isReadOnly" type="warning" variant="tonal" class="mb-4">
        Dieser Stromkreis ist archiviert und bleibt als historische Dokumentation lesbar.
      </v-alert>

      <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
        <div>
          <div class="d-flex flex-wrap align-center ga-2">
            <v-chip v-if="circuit.circuit_number" color="primary" variant="tonal">
              {{ circuit.circuit_number }}
            </v-chip>
            <h1 class="text-h4">{{ circuit.name }}</h1>
          </div>
          <p class="text-medium-emphasis mt-2 mb-0">{{ circuit.distribution_name }}</p>
        </div>
        <v-btn
          v-if="!isReadOnly"
          color="primary"
          prepend-icon="mdi-pencil"
          :to="`/electrical/circuits/${circuit.id}/edit`"
        >
          Bearbeiten
        </v-btn>
      </div>

      <v-alert
        type="info"
        variant="tonal"
        icon="mdi-information-outline"
        class="mb-5"
        title="Was bildet dieser Stromkreis ab?"
      >
        Hier wird ein einzelner Versorgungszweig dokumentiert: seine Verteilung, das optionale
        Schutzgerät und die daran versorgten Assets. So lässt sich später vom Gerät bis zur
        Einspeisung zurückverfolgen, wo es angeschlossen ist. Leitungsberechnung, Selektivität und
        fachliche Prüfung bleiben außerhalb von DocOfHome.
      </v-alert>

      <v-row>
        <v-col cols="12" md="5">
          <v-card title="Stromkreis" prepend-icon="mdi-transmission-tower" height="100%">
            <v-list>
              <v-list-item title="Verteilung" :subtitle="circuit.distribution_name" />
              <v-list-item
                title="Schutzgerät"
                :subtitle="circuit.protective_device_name
                  ? `${circuit.protective_device_name} · ${circuit.protective_device_code}`
                  : 'Nicht zugeordnet'"
              />
              <v-list-item v-if="circuit.description" title="Beschreibung">
                <template #subtitle><span class="text-wrap">{{ circuit.description }}</span></template>
              </v-list-item>
              <v-list-item v-if="circuit.notes" title="Notizen">
                <template #subtitle><span class="text-wrap">{{ circuit.notes }}</span></template>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>

        <v-col cols="12" md="7">
          <v-card title="Zugeordnete Assets" prepend-icon="mdi-power-plug-outline" height="100%">
            <template v-if="!isReadOnly" #append>
              <v-btn color="primary" prepend-icon="mdi-link-plus" @click="openPicker">
                Asset zuordnen
              </v-btn>
            </template>
            <v-card-text>
              <div v-if="assignments.length === 0" class="text-center py-7">
                <v-icon icon="mdi-power-plug-off-outline" size="44" color="secondary" />
                <h2 class="text-h6 mt-2">Noch keine Assets zugeordnet</h2>
                <p class="text-medium-emphasis mb-0">
                  Ordne hier Geräte oder andere bestehende Assets diesem Stromkreis zu.
                </p>
              </div>
              <v-list v-else lines="three">
                <v-list-item
                  v-for="item in assignments"
                  :key="item.link_id"
                  :title="item.asset_name"
                  :subtitle="[item.asset_code, item.asset_type_name, item.location_name]
                    .filter(Boolean).join(' · ')"
                  :to="`/assets/${item.asset_id}${item.asset_deleted_at ? '?archived=1' : ''}`"
                >
                  <template #prepend>
                    <v-avatar color="surface-variant"><v-icon icon="mdi-package-variant" /></v-avatar>
                  </template>
                  <template #append>
                    <div class="d-flex align-center ga-1">
                      <v-chip :color="assignmentColor(item)" size="small" variant="tonal">
                        {{ assignmentStatus(item) }}
                      </v-chip>
                      <v-btn
                        v-if="!isReadOnly"
                        icon="mdi-link-variant-off"
                        variant="text"
                        color="warning"
                        title="Zuordnung zum Stromkreis entfernen"
                        aria-label="Zuordnung zum Stromkreis entfernen"
                        :loading="changingAssetId === item.asset_id"
                        @click.prevent="assignmentToRemove = item"
                      />
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <DocumentLinksCard
      v-if="circuit"
      target-type="circuit"
      :target-id="circuit.id"
      :read-only="isReadOnly"
      class="mt-5"
    />

    <NotesCard
      v-if="circuit"
      target-type="circuit"
      :target-id="circuit.id"
      :read-only="isReadOnly"
      class="mt-5"
    />
    <MaintenanceCard
      v-if="circuit"
      target-type="circuit"
      :target-id="circuit.id"
      :read-only="isReadOnly"
      class="mt-5"
    />

    <v-dialog v-model="pickerOpen" max-width="780" scrollable>
      <v-card title="Asset dem Stromkreis zuordnen" prepend-icon="mdi-link-plus">
        <v-card-text>
          <v-alert v-if="pickerError" type="error" variant="tonal" class="mb-4">
            {{ pickerError }}
          </v-alert>
          <v-text-field
            v-model="search"
            label="Assets durchsuchen"
            prepend-inner-icon="mdi-magnify"
            clearable
            hide-details
            class="mb-4"
            @keyup.enter="applySearch"
            @click:clear="applySearch"
          >
            <template #append-inner>
              <v-btn icon="mdi-arrow-right" variant="text" title="Suche ausführen" @click="applySearch" />
            </template>
          </v-text-field>
          <v-skeleton-loader v-if="pickerLoading" type="list-item-three-line@4" />
          <div v-else-if="assets.length === 0" class="text-center py-7">
            <v-icon icon="mdi-package-variant-closed-remove" size="42" color="secondary" />
            <p class="mt-2 mb-0">Keine passenden Assets gefunden.</p>
          </div>
          <v-list v-else lines="two">
            <v-list-item
              v-for="asset in assets"
              :key="asset.id"
              :title="asset.name"
              :subtitle="[asset.jarvis_code, asset.asset_type.name, asset.location?.name]
                .filter(Boolean).join(' · ')"
            >
              <template #append>
                <v-btn
                  v-if="!linkedAssetIds.has(asset.id)"
                  color="primary"
                  variant="tonal"
                  prepend-icon="mdi-link-plus"
                  :loading="changingAssetId === asset.id"
                  @click="assignAsset(asset)"
                >
                  Zuordnen
                </v-btn>
                <v-chip v-else color="success" prepend-icon="mdi-check">Zugeordnet</v-chip>
              </template>
            </v-list-item>
          </v-list>
          <div v-if="assetPages > 1" class="d-flex flex-wrap align-center justify-space-between ga-3 mt-4">
            <span class="text-caption text-medium-emphasis">{{ assetTotal }} Assets</span>
            <v-pagination
              v-model="assetPage"
              :length="assetPages"
              density="comfortable"
              @update:model-value="loadAssets"
            />
          </div>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="pickerOpen = false">Schließen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      :model-value="assignmentToRemove !== null"
      max-width="520"
      @update:model-value="assignmentToRemove = null"
    >
      <v-card title="Zuordnung entfernen?">
        <v-card-text>
          Das Asset bleibt erhalten. Nur die Verbindung zu diesem Stromkreis wird historisch beendet.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="assignmentToRemove = null">Abbrechen</v-btn>
          <v-btn color="warning" :loading="changingAssetId !== null" @click="removeAssignment">
            Entfernen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

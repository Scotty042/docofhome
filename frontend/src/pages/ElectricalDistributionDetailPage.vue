<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NotesCard from '../components/NotesCard.vue'
import ElectricalCircuitList from '../components/ElectricalCircuitList.vue'
import ElectricalWiringSummary from '../components/ElectricalWiringSummary.vue'
import ImmichImageLinksCard from '../components/ImmichImageLinksCard.vue'
import { useElectricalDistributionDetail } from '../composables/useElectricalData'
import { ElectricalApiError, electricalApi } from '../services/electricalApi'
import {
  distributionCapacity,
  groupProtectiveDevices,
  moduleNumbers,
  modulePlacements,
  protectiveDeviceLabels
} from '../services/electricalPresentation'
import type { ElectricalTopology, ProtectiveDevice } from '../types/electrical'

const route = useRoute()
const router = useRouter()
const { distribution, loading, error, errorStatus, loadDistribution } = (
  useElectricalDistributionDetail()
)
const deleting = ref(false)
const topology = ref<ElectricalTopology>({ nodes: [], connections: [], measurement_points: [] })
const topologyLoading = ref(false)
const topologyError = ref<string | null>(null)
const confirmArchive = ref(false)
const deviceToArchive = ref<ProtectiveDevice | null>(null)
const distributionId = computed(() => String(route.params.id ?? ''))
const unavailable = computed(() => errorStatus.value === 0 || (errorStatus.value ?? 0) >= 500)
const structuredLayout = computed(() => distribution.value?.layout_mode === 'sections')
const deviceGroups = computed(() => groupProtectiveDevices(
  distribution.value?.protective_devices ?? [],
  distribution.value?.rows ?? null
))
const positionedGroups = computed(() => deviceGroups.value.filter((group) => group.row !== null))
const unknownGroup = computed(() => deviceGroups.value.find((group) => group.row === null) ?? null)
const moduleLabels = computed(() => (
  distribution.value?.modules_per_row
    ? moduleNumbers(distribution.value.modules_per_row)
    : []
))
const breadcrumbItems = computed(() => distribution.value?.breadcrumbs.map(
  (item, index, values) => ({
    title: item.display_name,
    to: index < values.length - 1 ? `/electrical/distributions/${item.id}` : undefined,
    disabled: index === values.length - 1
  })
) ?? [])

async function archiveDistribution() {
  if (!distribution.value) return
  deleting.value = true
  error.value = null
  try {
    await electricalApi.removeDistribution(distribution.value.id)
    await router.push('/electrical')
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Verteilung konnte nicht archiviert werden.'
    errorStatus.value = reason instanceof ElectricalApiError ? reason.status : 0
    confirmArchive.value = false
  } finally {
    deleting.value = false
  }
}

async function archiveDevice() {
  const device = deviceToArchive.value
  const currentDistributionId = distributionId.value
  if (!device) return
  deleting.value = true
  error.value = null
  try {
    await electricalApi.removeProtectiveDevice(device.id)
    deviceToArchive.value = null
    if (distributionId.value === currentDistributionId) {
      await loadDistribution(currentDistributionId)
    }
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Schutzgerät konnte nicht archiviert werden.'
  } finally {
    deleting.value = false
  }
}

async function loadTopology() {
  topologyLoading.value = true
  topologyError.value = null
  try {
    topology.value = await electricalApi.topology()
  } catch (reason) {
    topology.value = { nodes: [], connections: [], measurement_points: [] }
    topologyError.value = reason instanceof Error
      ? reason.message
      : 'Versorgungsinformationen konnten nicht geladen werden.'
  } finally {
    topologyLoading.value = false
  }
}

watch(distributionId, (id) => {
  void loadDistribution(id)
  void loadTopology()
}, { immediate: true })
</script>

<template>
  <v-container class="distribution-detail pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/electrical" class="mb-2">
      Zur Elektroübersicht
    </v-btn>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
    <v-alert v-else-if="error && !distribution" :type="unavailable ? 'warning' : 'error'" variant="tonal">
      {{ unavailable ? 'Backend nicht erreichbar: ' : '' }}{{ error }}
    </v-alert>

    <template v-else-if="distribution">
      <v-breadcrumbs :items="breadcrumbItems" class="px-0 mb-2" />
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="distribution.deleted_at" type="warning" variant="tonal" class="mb-4">
        Diese Verteilung ist archiviert und nur noch historisch lesbar.
      </v-alert>

      <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
        <div>
          <div class="d-flex align-center ga-3">
            <v-icon icon="mdi-electric-switch" size="38" color="secondary" />
            <h1>{{ distribution.display_name }}</h1>
          </div>
          <p class="text-medium-emphasis mb-0">
            {{ distribution.distribution_type === 'main' ? 'Hauptverteilung' : 'Unterverteilung' }}
            · {{ distribution.asset.location_path }}
          </p>
        </div>
        <div v-if="!distribution.deleted_at" class="d-flex flex-wrap ga-2">
          <v-btn
            prepend-icon="mdi-view-column-outline"
            color="primary"
            :to="`/electrical/distributions/${distribution.id}/layout`"
          >
            Schrankaufteilung
          </v-btn>
          <v-btn
            prepend-icon="mdi-shield-plus-outline"
            variant="tonal"
            :to="`/electrical/protective-devices/new?distribution=${distribution.id}`"
          >
            Schutzgerät
          </v-btn>
          <v-btn
            prepend-icon="mdi-pencil"
            :to="`/electrical/distributions/${distribution.id}/edit`"
          >
            Bearbeiten
          </v-btn>
          <v-btn
            icon="mdi-archive-arrow-down-outline"
            color="warning"
            variant="text"
            aria-label="Verteilung archivieren"
            title="Verteilung archivieren"
            @click="confirmArchive = true"
          />
        </div>
      </div>

      <v-row class="mb-2">
        <v-col cols="12" md="7">
          <v-card title="Verteilung" prepend-icon="mdi-information-outline" height="100%">
            <v-card-text>
              <v-list lines="two">
                <v-list-item title="Asset" :subtitle="distribution.asset.name">
                  <template #append>
                    <v-btn
                      variant="text"
                      :to="`/assets/${distribution.asset.id}`"
                      :text="distribution.asset.jarvis_code"
                    />
                  </template>
                </v-list-item>
                <v-list-item title="Standort" :subtitle="distribution.asset.location_path" />
                <v-list-item
                  title="Aufbau"
                  :subtitle="structuredLayout ? 'Felder und Bereiche' : 'Einfache Reihen'"
                />
                <v-list-item
                  v-if="!structuredLayout"
                  title="Kapazität"
                  :subtitle="distributionCapacity(distribution)"
                />
                <v-list-item
                  v-if="distribution.description"
                  title="Beschreibung"
                  :subtitle="distribution.description"
                />
                <v-list-item v-if="distribution.notes" title="Notizen" :subtitle="distribution.notes" />
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="5">
          <v-card title="Struktur" prepend-icon="mdi-file-tree-outline" height="100%">
            <v-card-text>
              <div class="metric mb-4">
                <span class="text-h4">{{ distribution.direct_subdistribution_count }}</span>
                <span class="text-medium-emphasis">direkte Unterverteilungen</span>
              </div>
              <div class="metric">
                <span class="text-h4">{{ distribution.direct_protective_device_count }}</span>
                <span class="text-medium-emphasis">aktive Schutzgeräte</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-card class="mb-4" title="Versorgung und Abgänge" prepend-icon="mdi-source-branch">
        <v-card-text>
          <v-progress-linear v-if="topologyLoading" indeterminate color="primary" class="mb-3" />
          <v-alert v-if="topologyError" type="warning" variant="tonal" density="compact" class="mb-3">
            Phase und Versorgungsweg konnten nicht geladen werden: {{ topologyError }}
          </v-alert>
          <ElectricalWiringSummary
            :topology="topology"
            endpoint-kind="distribution"
            :endpoint-id="distribution.id"
            :show-button="!distribution.deleted_at"
          />
        </v-card-text>
      </v-card>

      <ImmichImageLinksCard
        :asset-id="distribution.asset.id"
        :read-only="Boolean(distribution.deleted_at)"
        title="Fotos des Verteilerschranks"
        empty-text="Noch keine Immich-Fotos mit diesem Verteilerschrank verknüpft."
      />

      <v-card
        v-if="structuredLayout"
        class="mt-4"
        title="Strukturierte Schrankaufteilung"
        prepend-icon="mdi-view-column-outline"
      >
        <v-card-text>
          <p class="mb-4">
            Felder, Bereiche, Reihen und Modulpositionen werden in der Schrankaufteilung dargestellt.
            Die Ansicht steht für Haupt- und Unterverteilungen gleichermaßen zur Verfügung.
          </p>
          <v-btn
            color="primary"
            prepend-icon="mdi-view-dashboard-edit-outline"
            :to="`/electrical/distributions/${distribution.id}/layout`"
          >
            Schrankaufteilung öffnen
          </v-btn>
        </v-card-text>
      </v-card>

      <v-card v-else class="mt-4" title="Schutzgeräte" prepend-icon="mdi-shield-outline">
        <v-card-text v-if="distribution.protective_devices.length === 0" class="text-center py-10">
          <v-icon icon="mdi-shield-off-outline" size="48" color="secondary" />
          <h2 class="mt-3">Keine Schutzgeräte zugeordnet</h2>
          <p class="text-medium-emphasis">Die Verteilung funktioniert auch ohne dokumentierte Geräte.</p>
        </v-card-text>
        <v-card-text v-else>
          <section v-for="group in positionedGroups" :key="group.row ?? 'positioned'" class="mb-7">
            <div class="d-flex align-center justify-space-between mb-3">
              <h2>Reihe {{ group.row }}</h2>
              <v-chip size="small" variant="tonal">{{ group.devices.length }} Geräte</v-chip>
            </div>

            <div v-if="distribution.modules_per_row" class="module-scroll" data-testid="module-scroll">
              <div
                class="module-board"
                :style="{ gridTemplateColumns: `repeat(${distribution.modules_per_row}, minmax(54px, 1fr))` }"
              >
                <div
                  v-for="moduleNumber in moduleLabels"
                  :key="`module-${group.row}-${moduleNumber}`"
                  class="module-cell"
                  :style="{ gridColumn: moduleNumber }"
                >
                  <span>{{ moduleNumber }}</span>
                </div>
                <v-card
                  v-for="placement in modulePlacements(group.devices)"
                  :key="placement.device.id"
                  class="module-device"
                  variant="tonal"
                  :style="{ gridColumn: placement.gridColumn }"
                >
                  <v-card-title class="text-wrap text-body-1 font-weight-bold">
                    {{ placement.device.asset.name }}
                  </v-card-title>
                  <v-card-subtitle>{{ placement.device.asset.jarvis_code }}</v-card-subtitle>
                  <v-card-text class="pt-2">
                    <v-chip color="primary" variant="tonal" size="x-small" class="mb-2">
                      {{ protectiveDeviceLabels[placement.device.device_type] }}
                    </v-chip>
                    <div class="text-caption font-weight-bold">
                      Modul {{ placement.start }}–{{ placement.end }} · {{ placement.device.module_width }} TE
                    </div>
                    <div class="text-caption">
                      <span v-if="placement.device.rated_current_a !== null">{{ placement.device.rated_current_a }} A</span>
                      <span v-if="placement.device.characteristic"> · {{ placement.device.characteristic }}</span>
                      <span v-if="placement.device.residual_current_ma !== null">
                        · {{ placement.device.residual_current_ma }} mA
                      </span>
                    </div>
                    <ElectricalWiringSummary
                      class="mt-3"
                      :topology="topology"
                      endpoint-kind="protective_device"
                      :endpoint-id="placement.device.id"
                      :show-button="!distribution.deleted_at"
                      compact
                    />
                  </v-card-text>
                  <v-card-actions v-if="!distribution.deleted_at" class="px-2">
                    <v-btn
                      size="small"
                      variant="text"
                      icon="mdi-pencil"
                      :to="`/electrical/protective-devices/${placement.device.id}/edit`"
                      aria-label="Schutzgerät bearbeiten"
                      title="Schutzgerät bearbeiten"
                    />
                    <v-spacer />
                    <v-btn
                      size="small"
                      icon="mdi-archive-arrow-down-outline"
                      color="warning"
                      variant="text"
                      aria-label="Schutzgerät archivieren"
                      title="Schutzgerät archivieren"
                      @click="deviceToArchive = placement.device"
                    />
                  </v-card-actions>
                </v-card>
              </div>
            </div>

            <div v-else class="device-list">
              <v-card
                v-for="device in group.devices"
                :key="device.id"
                variant="outlined"
                class="device-card"
              >
                <v-card-title class="text-wrap">{{ device.asset.name }}</v-card-title>
                <v-card-subtitle>{{ device.asset.jarvis_code }}</v-card-subtitle>
                <v-card-text>
                  <div class="mb-3">
                    {{ protectiveDeviceLabels[device.device_type] }} · Modul
                    {{ device.start_position }}–{{ (device.start_position ?? 1) + (device.module_width ?? 1) - 1 }}
                  </div>
                  <ElectricalWiringSummary
                    :topology="topology"
                    endpoint-kind="protective_device"
                    :endpoint-id="device.id"
                    :show-button="!distribution.deleted_at"
                    compact
                  />
                </v-card-text>
                <v-card-actions v-if="!distribution.deleted_at">
                  <v-btn
                    variant="text"
                    prepend-icon="mdi-pencil"
                    :to="`/electrical/protective-devices/${device.id}/edit`"
                  >
                    Bearbeiten
                  </v-btn>
                  <v-spacer />
                  <v-btn
                    icon="mdi-archive-arrow-down-outline"
                    color="warning"
                    variant="text"
                    aria-label="Schutzgerät archivieren"
                    title="Schutzgerät archivieren"
                    @click="deviceToArchive = device"
                  />
                </v-card-actions>
              </v-card>
            </div>
          </section>

          <section v-if="unknownGroup" class="mb-2">
            <div class="d-flex align-center justify-space-between mb-3">
              <h2>Position unbekannt</h2>
              <v-chip size="small" variant="tonal">{{ unknownGroup.devices.length }} Geräte</v-chip>
            </div>
            <div class="device-grid">
              <v-card
                v-for="device in unknownGroup.devices"
                :key="device.id"
                variant="outlined"
                class="device-card"
              >
                <v-card-title class="text-wrap pb-1">{{ device.asset.name }}</v-card-title>
                <v-card-subtitle>{{ device.asset.jarvis_code }}</v-card-subtitle>
                <v-card-text>
                  <v-chip color="primary" variant="tonal" size="small">
                    {{ protectiveDeviceLabels[device.device_type] }}
                  </v-chip>
                  <ElectricalWiringSummary
                    class="mt-3"
                    :topology="topology"
                    endpoint-kind="protective_device"
                    :endpoint-id="device.id"
                    :show-button="!distribution.deleted_at"
                    compact
                  />
                </v-card-text>
                <v-card-actions v-if="!distribution.deleted_at">
                  <v-btn
                    variant="text"
                    prepend-icon="mdi-pencil"
                    :to="`/electrical/protective-devices/${device.id}/edit`"
                  >
                    Bearbeiten
                  </v-btn>
                  <v-spacer />
                  <v-btn
                    icon="mdi-archive-arrow-down-outline"
                    color="warning"
                    variant="text"
                    aria-label="Schutzgerät archivieren"
                    title="Schutzgerät archivieren"
                    @click="deviceToArchive = device"
                  />
                </v-card-actions>
              </v-card>
            </div>
          </section>
        </v-card-text>
      </v-card>

      <ElectricalCircuitList
        :distribution-id="distribution.id"
        :distribution-deleted="Boolean(distribution.deleted_at)"
      />
    </template>

    <DocumentLinksCard
      v-if="distribution"
      target-type="distribution"
      :target-id="distribution.id"
      :read-only="Boolean(distribution.deleted_at)"
      class="mt-5"
    />

    <NotesCard
      v-if="distribution"
      target-type="distribution"
      :target-id="distribution.id"
      :read-only="Boolean(distribution.deleted_at)"
      class="mt-5"
    />
    <MaintenanceCard
      v-if="distribution"
      target-type="distribution"
      :target-id="distribution.id"
      :read-only="Boolean(distribution.deleted_at)"
      class="mt-5"
    />

    <v-dialog v-model="confirmArchive" max-width="520">
      <v-card title="Verteilung archivieren?">
        <v-card-text>
          Eine Verteilung kann nur ohne aktive Unterverteilungen, Schutzgeräte und Stromkreise
          archiviert werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="confirmArchive = false">Abbrechen</v-btn>
          <v-btn color="warning" :loading="deleting" @click="archiveDistribution">Archivieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="deviceToArchive !== null" max-width="520" @update:model-value="deviceToArchive = null">
      <v-card title="Schutzgerät archivieren?">
        <v-card-text>Die historische Zuordnung bleibt lesbar.</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="deviceToArchive = null">Abbrechen</v-btn>
          <v-btn color="warning" :loading="deleting" @click="archiveDevice">Archivieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.distribution-detail { max-width: 1280px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
h2 { font-size: 1.15rem; }
.metric { display: flex; flex-direction: column; }
.device-grid,
.device-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
.module-scroll { overflow-x: auto; padding: 0.25rem 0.25rem 0.75rem; }
.module-board {
  display: grid;
  grid-template-rows: 28px minmax(150px, auto);
  gap: 4px;
  min-width: max-content;
}
.module-cell {
  grid-row: 1;
  min-width: 54px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  text-align: center;
  color: rgb(var(--v-theme-on-surface));
  background: rgb(var(--v-theme-surface-variant));
}
.module-cell span { font-size: 0.72rem; }
.module-device {
  grid-row: 2;
  min-width: 54px;
  overflow: hidden;
  border: 1px solid rgb(var(--v-theme-primary));
}
</style>

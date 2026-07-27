<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NotesCard from '../components/NotesCard.vue'
import ElectricalWiringSummary from '../components/ElectricalWiringSummary.vue'
import { useElectricalProtectiveDeviceEditor } from '../composables/useElectricalData'
import { electricalApi } from '../services/electricalApi'
import {
  flattenDistributionTree,
  protectiveDeviceLabels
} from '../services/electricalPresentation'
import type {
  ElectricalTopology,
  ProtectiveDeviceType,
  ProtectiveDeviceWrite
} from '../types/electrical'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const route = useRoute()
const router = useRouter()
const formElement = ref<FormHandle | null>(null)
const { form, tree, assets, loading, assetsLoading, error, loadEditor, searchAssets } = (
  useElectricalProtectiveDeviceEditor()
)
const saving = ref(false)
const topology = ref<ElectricalTopology>({ nodes: [], connections: [], measurement_points: [] })
const topologyLoading = ref(false)
const topologyError = ref<string | null>(null)
let assetSearchTimer: ReturnType<typeof setTimeout> | undefined
const deviceId = computed(() => route.params.id ? String(route.params.id) : null)
const requestedDistribution = computed(() => (
  typeof route.query.distribution === 'string' ? route.query.distribution : null
))
const isEditing = computed(() => deviceId.value !== null)
const title = computed(() => isEditing.value ? 'Schutzgerät bearbeiten' : 'Schutzgerät anlegen')
const flatDistributions = computed(() => flattenDistributionTree(tree.value))
const distributionOptions = computed(() => flatDistributions.value.map(({ distribution, depth }) => ({
  id: distribution.id,
  title: `${'— '.repeat(depth)}${distribution.display_name} · ${distribution.asset.location_path}`
})))
const selectedDistribution = computed(() => flatDistributions.value.find(
  ({ distribution }) => distribution.id === form.value.distribution_id
)?.distribution ?? null)
const structuredLayout = computed(() => selectedDistribution.value?.layout_mode === 'sections')
const returnPath = computed(() => {
  if (!form.value.distribution_id) return '/electrical'
  return structuredLayout.value
    ? `/electrical/distributions/${form.value.distribution_id}/layout`
    : `/electrical/distributions/${form.value.distribution_id}`
})
const matchingAssets = computed(() => assets.value.filter((asset) => (
  !selectedDistribution.value
  || asset.location_id === selectedDistribution.value.asset.location_id
)))
const selectedAsset = computed(() => assets.value.find(
  (asset) => asset.id === form.value.asset_id
) ?? null)
const assetOptions = computed(() => matchingAssets.value.map((asset) => ({
  ...asset,
  title: `${asset.name} · ${asset.jarvis_code} · ${asset.location_path}`
})))
const typeItems = (Object.entries(protectiveDeviceLabels) as Array<[ProtectiveDeviceType, string]>)
  .map(([value, label]) => ({ title: label, value }))
const requiredRule = (value: string | null) => Boolean(value) || 'Dieses Feld ist erforderlich.'
const positionRule = () => {
  if (structuredLayout.value) return true
  const values = [form.value.row_number, form.value.start_position, form.value.module_width]
  const supplied = values.filter((value) => value !== null && value !== undefined).length
  return supplied === 0 || supplied === 3 || 'Reihe, Startposition und Breite gemeinsam angeben.'
}

watch(
  [deviceId, requestedDistribution],
  ([id, distribution]) => {
    clearTimeout(assetSearchTimer)
    void loadEditor(id, distribution)
  },
  { immediate: true }
)

watch(deviceId, async (id) => {
  topology.value = { nodes: [], connections: [], measurement_points: [] }
  topologyError.value = null
  if (!id) return
  topologyLoading.value = true
  try {
    topology.value = await electricalApi.topology()
  } catch (reason) {
    topologyError.value = reason instanceof Error
      ? reason.message
      : 'Versorgungsinformationen konnten nicht geladen werden.'
  } finally {
    topologyLoading.value = false
  }
}, { immediate: true })

watch(
  () => form.value.asset_id,
  () => {
    if (!isEditing.value || form.value.module_width === null) {
      form.value.module_width = selectedAsset.value?.effective_module_width ?? null
    }
  }
)

watch(
  () => form.value.distribution_id,
  () => {
    if (form.value.asset_id && !matchingAssets.value.some((asset) => asset.id === form.value.asset_id)) {
      form.value.asset_id = ''
    }
    if (!isEditing.value && structuredLayout.value) {
      form.value.area_id = null
      form.value.row_number = null
      form.value.start_position = null
      form.value.module_width = null
    }
  }
)

function optionalText(value: string | null): string | null {
  return value?.trim() || null
}

function optionalNumber(value: number | null): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function scheduleAssetSearch(value: string | null) {
  if (form.value.asset_id) return
  clearTimeout(assetSearchTimer)
  assetSearchTimer = setTimeout(() => void searchAssets(value?.trim() ?? ''), 250)
}

async function save() {
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  saving.value = true
  error.value = null
  try {
    const structuredCreate = structuredLayout.value && !deviceId.value
    const payload: ProtectiveDeviceWrite = {
      ...form.value,
      device_type: form.value.device_type as ProtectiveDeviceType,
      area_id: structuredCreate ? null : form.value.area_id,
      row_number: structuredCreate ? null : optionalNumber(form.value.row_number),
      start_position: structuredCreate ? null : optionalNumber(form.value.start_position),
      module_width: structuredCreate ? null : optionalNumber(form.value.module_width),
      rated_current_a: optionalNumber(form.value.rated_current_a),
      residual_current_ma: optionalNumber(form.value.residual_current_ma),
      poles: optionalNumber(form.value.poles),
      breaking_capacity_ka: optionalNumber(form.value.breaking_capacity_ka),
      characteristic: optionalText(form.value.characteristic),
      rcd_type: optionalText(form.value.rcd_type),
      fuse_type: optionalText(form.value.fuse_type),
      spd_type: optionalText(form.value.spd_type),
      description: optionalText(form.value.description),
      notes: optionalText(form.value.notes)
    }
    if (deviceId.value && structuredLayout.value) {
      await electricalApi.updateStructuredProtectiveDevice(
        form.value.distribution_id,
        deviceId.value,
        payload
      )
    } else if (deviceId.value) {
      await electricalApi.updateProtectiveDevice(deviceId.value, payload)
    } else {
      await electricalApi.createProtectiveDevice(payload)
    }
    await router.push(returnPath.value)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Schutzgerät konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-container class="device-editor pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" :to="returnPath" class="mb-3">
      Zur Verteilung
    </v-btn>
    <div class="mb-5">
      <h1>{{ title }}</h1>
      <p class="text-medium-emphasis">
        Sicherung, FI/RCD, LS/MCB, FI/LS/RCBO oder Überspannungsschutz dokumentieren.
      </p>
    </div>

    <v-skeleton-loader v-if="loading" type="heading, card, card, card" />
    <v-form v-else ref="formElement" @submit.prevent="save">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>

      <v-card
        v-if="isEditing && deviceId"
        title="Phase und Versorgungsweg"
        prepend-icon="mdi-source-branch"
        class="mb-5"
      >
        <v-card-text>
          <v-progress-linear v-if="topologyLoading" indeterminate color="primary" class="mb-3" />
          <v-alert v-if="topologyError" type="warning" variant="tonal" density="compact" class="mb-3">
            Die technischen Daten bleiben bearbeitbar, aber der Versorgungsweg konnte nicht geladen
            werden: {{ topologyError }}
          </v-alert>
          <ElectricalWiringSummary
            :topology="topology"
            endpoint-kind="protective_device"
            :endpoint-id="deviceId"
          />
          <p class="text-caption text-medium-emphasis mt-3 mb-0">
            „Dahinter“ umfasst alle dokumentierten Schutzgeräte, Stromkreise und Assets im
            nachgelagerten Versorgungsweg, nicht nur die direkt folgende Verbindung.
          </p>
        </v-card-text>
      </v-card>

      <v-card title="Zuordnung" prepend-icon="mdi-link-variant" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="form.distribution_id"
                label="Verteilung"
                :items="distributionOptions"
                item-title="title"
                item-value="id"
                :rules="[requiredRule]"
                :disabled="isEditing && structuredLayout"
              />
            </v-col>
            <v-col cols="12">
              <v-autocomplete
                v-model="form.asset_id"
                label="Asset am selben Standort"
                :items="assetOptions"
                item-title="title"
                item-value="id"
                :rules="[requiredRule]"
                :loading="assetsLoading"
                :disabled="!form.distribution_id || isEditing"
                no-data-text="Kein geeignetes Asset an diesem Standort"
                :hint="isEditing
                  ? 'Die Asset-Zuordnung ist im Bearbeitungsmodus unveränderlich.'
                  : 'Die vollständige, paginierte Asset-Auswahl wird geladen.'"
                persistent-hint
                no-filter
                @update:search="scheduleAssetSearch"
              />
            </v-col>
            <v-col cols="12">
              <v-btn variant="text" prepend-icon="mdi-plus" to="/assets/new">
                Neues Asset erfassen
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Gerät und Position" prepend-icon="mdi-shield-outline" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-select v-model="form.device_type" label="Gerätetyp" :items="typeItems" />
            </v-col>
            <v-col cols="4" md="2">
              <v-text-field
                v-model.number="form.row_number"
                label="Reihe"
                type="number"
                min="1"
                max="100"
                clearable
                :disabled="structuredLayout"
                :rules="[positionRule]"
              />
            </v-col>
            <v-col cols="4" md="3">
              <v-text-field
                v-model.number="form.start_position"
                label="Startmodul"
                type="number"
                min="1"
                max="1000"
                clearable
                :disabled="structuredLayout"
                :rules="[positionRule]"
              />
            </v-col>
            <v-col cols="4" md="3">
              <v-text-field
                v-model.number="form.module_width"
                label="Breite (TE)"
                type="number"
                min="1"
                max="100"
                readonly
                :disabled="structuredLayout"
                :rules="[positionRule]"
                :hint="form.asset_id && !form.module_width
                  ? 'Am Asset, Asset-Typ oder Produkt ist noch keine DIN-Breite hinterlegt.'
                  : 'Die Breite wird aus Asset, Asset-Typ oder DIN-Produkt übernommen.'"
                persistent-hint
              />
            </v-col>
            <v-col cols="12">
              <v-alert type="info" variant="tonal" density="compact">
                <template v-if="structuredLayout">
                  Feld, Bereich und Modulposition werden ausschließlich in der Schrankaufteilung geändert.
                </template>
                <template v-else>
                  Die Position darf vollständig unbekannt bleiben. Teilangaben und Überlappungen werden abgelehnt.
                </template>
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Technische Daten" prepend-icon="mdi-sine-wave" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="6" md="3"><v-text-field v-model.number="form.rated_current_a" label="Nennstrom (A)" type="number" min="0" clearable /></v-col>
            <v-col cols="6" md="3"><v-text-field v-model.number="form.residual_current_ma" label="Fehlerstrom (mA)" type="number" min="0" clearable /></v-col>
            <v-col cols="6" md="3"><v-text-field v-model="form.characteristic" label="Charakteristik" maxlength="30" /></v-col>
            <v-col cols="6" md="3"><v-text-field v-model.number="form.poles" label="Pole" type="number" min="1" max="12" clearable /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model.number="form.breaking_capacity_ka" label="Schaltvermögen (kA)" type="number" min="0" clearable /></v-col>
            <v-col v-if="form.device_type === 'rcd' || form.device_type === 'rcbo'" cols="12" md="4"><v-text-field v-model="form.rcd_type" label="RCD-Typ" maxlength="80" /></v-col>
            <v-col v-if="form.device_type === 'fuse'" cols="12" md="4"><v-text-field v-model="form.fuse_type" label="Sicherungstyp" maxlength="80" /></v-col>
            <v-col v-if="form.device_type === 'spd'" cols="12" md="4"><v-text-field v-model="form.spd_type" label="SPD-Typ" maxlength="80" /></v-col>
            <v-col cols="12">
              <v-alert type="info" variant="tonal" density="compact">
                Alle technischen Werte sind optional. DocOfHome ergänzt keine vermuteten Standardwerte.
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Beschreibung und Notizen" prepend-icon="mdi-note-text-outline" class="mb-5">
        <v-card-text>
          <v-textarea v-model="form.description" label="Beschreibung (optional)" rows="3" auto-grow />
          <v-textarea v-model="form.notes" label="Interne Notizen (optional)" rows="3" auto-grow />
        </v-card-text>
      </v-card>

      <div class="d-flex flex-column-reverse flex-sm-row justify-end ga-3">
        <v-btn variant="text" :to="returnPath">Abbrechen</v-btn>
        <v-btn type="submit" color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="matchingAssets.length === 0">
          Schutzgerät speichern
        </v-btn>
      </div>
    </v-form>
    <DocumentLinksCard
      v-if="deviceId"
      target-type="protective_device"
      :target-id="deviceId"
      class="mt-5"
    />
    <NotesCard
      v-if="deviceId"
      target-type="protective_device"
      :target-id="deviceId"
      class="mt-5"
    />
    <MaintenanceCard
      v-if="deviceId"
      target-type="protective_device"
      :target-id="deviceId"
      class="mt-5"
    />
</v-container>
</template>

<style scoped>
.device-editor { max-width: 1100px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
</style>

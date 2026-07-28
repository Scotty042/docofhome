<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { electricalApi } from '../services/electricalApi'
import {
  createEmptyElectricalCircuit,
  editableElectricalCircuit
} from '../types/electrical'
import type { DistributionDetail, ElectricalCircuitWrite, ElectricalProtectiveDeviceOption } from '../types/electrical'

const route = useRoute()
const router = useRouter()
const circuitId = computed(() => String(route.params.id ?? ''))
const editing = computed(() => Boolean(circuitId.value))
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const distribution = ref<DistributionDetail | null>(null)
const protectiveDeviceOptions = ref<ElectricalProtectiveDeviceOption[]>([])
const form = reactive<ElectricalCircuitWrite>(
  createEmptyElectricalCircuit(String(route.query.distribution ?? ''))
)

const protectiveDeviceSelection = computed<string | null>({
  get() {
    if (form.protective_device_asset_id) return `asset:${form.protective_device_asset_id}`
    if (form.protective_device_id) return `legacy_device:${form.protective_device_id}`
    return null
  },
  set(value) {
    form.protective_device_id = null
    form.protective_device_asset_id = null
    if (!value) return
    const [referenceType, id] = value.split(':', 2)
    if (!id) return
    if (referenceType === 'asset') form.protective_device_asset_id = id
    else if (referenceType === 'legacy_device') form.protective_device_id = id
  }
})

const protectiveDevices = computed(() => protectiveDeviceOptions.value.map((device) => ({
  title: device.occupied
    ? `${device.label} · belegt durch ${device.occupied_by_circuit_name}`
    : device.label,
  value: `${device.reference_type}:${device.id}`,
  disabled: device.occupied
})))

async function load() {
  loading.value = true
  error.value = null
  try {
    if (editing.value) {
      Object.assign(form, editableElectricalCircuit(await electricalApi.getCircuit(circuitId.value)))
    }
    if (!form.distribution_id) throw new Error('Keine Verteilung ausgewählt.')
    distribution.value = await electricalApi.getDistribution(form.distribution_id)
    protectiveDeviceOptions.value = await electricalApi.protectiveDeviceOptions(
      form.distribution_id, editing.value ? circuitId.value : undefined
    )
    if (distribution.value.deleted_at) throw new Error('Archivierte Verteilungen sind nur lesbar.')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Stromkreis konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.name.trim() || !form.distribution_id || !protectiveDeviceSelection.value) {
    error.value = 'Bitte Bezeichnung und konkrete Sicherung auswählen.'
    return
  }
  saving.value = true
  error.value = null
  try {
    const payload: ElectricalCircuitWrite = {
      ...form,
      name: form.name.trim(),
      circuit_number: form.circuit_number?.trim() || null,
      description: form.description?.trim() || null,
      notes: form.notes?.trim() || null
    }
    if (editing.value) await electricalApi.updateCircuit(circuitId.value, payload)
    else await electricalApi.createCircuit(payload)
    await router.push(`/electrical/distributions/${form.distribution_id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Stromkreis konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

watch(circuitId, () => void load(), { immediate: true })
</script>

<template>
  <v-container class="circuit-editor pa-4 pa-sm-6" fluid>
    <v-btn
      variant="text"
      prepend-icon="mdi-arrow-left"
      :to="form.distribution_id ? `/electrical/distributions/${form.distribution_id}` : '/electrical'"
      class="mb-2"
    >
      Zurück zur Verteilung
    </v-btn>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card" />
    <template v-else>
      <div class="d-flex align-center ga-3 mb-5">
        <v-icon icon="mdi-transmission-tower" size="38" color="secondary" />
        <div>
          <h1>{{ editing ? 'Stromkreis bearbeiten' : 'Stromkreis hinzufügen' }}</h1>
          <p class="text-medium-emphasis mb-0">
            {{ distribution?.display_name ?? 'Elektrische Verteilung' }}
          </p>
        </div>
      </div>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert
        type="info"
        variant="tonal"
        density="compact"
        icon="mdi-information-outline"
        class="mb-4"
        title="Wofür ist der Stromkreis gedacht?"
      >
        Erfasse hier einen benannten Versorgungszweig der Verteilung, beispielsweise Steckdosen,
        Beleuchtung oder Wärmepumpe. Das tatsächlich schützende Endgerät ist verpflichtend; die konkret versorgten Assets
        werden anschließend auf der Detailseite zugeordnet.
      </v-alert>
      <v-card title="Dokumentation" prepend-icon="mdi-form-textbox">
        <v-card-text>
          <v-row>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model="form.circuit_number"
                label="Nummer"
                maxlength="50"
                hint="Optional und innerhalb der Verteilung eindeutig"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="form.name"
                label="Bezeichnung"
                maxlength="150"
                :rules="[(value: string) => Boolean(value?.trim()) || 'Bezeichnung ist erforderlich']"
                required
              />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="protectiveDeviceSelection"
                :items="protectiveDevices"
                label="Sicherung / Schutzgerät"
                prepend-inner-icon="mdi-shield-outline"
                :rules="[(value: string) => Boolean(value) || 'Sicherung / Schutzgerät ist erforderlich']"
                required
                hint="Nur aktive, platzierte und noch nicht belegte Sicherungen, LS und FI/LS dieser Verteilung"
                persistent-hint
              />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="form.description" label="Beschreibung" rows="3" auto-grow />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="form.notes" label="Notizen" rows="3" auto-grow />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            :to="form.distribution_id ? `/electrical/distributions/${form.distribution_id}` : '/electrical'"
          >
            Abbrechen
          </v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!protectiveDeviceSelection" prepend-icon="mdi-content-save" @click="submit">
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </template>
  </v-container>
</template>

<style scoped>
.circuit-editor { max-width: 900px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
</style>

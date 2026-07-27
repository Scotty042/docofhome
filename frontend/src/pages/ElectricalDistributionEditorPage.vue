<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useElectricalDistributionEditor } from '../composables/useElectricalData'
import { electricalApi } from '../services/electricalApi'
import { eligibleParentDistributions } from '../services/electricalPresentation'
import type { DistributionType, DistributionWrite } from '../types/electrical'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const route = useRoute()
const router = useRouter()
const formElement = ref<FormHandle | null>(null)
const { form, tree, assets, loading, assetsLoading, error, loadEditor, searchAssets } = (
  useElectricalDistributionEditor()
)
const saving = ref(false)
let assetSearchTimer: ReturnType<typeof setTimeout> | undefined
const distributionId = computed(() => route.params.id ? String(route.params.id) : null)
const requestedParent = computed(() => (
  typeof route.query.parent === 'string' ? route.query.parent : null
))
const isEditing = computed(() => distributionId.value !== null)
const structuredEditing = computed(() => isEditing.value && form.value.layout_mode === 'sections')
const title = computed(() => isEditing.value ? 'Verteilung bearbeiten' : 'Verteilung anlegen')
const assetOptions = computed(() => assets.value.map((asset) => ({
  ...asset,
  title: `${asset.name} · ${asset.jarvis_code} · ${asset.location_path}`
})))
const parentOptions = computed(() => eligibleParentDistributions(
  tree.value,
  distributionId.value
).map(({ distribution, depth }) => ({
  id: distribution.id,
  title: `${'— '.repeat(depth)}${distribution.display_name} · ${distribution.asset.location_path}`
})))
const typeItems = [
  { title: 'Hauptverteilung', value: 'main' },
  { title: 'Unterverteilung', value: 'sub' }
]
const layoutItems = [
  { title: 'Einfache Reihen', value: 'rows' },
  { title: 'Felder und Bereiche', value: 'sections' },
  { title: 'Verteilerdose', value: 'junction_box' }
]
const requiredRule = (value: string | null) => Boolean(value) || 'Dieses Feld ist erforderlich.'
const parentRule = (value: string | null) => (
  form.value.distribution_type === 'main'
  || Boolean(value)
  || 'Eine Unterverteilung benötigt eine übergeordnete Verteilung.'
)

watch(
  [distributionId, requestedParent],
  ([id, parent]) => {
    clearTimeout(assetSearchTimer)
    void loadEditor(id, parent)
  },
  { immediate: true }
)

watch(
  () => form.value.distribution_type,
  (type) => {
    if (type === 'main') form.value.parent_distribution_id = null
  }
)

watch(
  () => form.value.parent_distribution_id,
  (parentId) => {
    if (parentId) form.value.distribution_type = 'sub'
  }
)

watch(
  () => form.value.layout_mode,
  (layout) => {
    if (layout === 'sections') {
      form.value.rows = null
      form.value.modules_per_row = null
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
    const distributionType = form.value.distribution_type as DistributionType
    const structured = form.value.layout_mode === 'sections'
    const rowLayout = form.value.layout_mode === 'rows'
    const payload: DistributionWrite = {
      ...form.value,
      distribution_type: distributionType,
      layout_mode: form.value.layout_mode,
      parent_distribution_id: distributionType === 'main'
        ? null
        : form.value.parent_distribution_id,
      designation: optionalText(form.value.designation),
      rows: rowLayout ? optionalNumber(form.value.rows) : null,
      modules_per_row: rowLayout ? optionalNumber(form.value.modules_per_row) : null,
      description: optionalText(form.value.description),
      notes: optionalText(form.value.notes)
    }
    const saved = distributionId.value
      ? await electricalApi.updateDistribution(distributionId.value, payload)
      : await electricalApi.createDistribution(payload)
    await router.push(
      saved.layout_mode === 'sections'
        ? `/electrical/distributions/${saved.id}/layout`
        : `/electrical/distributions/${saved.id}`
    )
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Verteilung konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-container class="distribution-editor pa-4 pa-sm-6" fluid>
    <v-btn
      variant="text"
      prepend-icon="mdi-arrow-left"
      :to="distributionId ? `/electrical/distributions/${distributionId}` : '/electrical'"
      class="mb-3"
    >
      {{ distributionId ? 'Zur Detailansicht' : 'Zur Elektroübersicht' }}
    </v-btn>
    <div class="mb-5">
      <h1>{{ title }}</h1>
      <p class="text-medium-emphasis">
        Die elektrische Rolle verwendet Identität und Standort eines bestehenden Assets.
      </p>
    </div>

    <v-skeleton-loader v-if="loading" type="heading, card, card" />
    <v-form v-else ref="formElement" @submit.prevent="save">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
      <v-alert v-if="assets.length === 0" type="info" variant="tonal" class="mb-5">
        Kein geeignetes aktives Asset mit Standort ist verfügbar.
        <v-btn variant="text" to="/assets/new">Asset erfassen</v-btn>
      </v-alert>

      <v-card title="Asset und Bezeichnung" prepend-icon="mdi-package-variant" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-autocomplete
                v-model="form.asset_id"
                label="Asset"
                :items="assetOptions"
                item-title="title"
                item-value="id"
                :rules="[requiredRule]"
                :loading="assetsLoading"
                :disabled="isEditing"
                hint="Name, Asset-Code und vollständiger Standortpfad; im Bearbeitungsmodus unveränderlich"
                persistent-hint
                no-data-text="Kein geeignetes Asset gefunden"
                no-filter
                @update:search="scheduleAssetSearch"
              />
            </v-col>
            <v-col cols="12" md="8">
              <v-text-field
                v-model="form.designation"
                label="Bezeichnung (optional)"
                maxlength="150"
                hint="Ohne Bezeichnung wird der Assetname angezeigt."
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Hierarchie und Aufbau" prepend-icon="mdi-file-tree-outline" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-select
                v-model="form.distribution_type"
                label="Verteilungstyp"
                :items="typeItems"
                :disabled="structuredEditing"
              />
            </v-col>
            <v-col cols="12" md="8">
              <v-select
                v-model="form.parent_distribution_id"
                label="Übergeordnete Verteilung"
                :items="parentOptions"
                item-title="title"
                item-value="id"
                :disabled="form.distribution_type === 'main'"
                :rules="[parentRule]"
                clearable
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="form.layout_mode"
                label="Aufbau"
                :items="layoutItems"
                :disabled="structuredEditing"
                :hint="structuredEditing
                  ? 'Eine konfigurierte Schrankaufteilung bleibt dauerhaft im Feld-/Bereichsmodus.'
                  : 'Felder und Bereiche kann für Haupt- und Unterverteilungen verwendet werden.'"
                persistent-hint
              />
            </v-col>
            <template v-if="form.layout_mode === 'rows'">
              <v-col cols="6" md="3">
                <v-text-field
                  v-model.number="form.rows"
                  label="Reihen"
                  type="number"
                  min="1"
                  max="100"
                  clearable
                />
              </v-col>
              <v-col cols="6" md="3">
                <v-text-field
                  v-model.number="form.modules_per_row"
                  label="Module je Reihe"
                  type="number"
                  min="1"
                  max="1000"
                  clearable
                />
              </v-col>
            </template>
            <v-col cols="12">
              <v-alert type="info" variant="tonal" density="compact">
                <template v-if="form.layout_mode === 'sections'">
                  Nach dem Speichern legst du Felder wie „Links“, „Mitte“ und „Rechts“ sowie deren Bereiche an.
                </template>
                <template v-else-if="form.layout_mode === 'junction_box'">
                  Eine Verteilerdose ist ein struktureller Behälter für Klemmen und direkte Verbindungen. Sie besitzt keine fiktiven TE-Reihen.
                </template>
                <template v-else>
                  Unbekannte Kapazitäten bleiben leer; DocOfHome erzeugt keine technischen Annahmen.
                </template>
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
        <v-btn
          v-if="distributionId && form.layout_mode === 'sections'"
          variant="tonal"
          prepend-icon="mdi-view-column-outline"
          :to="`/electrical/distributions/${distributionId}/layout`"
        >
          Schrankaufteilung
        </v-btn>
        <v-btn
          variant="text"
          :to="distributionId ? `/electrical/distributions/${distributionId}` : '/electrical'"
        >
          Abbrechen
        </v-btn>
        <v-btn
          type="submit"
          color="primary"
          prepend-icon="mdi-content-save"
          :loading="saving"
          :disabled="assets.length === 0"
        >
          Verteilung speichern
        </v-btn>
      </div>
    </v-form>
  </v-container>
</template>

<style scoped>
.distribution-editor { max-width: 1100px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
</style>

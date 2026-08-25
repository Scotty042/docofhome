<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useLocationEditorData } from '../composables/useLocationEditorData'
import { locationApi } from '../services/locationApi'
import { eligibleParentLocations, locationTypeItems } from '../services/locationPresentation'
import type { LocationType } from '../types/locations'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const route = useRoute()
const router = useRouter()
const formElement = ref<FormHandle | null>(null)
const { form, locations, loading, error, loadEditor } = useLocationEditorData()
const saving = ref(false)
const locationId = computed(() => route.params.id ? String(route.params.id) : null)
const isEditing = computed(() => locationId.value !== null)
const isRoot = computed(() => form.value.location_type === 'building')
const title = computed(() => isEditing.value ? 'Standort bearbeiten' : 'Bereich anlegen')
const parentOptions = computed(() => eligibleParentLocations(locations.value, locationId.value))
const selectableTypes = computed(() => isRoot.value
  ? locationTypeItems
  : locationTypeItems.filter((item) => item.value !== 'building'))

const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const parentRule = (value: string | null) => isRoot.value || Boolean(value) || 'Ein übergeordneter Standort ist erforderlich.'

watch(
  [locationId, () => typeof route.query.parent === 'string' ? route.query.parent : null],
  ([id, requestedParent]) => void loadEditor(id, requestedParent),
  { immediate: true }
)

async function save() {
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  saving.value = true
  error.value = null
  try {
    const payload = {
      ...form.value,
      parent_id: isRoot.value ? null : form.value.parent_id,
      location_type: form.value.location_type as LocationType
    }
    const saved = locationId.value
      ? await locationApi.update(locationId.value, payload)
      : await locationApi.create(payload)
    await router.push(`/locations/${saved.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Standort konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-container class="location-editor pa-4 pa-sm-6" fluid>
    <v-btn
      variant="text"
      prepend-icon="mdi-arrow-left"
      :to="locationId ? `/locations/${locationId}` : '/locations'"
      class="mb-3"
    >
      {{ locationId ? 'Zur Detailansicht' : 'Zur Standortübersicht' }}
    </v-btn>
    <div class="mb-5">
      <h1>{{ title }}</h1>
      <p class="text-medium-emphasis">Stammdaten und Position in der Hausstruktur.</p>
    </div>

    <v-skeleton-loader v-if="loading" type="heading, card, card" />
    <v-form v-else ref="formElement" @submit.prevent="save">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
      <v-alert v-if="isRoot" type="info" variant="tonal" class="mb-5">
        Die Gebäudewurzel bleibt der einzige Standort ohne übergeordneten Eintrag.
      </v-alert>

      <v-card title="Allgemein" prepend-icon="mdi-map-marker-outline" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="8">
              <v-text-field v-model="form.name" label="Name" :rules="[requiredRule]" maxlength="150" autofocus />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="form.short_name" label="Kurzname (optional)" maxlength="80" />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="form.description" label="Beschreibung" rows="3" auto-grow />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Hierarchie" prepend-icon="mdi-file-tree-outline" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="5">
              <v-select
                v-model="form.location_type"
                label="Location-Typ"
                :items="selectableTypes"
                :disabled="isRoot"
              />
            </v-col>
            <v-col cols="12" md="5">
              <v-select
                v-model="form.parent_id"
                label="Übergeordneter Standort"
                :items="parentOptions"
                item-title="path"
                item-value="id"
                :rules="[parentRule]"
                :disabled="isRoot"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field
                v-model.number="form.sort_order"
                label="Reihenfolge"
                type="number"
                min="0"
                max="1000000"
                clearable
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Notizen" prepend-icon="mdi-note-text-outline" class="mb-5">
        <v-card-text>
          <v-textarea v-model="form.notes" label="Interne Notizen (optional)" rows="4" auto-grow />
        </v-card-text>
      </v-card>

      <div class="d-flex flex-column-reverse flex-sm-row justify-end ga-3">
        <v-btn variant="text" :to="locationId ? `/locations/${locationId}` : '/locations'">Abbrechen</v-btn>
        <v-btn type="submit" color="primary" prepend-icon="mdi-content-save" :loading="saving">
          Standort speichern
        </v-btn>
      </div>
    </v-form>
  </v-container>
</template>

<style scoped>
.location-editor { max-width: 1100px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
</style>

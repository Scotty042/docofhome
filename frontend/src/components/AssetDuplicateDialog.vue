<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { assetApi } from '../services/assetApi'
import { electricalApi } from '../services/electricalApi'
import type { Asset, AssetDuplicateWrite, AssetSeriesWrite } from '../types/assets'
import type { DistributionArea, DistributionSection, DistributionTreeNode } from '../types/electrical'

const props = defineProps<{ modelValue: boolean; asset: Asset | null }>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [assets: Asset[]]
}>()

const mode = ref<'single' | 'series'>('single')
const saving = ref(false)
const error = ref<string | null>(null)
const singleName = ref('')
const count = ref(2)
const startNumber = ref(1)
const nameTemplate = ref('{name} {n:02}')
const copyLocation = ref(true)
const copyLabels = ref(true)
const copyElectricalRole = ref(true)
const placeSequentially = ref(false)
const distributions = ref<DistributionTreeNode[]>([])
const sections = ref<DistributionSection[]>([])
const distributionId = ref<string | null>(null)
const areaId = ref<string | null>(null)
const rowNumber = ref(1)
const startPosition = ref(1)

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const flatDistributions = computed(() => {
  const result: Array<{ id: string; title: string; layoutMode: 'rows' | 'sections' }> = []
  const visit = (nodes: DistributionTreeNode[], depth = 0) => {
    for (const node of nodes) {
      result.push({ id: node.id, title: `${'— '.repeat(depth)}${node.display_name}`, layoutMode: node.layout_mode })
      visit(node.children, depth + 1)
    }
  }
  visit(distributions.value)
  return result
})
const areas = computed<DistributionArea[]>(() => sections.value.flatMap((section) => section.areas)
  .filter((area) => area.area_type === 'device_rows' && !area.deleted_at))
const selectedDistribution = computed(() => (
  flatDistributions.value.find((item) => item.id === distributionId.value) ?? null
))
const selectedUsesSections = computed(() => selectedDistribution.value?.layoutMode === 'sections')
const seriesPreview = computed(() => {
  try {
    return nameTemplate.value
      .replaceAll('{name}', props.asset?.name ?? 'Asset')
      .replace(/\{n(?::0?(\d+))?\}/g, (_match, width: string | undefined) => (
        String(startNumber.value).padStart(Number(width ?? 0), '0')
      ))
  } catch {
    return 'Ungültiges Namensschema'
  }
})

watch(open, async (value) => {
  if (!value) return
  error.value = null
  mode.value = 'single'
  singleName.value = props.asset ? `${props.asset.name} Kopie` : ''
  count.value = 2
  startNumber.value = 1
  nameTemplate.value = '{name} {n:02}'
  copyLocation.value = true
  copyLabels.value = true
  copyElectricalRole.value = true
  placeSequentially.value = false
  distributionId.value = null
  areaId.value = null
  try {
    distributions.value = await electricalApi.distributionTree()
  } catch {
    distributions.value = []
  }
})

watch(distributionId, async (id) => {
  sections.value = []
  areaId.value = null
  error.value = null
  if (!id || !selectedUsesSections.value) return
  try {
    sections.value = await electricalApi.getLayout(id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verteilungsbereiche konnten nicht geladen werden.'
  }
})

async function save() {
  if (!props.asset) return
  error.value = null
  if (mode.value === 'series' && placeSequentially.value) {
    if (!distributionId.value) {
      error.value = 'Bitte eine Verteilung auswählen.'
      return
    }
    if (selectedUsesSections.value && !areaId.value) {
      error.value = 'Bitte einen DIN-Bereich auswählen.'
      return
    }
  }
  saving.value = true
  try {
    let created: Asset[]
    if (mode.value === 'single') {
      const payload: AssetDuplicateWrite = {
        name: singleName.value.trim() || null,
        copy_location: copyLocation.value,
        copy_labels: copyLabels.value,
        copy_electrical_role: copyElectricalRole.value
      }
      created = [await assetApi.duplicate(props.asset.id, payload)]
    } else {
      const payload: AssetSeriesWrite = {
        count: count.value,
        start_number: startNumber.value,
        name_template: nameTemplate.value.trim(),
        copy_location: copyLocation.value,
        copy_labels: copyLabels.value,
        copy_electrical_role: copyElectricalRole.value,
        place_sequentially: placeSequentially.value,
        distribution_id: placeSequentially.value ? distributionId.value : null,
        area_id: placeSequentially.value && selectedUsesSections.value ? areaId.value : null,
        row_number: placeSequentially.value ? rowNumber.value : null,
        start_position: placeSequentially.value ? startPosition.value : null
      }
      created = (await assetApi.createSeries(props.asset.id, payload)).items
    }
    emit('saved', created)
    open.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset-Kopien konnten nicht angelegt werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-dialog v-model="open" max-width="760" persistent>
    <v-card title="Asset duplizieren oder als Serie anlegen" prepend-icon="mdi-content-copy">
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
        <v-alert type="info" variant="tonal" density="compact" class="mb-4">
          Seriennummer, Inventarnummer, MAC-/IP-Adressen, HA-Zuordnungen, individuelle Fotos und Verkabelungen werden nicht kopiert.
        </v-alert>
        <v-btn-toggle v-model="mode" mandatory color="primary" class="mb-5">
          <v-btn value="single">Eine Kopie</v-btn>
          <v-btn value="series">Serie</v-btn>
        </v-btn-toggle>

        <v-text-field v-if="mode === 'single'" v-model="singleName" label="Name der Kopie" maxlength="150" />
        <v-row v-else>
          <v-col cols="12" sm="4"><v-text-field v-model.number="count" label="Anzahl" type="number" min="1" max="100" /></v-col>
          <v-col cols="12" sm="4"><v-text-field v-model.number="startNumber" label="Startnummer" type="number" min="0" /></v-col>
          <v-col cols="12" sm="4"><v-text-field :model-value="seriesPreview" label="Vorschau" readonly /></v-col>
          <v-col cols="12"><v-text-field v-model="nameTemplate" label="Namensschema" hint="Erlaubt: {name}, {n} oder z. B. {n:02}" persistent-hint /></v-col>
        </v-row>

        <div class="text-subtitle-2 mb-2">Übernehmen</div>
        <div class="d-flex flex-wrap ga-4 mb-4">
          <v-checkbox v-model="copyLocation" label="Ort" hide-details />
          <v-checkbox v-model="copyLabels" label="Labels" hide-details />
          <v-checkbox v-model="copyElectricalRole" label="Technische Gerätedaten" hide-details />
        </div>

        <template v-if="mode === 'series'">
          <v-switch v-model="placeSequentially" label="Fortlaufend im Zählerschrank platzieren" color="primary" inset />
          <v-row v-if="placeSequentially">
            <v-col cols="12" :md="selectedUsesSections ? 6 : 12"><v-select v-model="distributionId" :items="flatDistributions" item-title="title" item-value="id" label="Verteilung" /></v-col>
            <v-col v-if="selectedUsesSections" cols="12" md="6"><v-select v-model="areaId" :items="areas" item-title="name" item-value="id" label="DIN-Bereich" :disabled="!distributionId" /></v-col>
            <v-col v-if="distributionId && !selectedUsesSections" cols="12">
              <v-alert type="info" variant="tonal" density="compact">Diese Verteilung verwendet die einfache Reihenaufteilung. Die Serie wird direkt über Reihe und Startposition platziert.</v-alert>
            </v-col>
            <v-col cols="6"><v-text-field v-model.number="rowNumber" label="Reihe" type="number" min="1" /></v-col>
            <v-col cols="6"><v-text-field v-model.number="startPosition" label="Startposition (TE)" type="number" min="1" /></v-col>
          </v-row>
        </template>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :disabled="saving" @click="open = false">Abbrechen</v-btn>
        <v-btn color="primary" :loading="saving" @click="save">{{ mode === 'series' ? 'Serie anlegen' : 'Duplizieren' }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

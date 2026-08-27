<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { immichApi } from '../services/immichApi'
import { recipeApi } from '../services/recipeApi'
import type { ImmichAlbum, ImmichImage } from '../types/immich'

const modelValue = defineModel<string | null>({ required: true })

const cameraInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const busy = ref(false)
const error = ref('')
const advancedPanel = ref<string | null>(null)
const immichDialog = ref(false)
const immichAlbums = ref<ImmichAlbum[]>([])
const immichImages = ref<ImmichImage[]>([])
const immichAlbumId = ref<string | null>(null)
const immichSearch = ref('')
const immichPage = ref(1)
const immichPages = ref(1)
const immichTotal = ref(0)

const hasImage = computed(() => Boolean(modelValue.value))

function openCamera() {
  cameraInput.value?.click()
}

function openFilePicker() {
  fileInput.value?.click()
}

async function handleNativeInput(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  await upload(file)
}

async function upload(file: File) {
  busy.value = true
  error.value = ''
  try {
    const result = await recipeApi.uploadImage(file)
    modelValue.value = result.image_url
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bild konnte nicht gespeichert werden.'
  } finally {
    busy.value = false
  }
}

async function openImmich() {
  immichDialog.value = true
  error.value = ''
  try {
    if (!immichAlbums.value.length) immichAlbums.value = (await immichApi.albums()).items
    await loadImmichImages()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bilder konnten nicht geladen werden.'
  }
}

async function loadImmichImages() {
  if (!immichDialog.value) return
  busy.value = true
  error.value = ''
  try {
    const result = await immichApi.browse({
      page: immichPage.value,
      page_size: 36,
      search: immichSearch.value.trim() || undefined,
      album_id: immichAlbumId.value || undefined
    })
    immichImages.value = result.items
    immichPages.value = result.pages
    immichTotal.value = result.total
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bilder konnten nicht geladen werden.'
  } finally {
    busy.value = false
  }
}

async function selectImmich(image: ImmichImage) {
  busy.value = true
  error.value = ''
  try {
    const result = await recipeApi.importImmichImage(image.immich_asset_id)
    modelValue.value = result.image_url
    immichDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bild konnte nicht übernommen werden.'
  } finally {
    busy.value = false
  }
}

function removeImage() {
  modelValue.value = null
}

watch(immichAlbumId, () => {
  immichPage.value = 1
  void loadImmichImages()
})
watch(immichPage, () => void loadImmichImages())

onMounted(() => {
  if (modelValue.value?.startsWith('http')) advancedPanel.value = 'advanced'
})
</script>

<template>
  <div class="recipe-image-field">
    <div class="recipe-image-preview">
      <v-img v-if="hasImage" :src="modelValue || ''" height="240" cover class="rounded-lg" />
      <div v-else class="recipe-image-placeholder">
        <v-icon size="64">mdi-image-outline</v-icon>
        <span>Noch kein Rezeptbild</span>
      </div>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mt-3">{{ error }}</v-alert>

    <div class="recipe-image-actions mt-3">
      <v-btn prepend-icon="mdi-camera" color="primary" variant="tonal" :loading="busy" @click="openCamera">Foto aufnehmen</v-btn>
      <v-btn prepend-icon="mdi-image-plus" variant="tonal" :loading="busy" @click="openFilePicker">Bild auswählen</v-btn>
      <v-btn prepend-icon="mdi-image-multiple" variant="tonal" :loading="busy" @click="openImmich">Aus Immich auswählen</v-btn>
      <v-btn v-if="hasImage" prepend-icon="mdi-delete-outline" color="error" variant="text" @click="removeImage">Bild entfernen</v-btn>
    </div>

    <input ref="cameraInput" class="native-image-input" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" @change="handleNativeInput">
    <input ref="fileInput" class="native-image-input" type="file" accept="image/jpeg,image/png,image/webp" @change="handleNativeInput">

    <v-expansion-panels v-model="advancedPanel" class="mt-3" variant="accordion">
      <v-expansion-panel value="advanced">
        <v-expansion-panel-title>Erweitert</v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-text-field
            v-model="modelValue"
            label="Bild-URL (optional)"
            prepend-inner-icon="mdi-link-variant"
            hint="Nur für Sonderfälle. Im Normalfall Foto, Datei oder Immich verwenden."
            persistent-hint
            clearable
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>

  <v-dialog v-model="immichDialog" max-width="1180" scrollable>
    <v-card title="Rezeptbild aus Immich auswählen" prepend-icon="mdi-image-multiple">
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-3">{{ error }}</v-alert>
        <div class="immich-toolbar mb-4">
          <v-select
            v-model="immichAlbumId"
            :items="immichAlbums"
            item-title="album_name"
            item-value="immich_album_id"
            label="Album (optional)"
            clearable
            hide-details
          />
          <v-text-field
            v-model="immichSearch"
            label="Dateiname suchen"
            prepend-inner-icon="mdi-magnify"
            clearable
            hide-details
            @keyup.enter="immichPage = 1; loadImmichImages()"
          />
          <v-btn color="primary" prepend-icon="mdi-magnify" :loading="busy" @click="immichPage = 1; loadImmichImages()">Suchen</v-btn>
        </div>
        <div class="text-caption text-medium-emphasis mb-3">{{ immichTotal }} Bilder gefunden</div>
        <v-skeleton-loader v-if="busy && !immichImages.length" type="image, image, image" />
        <v-row v-else>
          <v-col v-for="image in immichImages" :key="image.immich_asset_id" cols="6" sm="4" md="3" lg="2">
            <v-card class="immich-image-card" variant="outlined" @click="selectImmich(image)">
              <v-img :src="image.thumbnail_url" :alt="image.original_file_name" height="140" cover />
              <v-card-text class="pa-2 text-caption text-truncate" :title="image.original_file_name">{{ image.original_file_name }}</v-card-text>
            </v-card>
          </v-col>
        </v-row>
        <v-pagination v-if="immichPages > 1" v-model="immichPage" :length="immichPages" class="mt-4" />
      </v-card-text>
      <v-card-actions><v-spacer /><v-btn @click="immichDialog = false">Abbrechen</v-btn></v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.recipe-image-field { width: 100%; }
.recipe-image-preview { max-width: 520px; }
.recipe-image-placeholder { display: grid; place-items: center; gap: 6px; height: 240px; border: 1px dashed rgba(var(--v-border-color), .55); border-radius: 12px; color: rgba(var(--v-theme-on-surface), .45); background: rgba(var(--v-theme-primary), .035); }
.recipe-image-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.native-image-input { display: none; }
.immich-toolbar { display: grid; grid-template-columns: minmax(200px, .7fr) minmax(240px, 1fr) auto; gap: 10px; align-items: start; }
.immich-image-card { cursor: pointer; overflow: hidden; transition: transform .12s ease, box-shadow .12s ease; }
.immich-image-card:hover { transform: translateY(-2px); box-shadow: 0 5px 16px rgba(0, 0, 0, .12); }
@media (max-width: 700px) { .immich-toolbar { grid-template-columns: 1fr; } }
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { immichApi } from '../services/immichApi'
import {
  adjacentImmichImage,
  formatImmichDimensions,
  formatImmichTimestamp
} from '../services/immichGallery'
import type { ImmichAlbum, ImmichImage } from '../types/immich'

const loading = ref(false)
const error = ref<string | null>(null)
const images = ref<ImmichImage[]>([])
const albums = ref<ImmichAlbum[]>([])
const albumsLoading = ref(false)
const albumError = ref<string | null>(null)
const search = ref('')
const selectedAlbumId = ref<string | null>(null)
const favoriteOnly = ref(false)
const takenFrom = ref('')
const takenUntil = ref('')
const page = ref(1)
const pages = ref(0)
const total = ref(0)
const selectedImage = ref<ImmichImage | null>(null)
const selectedAlbum = computed(() => (
  albums.value.find((album) => album.immich_album_id === selectedAlbumId.value) ?? null
))
const filtersActive = computed(() => Boolean(
  search.value.trim()
  || selectedAlbumId.value
  || favoriteOnly.value
  || takenFrom.value
  || takenUntil.value
))
const dateRangeError = computed(() => (
  takenFrom.value && takenUntil.value && takenFrom.value > takenUntil.value
    ? 'Das Startdatum darf nicht nach dem Enddatum liegen.'
    : null
))
const previewOpen = computed({
  get: () => selectedImage.value !== null,
  set: (open: boolean) => {
    if (!open) selectedImage.value = null
  }
})
const previousImage = computed(() => selectedImage.value
  ? adjacentImmichImage(images.value, selectedImage.value.immich_asset_id, -1)
  : null)
const nextImage = computed(() => selectedImage.value
  ? adjacentImmichImage(images.value, selectedImage.value.immich_asset_id, 1)
  : null)

function startOfDay(value: string): string | undefined {
  return value ? `${value}T00:00:00` : undefined
}

function endOfDay(value: string): string | undefined {
  return value ? `${value}T23:59:59.999` : undefined
}

function albumTitle(album: ImmichAlbum): string {
  return `${album.album_name} (${album.asset_count})`
}

async function loadAlbums() {
  albumsLoading.value = true
  albumError.value = null
  try {
    albums.value = (await immichApi.albums()).items
  } catch (reason) {
    albums.value = []
    selectedAlbumId.value = null
    albumError.value = reason instanceof Error
      ? reason.message
      : 'Die Immich-Alben konnten nicht geladen werden.'
  } finally {
    albumsLoading.value = false
  }
}

async function load(targetPage = 1) {
  if (dateRangeError.value) {
    error.value = dateRangeError.value
    return
  }
  loading.value = true
  error.value = null
  selectedImage.value = null
  try {
    const result = await immichApi.browse({
      page: targetPage,
      page_size: 36,
      search: search.value.trim() || undefined,
      album_id: selectedAlbumId.value || undefined,
      favorite_only: favoriteOnly.value || undefined,
      taken_after: startOfDay(takenFrom.value),
      taken_before: endOfDay(takenUntil.value)
    })
    images.value = result.items
    page.value = result.page
    pages.value = result.pages
    total.value = result.total
  } catch (reason) {
    images.value = []
    pages.value = 0
    total.value = 0
    error.value = reason instanceof Error
      ? reason.message
      : 'Die Immich-Bilder konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  search.value = ''
  selectedAlbumId.value = null
  favoriteOnly.value = false
  takenFrom.value = ''
  takenUntil.value = ''
  void load(1)
}

function openPreview(image: ImmichImage) {
  selectedImage.value = image
}

function showAdjacent(image: ImmichImage | null) {
  if (image) selectedImage.value = image
}

onMounted(() => {
  void loadAlbums()
  void load(1)
})
</script>

<template>
  <v-container class="gallery-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
      <div>
        <h1>Bilder</h1>
        <p class="text-medium-emphasis mb-0">
          Zentrale, schreibgeschützte Ansicht deiner technischen Fotos aus Immich.
        </p>
      </div>
      <v-chip prepend-icon="mdi-image-multiple-outline" color="primary" variant="tonal">
        {{ total }} Bilder
      </v-chip>
    </div>

    <v-alert type="info" variant="tonal" density="compact" class="mb-4">
      DocOfHome zeigt Vorschaubilder über den eigenen Server an. API-Key und interne Immich-URL
      werden niemals an den Browser weitergegeben; Bilder und Alben werden in Immich nicht verändert.
    </v-alert>

    <v-card class="mb-5" variant="outlined">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              label="Nach Dateiname suchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              @keyup.enter="load(1)"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedAlbumId"
              :items="albums"
              :item-title="albumTitle"
              item-value="immich_album_id"
              label="Immich-Album"
              prepend-inner-icon="mdi-image-album"
              :loading="albumsLoading"
              clearable
              hide-details
              @update:model-value="load(1)"
            />
          </v-col>
          <v-col cols="12" md="4" class="d-flex align-center">
            <v-switch
              v-model="favoriteOnly"
              color="warning"
              label="Nur Immich-Favoriten"
              hide-details
              inset
              @update:model-value="load(1)"
            />
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-text-field
              v-model="takenFrom"
              type="date"
              label="Aufgenommen ab"
              prepend-inner-icon="mdi-calendar-start"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-text-field
              v-model="takenUntil"
              type="date"
              label="Aufgenommen bis"
              prepend-inner-icon="mdi-calendar-end"
              clearable
              hide-details
            />
          </v-col>
        </v-row>
        <v-alert v-if="albumError" type="warning" variant="tonal" density="compact" class="mt-3">
          {{ albumError }} Für die Albumübersicht benötigt der Immich-API-Key zusätzlich
          <code>album.read</code>. Die normale Bildergalerie bleibt nutzbar.
        </v-alert>
        <v-alert v-if="dateRangeError" type="error" variant="tonal" density="compact" class="mt-3">
          {{ dateRangeError }}
        </v-alert>
        <div class="d-flex flex-wrap ga-3 mt-4">
          <v-btn
            color="primary"
            prepend-icon="mdi-filter-check-outline"
            :loading="loading"
            :disabled="Boolean(dateRangeError)"
            @click="load(1)"
          >
            Filter anwenden
          </v-btn>
          <v-btn
            variant="tonal"
            prepend-icon="mdi-filter-remove-outline"
            :disabled="!filtersActive"
            @click="resetFilters"
          >
            Zurücksetzen
          </v-btn>
          <v-chip
            v-if="selectedAlbum"
            color="primary"
            variant="tonal"
            prepend-icon="mdi-image-album"
          >
            {{ selectedAlbum.album_name }} · {{ selectedAlbum.asset_count }} Medien
          </v-chip>
          <v-chip v-if="favoriteOnly" color="warning" variant="tonal" prepend-icon="mdi-star">
            Nur Favoriten
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <v-alert v-if="error" type="warning" variant="tonal" class="mb-5">
      {{ error }}
    </v-alert>

    <v-skeleton-loader v-if="loading" type="image, image, image" />

    <v-alert v-else-if="images.length === 0" type="info" variant="tonal">
      Keine Bilder für die aktuellen Filter gefunden.
    </v-alert>

    <v-row v-else>
      <v-col
        v-for="image in images"
        :key="image.immich_asset_id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <v-card
          class="image-card"
          variant="outlined"
          height="100%"
          tabindex="0"
          role="button"
          :aria-label="`${image.original_file_name} vergrößert anzeigen`"
          @click="openPreview(image)"
          @keyup.enter="openPreview(image)"
          @keyup.space.prevent="openPreview(image)"
        >
          <v-img
            :src="image.thumbnail_url"
            :alt="image.original_file_name"
            aspect-ratio="1.333"
            cover
            class="image-thumbnail"
          >
            <v-chip
              v-if="image.is_favorite"
              class="ma-2"
              color="warning"
              size="small"
              prepend-icon="mdi-star"
            >
              Favorit
            </v-chip>
            <template #error>
              <div class="d-flex fill-height align-center justify-center bg-surface-variant">
                <v-icon icon="mdi-image-off-outline" size="48" />
              </div>
            </template>
          </v-img>
          <v-card-text>
            <div class="font-weight-medium file-name">{{ image.original_file_name }}</div>
            <div class="text-caption text-medium-emphasis">
              {{ formatImmichTimestamp(image.file_created_at) }}
            </div>
            <div class="text-caption text-medium-emphasis mt-1">
              {{ formatImmichDimensions(image) }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-pagination
      v-if="pages > 1"
      v-model="page"
      :length="pages"
      :total-visible="7"
      class="mt-6"
      @update:model-value="load"
    />

    <v-dialog v-model="previewOpen" max-width="1100" scrollable>
      <v-card v-if="selectedImage" class="preview-card">
        <v-toolbar density="comfortable" color="surface">
          <v-toolbar-title class="preview-title">{{ selectedImage.original_file_name }}</v-toolbar-title>
          <v-btn icon="mdi-close" aria-label="Vorschau schließen" title="Vorschau schließen" @click="previewOpen = false" />
        </v-toolbar>
        <v-card-text class="pa-0">
          <div class="preview-stage">
            <v-btn
              icon="mdi-chevron-left"
              variant="tonal"
              class="preview-navigation preview-navigation-left"
              aria-label="Vorheriges Bild"
              title="Vorheriges Bild"
              :disabled="!previousImage"
              @click="showAdjacent(previousImage)"
            />
            <v-img
              :src="selectedImage.thumbnail_url"
              :alt="selectedImage.original_file_name"
              max-height="72vh"
              contain
              class="preview-image"
            >
              <template #error>
                <div class="d-flex fill-height align-center justify-center bg-surface-variant">
                  <v-icon icon="mdi-image-off-outline" size="64" />
                </div>
              </template>
            </v-img>
            <v-btn
              icon="mdi-chevron-right"
              variant="tonal"
              class="preview-navigation preview-navigation-right"
              aria-label="Nächstes Bild"
              title="Nächstes Bild"
              :disabled="!nextImage"
              @click="showAdjacent(nextImage)"
            />
          </div>
        </v-card-text>
        <v-card-actions class="flex-wrap ga-2 px-4 py-3">
          <v-chip v-if="selectedImage.is_favorite" color="warning" prepend-icon="mdi-star" variant="tonal">
            Immich-Favorit
          </v-chip>
          <span class="text-body-2 text-medium-emphasis">
            {{ formatImmichTimestamp(selectedImage.file_created_at) }} · {{ formatImmichDimensions(selectedImage) }}
          </span>
          <v-spacer />
          <span class="text-caption text-medium-emphasis">Nur Vorschau · keine Originaldatei wird übertragen</span>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.gallery-page { max-width: 1500px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.4rem); }
.image-card { cursor: pointer; overflow: hidden; transition: transform .15s ease, box-shadow .15s ease; }
.image-card:hover, .image-card:focus-visible { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, .18); outline: 2px solid rgb(var(--v-theme-primary)); outline-offset: 2px; }
.image-thumbnail { background: rgba(var(--v-theme-on-surface), .04); }
.file-name, .preview-title { overflow-wrap: anywhere; }
.preview-stage { position: relative; display: flex; align-items: center; justify-content: center; min-height: 320px; background: rgba(var(--v-theme-on-surface), .04); }
.preview-image { width: 100%; }
.preview-navigation { position: absolute; top: 50%; z-index: 2; transform: translateY(-50%); }
.preview-navigation-left { left: 12px; }
.preview-navigation-right { right: 12px; }
@media (max-width: 600px) {
  .preview-navigation-left { left: 4px; }
  .preview-navigation-right { right: 4px; }
}
</style>

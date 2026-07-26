<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { immichApi } from '../services/immichApi'
import { selectedImmichAlbumId } from '../services/immichGallery'
import { settingsApi } from '../services/settingsApi'
import type { ImmichImage } from '../types/immich'

const assetId = defineModel<string | null>('assetId', { default: null })
const fileName = defineModel<string | null>('fileName', { default: null })

const loading = ref(false)
const error = ref<string | null>(null)
const albumId = ref<string | null>(null)
const search = ref('')
const images = ref<ImmichImage[]>([])
const selected = computed(() => images.value.find((item) => item.immich_asset_id === assetId.value) ?? null)

async function load() {
  if (!albumId.value) return
  loading.value = true
  error.value = null
  try {
    const result = await immichApi.browse({
      album_id: albumId.value,
      page: 1,
      page_size: 36,
      search: search.value.trim() || undefined
    })
    images.value = result.items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bilder konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function choose(image: ImmichImage) {
  assetId.value = image.immich_asset_id
  fileName.value = image.original_file_name
}

function clear() {
  assetId.value = null
  fileName.value = null
}

onMounted(async () => {
  try {
    albumId.value = selectedImmichAlbumId(await settingsApi.read())
    if (albumId.value) await load()
  } catch {
    // Immich is optional; the manual reading remains available.
  }
})
</script>

<template>
  <v-card variant="outlined" class="mt-3">
    <v-card-title class="text-subtitle-1 d-flex align-center ga-2">
      <v-icon icon="mdi-image-outline" /> Zählerfoto aus Immich
      <v-spacer />
      <v-btn v-if="assetId" size="small" variant="text" prepend-icon="mdi-close" @click="clear">Entfernen</v-btn>
    </v-card-title>
    <v-card-text>
      <v-alert v-if="!albumId" type="info" variant="tonal" density="compact">
        In den Einstellungen ist noch kein Immich-Album ausgewählt. Die Ablesung kann trotzdem gespeichert werden.
      </v-alert>
      <template v-else>
        <div class="d-flex ga-2 mb-3">
          <v-text-field v-model="search" label="Foto suchen" prepend-inner-icon="mdi-magnify" hide-details clearable @keyup.enter="load" />
          <v-btn :loading="loading" variant="tonal" icon="mdi-refresh" aria-label="Immich-Bilder laden" @click="load" />
        </div>
        <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
        <v-row dense class="image-grid">
          <v-col v-for="image in images" :key="image.immich_asset_id" cols="4" sm="3">
            <button
              type="button"
              class="image-choice"
              :class="{ selected: image.immich_asset_id === assetId }"
              :aria-label="`${image.original_file_name} auswählen`"
              @click="choose(image)"
            >
              <v-img :src="image.thumbnail_url" :alt="image.original_file_name" aspect-ratio="1" cover />
              <span class="image-name">{{ image.original_file_name }}</span>
              <v-icon v-if="image.immich_asset_id === assetId" class="selected-icon" icon="mdi-check-circle" color="primary" />
            </button>
          </v-col>
        </v-row>
        <div v-if="selected" class="text-caption mt-2">Ausgewählt: {{ selected.original_file_name }}</div>
      </template>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.image-grid { max-height: 330px; overflow-y: auto; }
.image-choice { position: relative; width: 100%; padding: 0; border: 2px solid transparent; border-radius: 8px; overflow: hidden; background: transparent; color: inherit; cursor: pointer; text-align: left; }
.image-choice.selected { border-color: rgb(var(--v-theme-primary)); }
.image-choice:focus-visible { outline: 3px solid rgb(var(--v-theme-primary)); outline-offset: 2px; }
.image-name { display: block; padding: 4px 6px; font-size: .68rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.selected-icon { position: absolute; top: 5px; right: 5px; filter: drop-shadow(0 1px 2px rgba(0, 0, 0, .55)); }
</style>

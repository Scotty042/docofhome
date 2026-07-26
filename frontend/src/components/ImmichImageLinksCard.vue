<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { immichApi } from '../services/immichApi'
import {
  albumImageQuery,
  formatImmichTimestamp,
  linkedImmichAssetIds,
  prependImmichLink,
  selectedImmichAlbumId
} from '../services/immichGallery'
import { settingsApi } from '../services/settingsApi'
import type { ImmichAssetLink, ImmichImage } from '../types/immich'

const props = withDefaults(defineProps<{
  assetId: string
  readOnly?: boolean
  title?: string
  emptyText?: string
}>(), {
  readOnly: false,
  title: 'Immich-Fotos',
  emptyText: 'Noch keine Immich-Fotos verknüpft.'
})

const links = ref<ImmichAssetLink[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const dialog = ref(false)
const previewDialog = ref(false)
const previewLink = ref<ImmichAssetLink | null>(null)
const browseLoading = ref(false)
const candidates = ref<ImmichImage[]>([])
const search = ref('')
const page = ref(1)
const pages = ref(0)
const total = ref(0)
const selectedAlbumId = ref<string | null>(null)
const selectedAlbumName = ref<string | null>(null)
const linkingIds = ref<Set<string>>(new Set())
const unlinkingIds = ref<Set<string>>(new Set())
const linkedIds = computed(() => linkedImmichAssetIds(links.value))
const albumLabel = computed(() => selectedAlbumName.value || selectedAlbumId.value)

async function loadLinks() {
  if (!props.assetId) return
  loading.value = true
  error.value = null
  try {
    links.value = (await immichApi.links(props.assetId)).items
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Immich-Verknüpfungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadAlbumSelection() {
  selectedAlbumId.value = null
  selectedAlbumName.value = null
  const configuration = await settingsApi.read()
  selectedAlbumId.value = selectedImmichAlbumId(configuration)
  if (!selectedAlbumId.value) return
  try {
    const albums = (await immichApi.albums()).items
    selectedAlbumName.value = albums.find(
      (album) => album.immich_album_id === selectedAlbumId.value
    )?.album_name ?? null
  } catch {
    // The stored album ID is sufficient for browsing if the album list is temporarily unavailable.
  }
}

function openPreview(link: ImmichAssetLink) {
  previewLink.value = link
  previewDialog.value = true
}

async function openDialog() {
  dialog.value = true
  search.value = ''
  candidates.value = []
  page.value = 1
  pages.value = 0
  total.value = 0
  error.value = null
  try {
    await loadAlbumSelection()
    if (selectedAlbumId.value) await browse(1)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Das ausgewählte Immich-Album konnte nicht geladen werden.'
  }
}

async function browse(targetPage = 1) {
  if (!selectedAlbumId.value) return
  browseLoading.value = true
  error.value = null
  try {
    const result = await immichApi.browse(
      albumImageQuery(selectedAlbumId.value, targetPage, search.value)
    )
    candidates.value = result.items
    page.value = result.page
    pages.value = result.pages
    total.value = result.total
  } catch (reason) {
    candidates.value = []
    error.value = reason instanceof Error
      ? reason.message
      : 'Immich-Fotos konnten nicht geladen werden.'
  } finally {
    browseLoading.value = false
  }
}

async function linkImage(image: ImmichImage) {
  if (linkedIds.value.has(image.immich_asset_id)) return
  linkingIds.value = new Set(linkingIds.value).add(image.immich_asset_id)
  error.value = null
  try {
    const created = await immichApi.createLink(props.assetId, image.immich_asset_id)
    links.value = prependImmichLink(links.value, created)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Immich-Foto konnte nicht verknüpft werden.'
  } finally {
    const next = new Set(linkingIds.value)
    next.delete(image.immich_asset_id)
    linkingIds.value = next
  }
}

async function unlinkImage(link: ImmichAssetLink) {
  unlinkingIds.value = new Set(unlinkingIds.value).add(link.id)
  error.value = null
  try {
    await immichApi.removeLink(link.id)
    links.value = links.value.filter((item) => item.id !== link.id)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Immich-Verknüpfung konnte nicht entfernt werden.'
  } finally {
    const next = new Set(unlinkingIds.value)
    next.delete(link.id)
    unlinkingIds.value = next
  }
}

onMounted(loadLinks)
watch(() => props.assetId, loadLinks)
</script>

<template>
  <v-card :title="title" prepend-icon="mdi-image-multiple" class="mb-5">
    <template #append>
      <v-btn
        v-if="!readOnly"
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-image-plus-outline"
        @click="openDialog"
      >
        Fotos verknüpfen
      </v-btn>
    </template>
    <v-card-text>
      <v-alert v-if="error && !dialog" type="warning" variant="tonal" class="mb-4">
        {{ error }}
      </v-alert>
      <v-skeleton-loader v-if="loading" type="image, image" />
      <v-row v-else-if="links.length">
        <v-col v-for="link in links" :key="link.id" cols="12" sm="6" md="4">
          <v-card variant="outlined" class="immich-tile" height="100%">
            <v-img
              :src="link.thumbnail_url"
              :alt="link.original_file_name"
              aspect-ratio="1.333"
              cover
              class="immich-thumbnail cursor-pointer"
              role="button"
              tabindex="0"
              title="Bild vergrößern"
              @click="openPreview(link)"
              @keydown.enter="openPreview(link)"
              @keydown.space.prevent="openPreview(link)"
            >
              <template #error>
                <div class="d-flex fill-height align-center justify-center bg-surface-variant">
                  <v-icon icon="mdi-image-off-outline" size="42" />
                </div>
              </template>
            </v-img>
            <v-card-text class="pb-2">
              <div class="font-weight-medium immich-file-name">{{ link.original_file_name }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ formatImmichTimestamp(link.file_created_at) }}
              </div>
            </v-card-text>
            <v-card-actions v-if="!readOnly">
              <v-spacer />
              <v-btn
                size="small"
                color="error"
                variant="text"
                prepend-icon="mdi-link-variant-off"
                :loading="unlinkingIds.has(link.id)"
                @click="unlinkImage(link)"
              >
                Verknüpfung lösen
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
      <div v-else class="text-medium-emphasis">{{ emptyText }}</div>
    </v-card-text>
  </v-card>

  <v-dialog v-model="previewDialog" max-width="1400">
    <v-card v-if="previewLink" :title="previewLink.original_file_name" prepend-icon="mdi-image">
      <v-card-text class="pa-2 pa-sm-4">
        <v-img
          :src="previewLink.thumbnail_url"
          :alt="previewLink.original_file_name"
          max-height="82vh"
          contain
          class="bg-black rounded"
        />
        <div class="text-caption text-medium-emphasis mt-2">
          {{ formatImmichTimestamp(previewLink.file_created_at) }}
          <span v-if="previewLink.width && previewLink.height"> · {{ previewLink.width }} × {{ previewLink.height }} px</span>
        </div>
      </v-card-text>
      <v-card-actions><v-spacer /><v-btn @click="previewDialog = false">Schließen</v-btn></v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="dialog" max-width="1200" scrollable>
    <v-card prepend-icon="mdi-image-multiple" title="Immich-Fotos verknüpfen">
      <v-card-text>
        <v-alert type="info" variant="tonal" density="compact" class="mb-4">
          DocOfHome liest nur Bilder und Vorschaudaten. In Immich wird nichts verändert.
        </v-alert>
        <v-alert v-if="!selectedAlbumId" type="warning" variant="tonal" class="mb-4">
          Wähle zuerst in den Einstellungen ein Immich-Album aus.
          <template #append>
            <v-btn variant="text" to="/settings">Zu den Einstellungen</v-btn>
          </template>
        </v-alert>
        <v-alert v-else type="success" variant="tonal" density="compact" class="mb-4">
          Album: <strong>{{ albumLabel }}</strong>. Alle Albumseiten können durchsucht und geöffnet werden.
        </v-alert>
        <v-alert v-if="error" type="warning" variant="tonal" class="mb-4">
          {{ error }}
        </v-alert>
        <div class="d-flex flex-column flex-sm-row ga-2 mb-4">
          <v-text-field
            v-model="search"
            label="Im ausgewählten Album nach Dateiname suchen"
            prepend-inner-icon="mdi-magnify"
            clearable
            hide-details
            :disabled="!selectedAlbumId"
            @keyup.enter="browse(1)"
          />
          <v-btn
            color="primary"
            prepend-icon="mdi-magnify"
            :loading="browseLoading"
            :disabled="!selectedAlbumId"
            @click="browse(1)"
          >
            Suchen
          </v-btn>
        </div>
        <div v-if="selectedAlbumId" class="d-flex flex-wrap align-center ga-2 mb-3">
          <v-chip variant="tonal">{{ total }} Bilder im Ergebnis</v-chip>
          <v-chip color="primary" variant="tonal">{{ links.length }} verknüpft</v-chip>
          <v-chip v-if="pages > 1" variant="outlined">Seite {{ page }} von {{ pages }}</v-chip>
        </div>
        <v-skeleton-loader v-if="browseLoading" type="image, image, image" />
        <v-alert
          v-else-if="selectedAlbumId && candidates.length === 0"
          type="info"
          variant="tonal"
        >
          Keine Bilder im ausgewählten Album für die aktuelle Suche gefunden.
        </v-alert>
        <v-row v-else-if="selectedAlbumId">
          <v-col
            v-for="image in candidates"
            :key="image.immich_asset_id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card variant="outlined" height="100%" class="immich-tile">
              <v-img
                :src="image.thumbnail_url"
                :alt="image.original_file_name"
                aspect-ratio="1.333"
                cover
                class="immich-thumbnail"
              >
                <template #error>
                  <div class="d-flex fill-height align-center justify-center bg-surface-variant">
                    <v-icon icon="mdi-image-off-outline" size="42" />
                  </div>
                </template>
              </v-img>
              <v-card-text class="pb-2">
                <div class="font-weight-medium immich-file-name">{{ image.original_file_name }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ formatImmichTimestamp(image.file_created_at) }}
                </div>
              </v-card-text>
              <v-card-actions>
                <v-btn
                  block
                  size="small"
                  :color="linkedIds.has(image.immich_asset_id) ? 'success' : 'primary'"
                  :variant="linkedIds.has(image.immich_asset_id) ? 'tonal' : 'flat'"
                  :prepend-icon="linkedIds.has(image.immich_asset_id) ? 'mdi-check' : 'mdi-link-plus'"
                  :disabled="linkedIds.has(image.immich_asset_id)"
                  :loading="linkingIds.has(image.immich_asset_id)"
                  @click="linkImage(image)"
                >
                  {{ linkedIds.has(image.immich_asset_id) ? 'Verknüpft' : 'Verknüpfen' }}
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        <v-pagination
          v-if="pages > 1"
          v-model="page"
          :length="pages"
          :total-visible="7"
          class="mt-5"
          aria-label="Seiten des ausgewählten Immich-Albums"
          @update:model-value="browse"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="dialog = false">Schließen</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.immich-thumbnail { background: rgba(var(--v-theme-on-surface), .04); }
.immich-file-name { overflow-wrap: anywhere; }
.immich-tile { overflow: hidden; }
</style>

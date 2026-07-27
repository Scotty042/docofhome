<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { AssetApiError, assetApi } from '../services/assetApi'
import { immichApi } from '../services/immichApi'
import { downloadWikimediaImageInBrowser, searchWikimediaInBrowser } from '../services/productImageSearch'
import { useNotificationStore } from '../stores/notifications'
import type { ProductImageSearchItem, ProductImageSource } from '../types/assets'
import type { ImmichAlbum, ImmichImage } from '../types/immich'

const props = withDefaults(defineProps<{
  modelValue?: string | null
  source?: ProductImageSource
  reference?: string | null
  searchTerms?: string
}>(), {
  modelValue: null,
  source: 'url',
  reference: null,
  searchTerms: ''
})
const notifications = useNotificationStore()
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'update:source': [value: ProductImageSource]
  'update:reference': [value: string | null]
}>()

const previewFailed = ref(false)
const previewDialog = ref(false)
const tab = ref<ProductImageSource>('url')
const busy = ref(false)
const error = ref<string | null>(null)
const immichDialog = ref(false)
const immichAlbums = ref<ImmichAlbum[]>([])
const immichImages = ref<ImmichImage[]>([])
const immichAlbumId = ref<string | null>(null)
const immichSearch = ref('')
const immichPage = ref(1)
const immichPages = ref(1)
const onlineQuery = ref('')
const onlineItems = ref<ProductImageSearchItem[]>([])
const onlineStatus = ref<string | null>(null)
const onlineStatusType = ref<'info' | 'warning'>('info')
const browserFallbackActive = ref(false)
let onlineSearchController: AbortController | null = null
let onlineImportController: AbortController | null = null
let immichTimer: ReturnType<typeof setTimeout> | undefined

async function withRequestTimeout<T>(
  parentSignal: AbortSignal,
  timeoutMs: number,
  request: (signal: AbortSignal) => Promise<T>
): Promise<T> {
  const controller = new AbortController()
  const abortFromParent = () => controller.abort(parentSignal.reason)
  if (parentSignal.aborted) abortFromParent()
  else parentSignal.addEventListener('abort', abortFromParent, { once: true })
  const timer = setTimeout(() => {
    controller.abort(new DOMException('Zeitüberschreitung', 'TimeoutError'))
  }, timeoutMs)
  try {
    return await request(controller.signal)
  } finally {
    clearTimeout(timer)
    parentSignal.removeEventListener('abort', abortFromParent)
  }
}

function requestErrorMessage(reason: unknown, fallback: string): string {
  if (reason instanceof DOMException && reason.name === 'TimeoutError') {
    return 'Zeitüberschreitung beim externen Zugriff.'
  }
  return reason instanceof Error ? reason.message : fallback
}

const hasImage = computed(() => Boolean(props.modelValue))
const sourceLabel = computed(() => ({
  url: 'Manuelle URL', upload: 'Upload', immich: 'Immich', online: 'Online-Suche'
}[props.source]))

watch(error, (message) => {
  if (message) notifications.error(message)
})
watch(() => props.modelValue, () => { previewFailed.value = false })
watch(() => props.source, (value) => { tab.value = value })
watch(immichSearch, () => {
  immichPage.value = 1
  clearTimeout(immichTimer)
  immichTimer = setTimeout(() => void loadImmichImages(), 300)
})
watch(immichAlbumId, () => {
  immichPage.value = 1
  void loadImmichImages()
})
watch(immichPage, () => void loadImmichImages())

onMounted(() => {
  tab.value = props.source
  onlineQuery.value = props.searchTerms.trim()
})

onBeforeUnmount(() => {
  clearTimeout(immichTimer)
  onlineSearchController?.abort()
  onlineImportController?.abort()
})

const imageRule = (value: string | null) => {
  if (!value?.trim()) return true
  return /^(https?:\/\/|\/(?!\/))/.test(value.trim())
    || 'HTTPS-/HTTP-URL oder lokaler Pfad beginnend mit / erforderlich.'
}

function applyImage(url: string | null, source: ProductImageSource, reference: string | null) {
  emit('update:modelValue', url)
  emit('update:source', source)
  emit('update:reference', reference)
  previewFailed.value = false
  error.value = null
}

function removeImage() {
  applyImage(null, 'url', null)
}

async function upload(files: File | File[] | null) {
  const file = Array.isArray(files) ? files[0] : files
  if (!file) return
  busy.value = true
  error.value = null
  try {
    const result = await assetApi.uploadProductImage(file)
    applyImage(result.image_url, result.image_source, result.image_reference)
    tab.value = 'upload'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bild konnte nicht hochgeladen werden.'
  } finally {
    busy.value = false
  }
}

async function openImmich() {
  immichDialog.value = true
  busy.value = true
  error.value = null
  try {
    if (!immichAlbums.value.length) immichAlbums.value = (await immichApi.albums()).items
    await loadImmichImages()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bilder konnten nicht geladen werden.'
  } finally {
    busy.value = false
  }
}

async function loadImmichImages() {
  if (!immichDialog.value) return
  busy.value = true
  try {
    const page = await immichApi.browse({
      page: immichPage.value,
      page_size: 36,
      search: immichSearch.value.trim() || undefined,
      album_id: immichAlbumId.value || undefined
    })
    immichImages.value = page.items
    immichPages.value = page.pages
  } finally {
    busy.value = false
  }
}

function selectImmich(image: ImmichImage) {
  applyImage(image.thumbnail_url, 'immich', image.immich_asset_id)
  tab.value = 'immich'
  immichDialog.value = false
}

async function searchOnline() {
  const query = onlineQuery.value.trim() || props.searchTerms.trim()
  if (query.length < 2) {
    error.value = 'Bitte mindestens zwei Suchzeichen eingeben.'
    return
  }
  onlineSearchController?.abort()
  const controller = new AbortController()
  onlineSearchController = controller
  busy.value = true
  error.value = null
  onlineStatus.value = null
  browserFallbackActive.value = false
  onlineItems.value = []
  try {
    const result = await withRequestTimeout(
      controller.signal,
      14_000,
      (signal) => assetApi.searchProductImages(query, signal)
    )
    if (controller.signal.aborted) return
    onlineItems.value = result.items
    onlineStatus.value = result.items.length
      ? null
      : 'Für diesen Suchbegriff wurden keine Bilder gefunden.'
    onlineStatusType.value = 'info'
  } catch (backendReason) {
    if (controller.signal.aborted) return
    const backendUnavailable = !(backendReason instanceof AssetApiError)
      || backendReason.status === 502
      || backendReason.status >= 500
    if (!backendUnavailable) {
      error.value = backendReason instanceof Error
        ? backendReason.message
        : 'Backend-Suche konnte nicht ausgeführt werden.'
      return
    }
    onlineStatus.value = 'Die Backend-Suche ist nicht erreichbar. DocOfHome verwendet die direkte Browser-Suche bei Wikimedia.'
    onlineStatusType.value = 'warning'
    try {
      const items = await withRequestTimeout(
        controller.signal,
        14_000,
        (signal) => searchWikimediaInBrowser(query, { signal })
      )
      if (controller.signal.aborted) return
      onlineItems.value = items
      browserFallbackActive.value = true
      if (!items.length) {
        onlineStatus.value = 'Die Browser-Suche war erreichbar, hat aber keine Treffer geliefert.'
        onlineStatusType.value = 'info'
      }
    } catch (browserReason) {
      if (controller.signal.aborted) return
      const backendMessage = requestErrorMessage(backendReason, 'Backend nicht erreichbar')
      const browserMessage = requestErrorMessage(browserReason, 'Externe Suche nicht erreichbar')
      error.value = `Backend-Suche nicht erreichbar: ${backendMessage} Browser-Suche nicht erreichbar: ${browserMessage}`
      onlineStatus.value = null
    }
  } finally {
    if (onlineSearchController === controller) {
      onlineSearchController = null
      busy.value = false
    }
  }
}

async function importOnline(item: ProductImageSearchItem) {
  onlineImportController?.abort()
  const controller = new AbortController()
  onlineImportController = controller
  busy.value = true
  error.value = null
  onlineStatus.value = null
  try {
    if (!browserFallbackActive.value) {
      try {
        const result = await withRequestTimeout(
          controller.signal,
          16_000,
          (signal) => assetApi.importProductImage(item.image_url, item.source_url, signal)
        )
        applyImage(result.image_url, 'online', item.source_url)
        tab.value = 'online'
        notifications.success('Das gewählte Produktbild wurde lokal gespeichert.')
        return
      } catch (reason) {
        const backendUnavailable = !(reason instanceof AssetApiError)
          || reason.status === 502
          || reason.status >= 500
        if (!backendUnavailable) throw reason
        onlineStatus.value = 'Der Container konnte das Bild nicht herunterladen. Der Browser übernimmt den Download und lädt es lokal zu DocOfHome hoch.'
        onlineStatusType.value = 'warning'
      }
    }
    const file = await withRequestTimeout(
      controller.signal,
      16_000,
      (signal) => downloadWikimediaImageInBrowser(item, { signal })
    )
    const result = await withRequestTimeout(
      controller.signal,
      16_000,
      (signal) => assetApi.uploadProductImage(file, signal)
    )
    if (controller.signal.aborted) return
    applyImage(result.image_url, 'online', item.source_url)
    tab.value = 'online'
    notifications.success('Das gewählte Produktbild wurde lokal gespeichert.')
  } catch (reason) {
    if (controller.signal.aborted) return
    error.value = `Bilddownload fehlgeschlagen: ${requestErrorMessage(reason, 'Unbekannter Fehler')}`
  } finally {
    if (onlineImportController === controller) {
      onlineImportController = null
      busy.value = false
    }
  }
}
</script>

<template>
  <div>
    <div class="d-flex flex-wrap align-center ga-2 mb-2">
      <div class="text-subtitle-1 font-weight-medium">Produktbild</div>
      <v-chip v-if="hasImage" size="small" color="primary" variant="tonal">{{ sourceLabel }}</v-chip>
      <v-spacer />
      <v-btn v-if="hasImage" size="small" variant="text" prepend-icon="mdi-delete-outline" color="error" @click="removeImage">
        Entfernen
      </v-btn>
    </div>
    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-3">{{ error }}</v-alert>

    <v-tabs v-model="tab" density="compact" show-arrows>
      <v-tab value="upload" prepend-icon="mdi-upload">Upload</v-tab>
      <v-tab value="immich" prepend-icon="mdi-image-multiple">Immich</v-tab>
      <v-tab value="online" prepend-icon="mdi-web">Online</v-tab>
      <v-tab value="url" prepend-icon="mdi-link-variant">URL</v-tab>
    </v-tabs>
    <v-window v-model="tab" class="mt-3">
      <v-window-item value="upload">
        <v-file-input
          label="Bild auswählen oder hier ablegen"
          accept="image/jpeg,image/png,image/webp,image/gif"
          prepend-icon="mdi-image-plus"
          :loading="busy"
          show-size
          @update:model-value="upload"
        />
        <div class="text-caption text-medium-emphasis">JPEG, PNG, WebP oder GIF, maximal 10 MB. Das Bild wird lokal gespeichert.</div>
      </v-window-item>
      <v-window-item value="immich">
        <v-btn color="primary" variant="tonal" prepend-icon="mdi-image-search" :loading="busy" @click="openImmich">
          Aus Immich auswählen
        </v-btn>
      </v-window-item>
      <v-window-item value="online">
        <div class="d-flex ga-2 align-start">
          <v-text-field
            v-model="onlineQuery"
            label="Produktbild suchen"
            :placeholder="searchTerms || 'Hersteller Produkt Modell'"
            prepend-inner-icon="mdi-magnify"
            hide-details
            @keyup.enter="searchOnline"
          />
          <v-btn color="primary" :loading="busy" class="mt-1" @click="searchOnline">Suchen</v-btn>
        </div>
        <v-alert type="info" variant="tonal" density="compact" class="mt-3">
          Die Suche verwendet primär DuckDuckGo Images und bei Bedarf Wikimedia Commons. Hersteller, Modell und Produktname liefern die besten Treffer. Erst der ausdrücklich gewählte Treffer wird lokal gespeichert.
        </v-alert>
        <v-alert v-if="onlineStatus" :type="onlineStatusType" variant="tonal" density="compact" class="mt-3">
          {{ onlineStatus }}
        </v-alert>
        <v-row v-if="onlineItems.length" class="mt-2" dense>
          <v-col v-for="item in onlineItems" :key="item.image_url" cols="6" sm="4" md="3">
            <v-card variant="outlined" height="100%" @click="importOnline(item)">
              <v-img :src="item.thumbnail_url" height="130" cover />
              <v-card-text class="pa-2">
                <div class="text-caption font-weight-medium text-truncate">{{ item.title }}</div>
                <div class="text-caption text-medium-emphasis text-truncate">{{ item.provider || 'Online-Suche' }} · {{ item.license_name || 'Rechte siehe Quelle' }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>
      <v-window-item value="url">
        <v-text-field
          :model-value="modelValue"
          label="Produktbild-URL (optional)"
          prepend-inner-icon="mdi-image-outline"
          maxlength="1000"
          :rules="[imageRule]"
          clearable
          @update:model-value="applyImage($event?.trim() || null, 'url', $event?.trim() || null)"
        />
      </v-window-item>
    </v-window>

    <v-card v-if="modelValue" variant="tonal" class="mt-4 image-preview" @click="previewDialog = true">
      <v-img
        v-if="!previewFailed"
        :src="modelValue"
        max-height="260"
        min-height="150"
        contain
        alt="Vorschau des Produktbilds"
        @error="previewFailed = true"
      />
      <v-alert v-else type="warning" variant="tonal" class="ma-3">
        Das Bild konnte nicht geladen werden. Bitte Quelle und Berechtigung prüfen.
      </v-alert>
      <div class="text-caption text-center pa-2">Zum Vergrößern anklicken</div>
    </v-card>

    <v-dialog v-model="previewDialog" max-width="1100">
      <v-card>
        <v-img :src="modelValue || ''" max-height="80vh" contain />
        <v-card-actions><v-spacer /><v-btn @click="previewDialog = false">Schließen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="immichDialog" max-width="1050" scrollable>
      <v-card title="Produktbild aus Immich auswählen" prepend-icon="mdi-image-multiple">
        <v-progress-linear v-if="busy" indeterminate />
        <v-card-text>
          <v-row dense class="mb-3">
            <v-col cols="12" sm="7">
              <v-text-field v-model="immichSearch" label="Dateiname suchen" prepend-inner-icon="mdi-magnify" clearable hide-details />
            </v-col>
            <v-col cols="12" sm="5">
              <v-select
                v-model="immichAlbumId"
                :items="immichAlbums"
                item-title="album_name"
                item-value="immich_album_id"
                label="Album"
                clearable
                hide-details
              />
            </v-col>
          </v-row>
          <v-row dense>
            <v-col v-for="image in immichImages" :key="image.immich_asset_id" cols="4" sm="3" md="2">
              <v-card variant="outlined" @click="selectImmich(image)">
                <v-img :src="image.thumbnail_url" aspect-ratio="1" cover />
                <div class="text-caption text-truncate pa-1">{{ image.original_file_name }}</div>
              </v-card>
            </v-col>
          </v-row>
          <v-pagination v-if="immichPages > 1" v-model="immichPage" :length="immichPages" class="mt-4" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="immichDialog = false">Abbrechen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.image-preview { cursor: zoom-in; overflow: hidden; }
</style>

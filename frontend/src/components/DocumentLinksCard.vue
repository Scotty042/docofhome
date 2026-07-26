<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { documentLinksApi } from '../services/documentLinksApi'
import { documentsApi } from '../services/documentsApi'
import type { DocumentLink, DocumentTargetType } from '../types/documentLinks'
import type { DocumentEntry } from '../types/documents'

const props = defineProps<{
  targetType: DocumentTargetType
  targetId: string
  readOnly?: boolean
}>()

const links = ref<DocumentLink[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const dialog = ref(false)
const browserPath = ref('')
const browserItems = ref<DocumentEntry[]>([])
const browserLoading = ref(false)
const selectedPath = ref<string | null>(null)
const saving = ref(false)
const removingId = ref<string | null>(null)

const breadcrumbs = computed(() => {
  const parts = browserPath.value ? browserPath.value.split('/') : []
  return [
    { title: 'Dokumente', path: '' },
    ...parts.map((title, index) => ({ title, path: parts.slice(0, index + 1).join('/') }))
  ]
})

async function loadLinks() {
  loading.value = true
  error.value = null
  try {
    links.value = await documentLinksApi.list(props.targetType, props.targetId)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dokumente konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadFolder(path: string) {
  browserLoading.value = true
  selectedPath.value = null
  try {
    const result = await documentsApi.list(path)
    browserPath.value = result.path
    browserItems.value = result.items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dokumentenordner konnte nicht geladen werden.'
  } finally {
    browserLoading.value = false
  }
}

async function openDialog() {
  dialog.value = true
  await loadFolder('')
}

async function addLink() {
  if (!selectedPath.value) return
  saving.value = true
  error.value = null
  try {
    await documentLinksApi.create(props.targetType, props.targetId, selectedPath.value)
    dialog.value = false
    await loadLinks()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dokument konnte nicht verknüpft werden.'
  } finally {
    saving.value = false
  }
}

async function removeLink(link: DocumentLink) {
  removingId.value = link.id
  error.value = null
  try {
    await documentLinksApi.remove(link.id)
    await loadLinks()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verknüpfung konnte nicht entfernt werden.'
  } finally {
    removingId.value = null
  }
}

function openEntry(entry: DocumentEntry) {
  if (entry.entry_type === 'folder') void loadFolder(entry.path)
  else selectedPath.value = entry.path
}

onMounted(() => void loadLinks())
watch(() => [props.targetType, props.targetId], () => void loadLinks())
</script>

<template>
  <v-card title="Dokumente" prepend-icon="mdi-file-document-outline" class="mb-5">
    <template #append>
      <v-btn
        v-if="!readOnly"
        size="small"
        variant="tonal"
        prepend-icon="mdi-link-plus"
        @click="openDialog"
      >
        Verknüpfen
      </v-btn>
    </template>
    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
    <v-list v-if="links.length" lines="two">
      <v-list-item
        v-for="link in links"
        :key="link.id"
        :prepend-icon="link.available ? 'mdi-file-outline' : 'mdi-alert-outline'"
        :href="link.available ? documentsApi.downloadUrl(link.document_path) : undefined"
        :target="link.available ? '_blank' : undefined"
      >
        <v-list-item-title>{{ link.document_name }}</v-list-item-title>
        <v-list-item-subtitle>
          {{ link.available ? link.document_path : `Nicht mehr unter ${link.document_path} verfügbar` }}
        </v-list-item-subtitle>
        <template #append>
          <v-btn
            v-if="!readOnly"
            icon="mdi-link-variant-off"
            variant="text"
            color="error"
            :loading="removingId === link.id"
            aria-label="Dokumentenverknüpfung entfernen"
            @click.prevent="removeLink(link)"
          />
        </template>
      </v-list-item>
    </v-list>
    <v-card-text v-else-if="!loading" class="text-medium-emphasis">
      Noch keine Dokumente verknüpft.
    </v-card-text>
  </v-card>

  <v-dialog v-model="dialog" max-width="720">
    <v-card title="Dokument auswählen" prepend-icon="mdi-file-document-outline">
      <v-card-text>
        <v-breadcrumbs :items="breadcrumbs.map((item) => ({ title: item.title, disabled: item.path === browserPath }))" class="px-0">
          <template #item="{ item, index }">
            <v-breadcrumbs-item
              :disabled="item.disabled"
              @click="loadFolder(breadcrumbs[index]?.path ?? '')"
            >{{ item.title }}</v-breadcrumbs-item>
          </template>
        </v-breadcrumbs>
        <v-progress-linear v-if="browserLoading" indeterminate class="mb-2" />
        <v-list border rounded>
          <v-list-item
            v-for="entry in browserItems"
            :key="entry.path"
            :prepend-icon="entry.entry_type === 'folder' ? 'mdi-folder-outline' : 'mdi-file-outline'"
            :active="selectedPath === entry.path"
            @click="openEntry(entry)"
          >
            <v-list-item-title>{{ entry.name }}</v-list-item-title>
            <template #append>
              <v-icon v-if="entry.entry_type === 'folder'" icon="mdi-chevron-right" />
              <v-icon v-else-if="selectedPath === entry.path" icon="mdi-check-circle" color="primary" />
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="dialog = false">Abbrechen</v-btn>
        <v-btn color="primary" :disabled="!selectedPath" :loading="saving" @click="addLink">
          Verknüpfen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

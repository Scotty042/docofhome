<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import {
  folderPathChain,
  isInvalidMoveDestination
} from '../services/documentFolderTree'
import { documentsApi, DocumentsApiError } from '../services/documentsApi'
import type { DocumentEntry, DocumentListRead } from '../types/documents'

interface MoveFolderNode {
  path: string
  name: string
  loaded: boolean
  loading: boolean
  children: string[]
  error: string | null
}

interface VisibleMoveFolderNode extends MoveFolderNode {
  depth: number
  expanded: boolean
  disabled: boolean
  expandable: boolean
}

const route = useRoute()

const MAX_UPLOAD_BYTES = 100 * 1024 * 1024
const CONFIGURATION_ERROR = 'Nextcloud integration is not fully configured or enabled'

const listing = ref<DocumentListRead | null>(null)
const storageConfigured = ref(true)
const currentPath = ref('')
const filterText = ref<string | null>('')
const loading = ref(false)
const actionLoading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const folderDialog = ref(false)
const folderName = ref('')
const moveDialog = ref(false)
const moveTarget = ref<DocumentEntry | null>(null)
const moveName = ref('')
const moveParentPath = ref('')
const moveFolderTree = ref<Record<string, MoveFolderNode>>({})
const moveExpandedPaths = ref<string[]>([])
const moveTreeInitializing = ref(false)
const moveTreeError = ref<string | null>(null)
const deleteDialog = ref(false)
const deleteTarget = ref<DocumentEntry | null>(null)
const overwriteDialog = ref(false)
const pendingOverwriteFile = ref<File | null>(null)
const focusedEntryPath = ref<string | null>(null)

const configuredRoot = computed(() => listing.value?.root_path ?? null)
const visibleItems = computed(() => {
  const needle = (filterText.value ?? '').trim().toLocaleLowerCase()
  if (!needle) return listing.value?.items ?? []
  return (listing.value?.items ?? []).filter((item) => (
    item.name.toLocaleLowerCase().includes(needle)
    || (item.content_type ?? '').toLocaleLowerCase().includes(needle)
  ))
})
const filterActive = computed(() => Boolean((filterText.value ?? '').trim()))
const breadcrumbs = computed(() => {
  const parts = currentPath.value ? currentPath.value.split('/') : []
  return [
    { title: 'Dokumente', path: '' },
    ...parts.map((title, index) => ({
      title,
      path: parts.slice(0, index + 1).join('/')
    }))
  ]
})

const visibleMoveFolders = computed<VisibleMoveFolderNode[]>(() => {
  const nodes: VisibleMoveFolderNode[] = []
  const expanded = new Set(moveExpandedPaths.value)

  function visit(path: string, depth: number) {
    const node = moveFolderTree.value[path]
    if (!node) return
    const disabled = moveTarget.value
      ? isInvalidMoveDestination(moveTarget.value.path, moveTarget.value.entry_type, path)
      : false
    const isExpanded = expanded.has(path)
    nodes.push({
      ...node,
      depth,
      expanded: isExpanded,
      disabled,
      expandable: !disabled && (!node.loaded || node.children.length > 0)
    })
    if (!isExpanded) return
    for (const childPath of node.children) visit(childPath, depth + 1)
  }

  visit('', 0)
  return nodes
})

const selectedMoveFolderLabel = computed(() => (
  moveParentPath.value || 'Dokumente (Stammordner)'
))

async function loadRouteTarget() {
  const requestedPath = typeof route.query.path === 'string' ? route.query.path : ''
  focusedEntryPath.value = typeof route.query.focus === 'string' ? route.query.focus : null
  await loadDocuments(requestedPath, true)
}

onMounted(loadRouteTarget)
watch(
  () => [route.query.path, route.query.focus],
  () => void loadRouteTarget()
)

async function loadDocuments(path = currentPath.value, preserveFocus = false) {
  if (!preserveFocus) focusedEntryPath.value = null
  loading.value = true
  error.value = null
  try {
    const result = await documentsApi.list(path)
    listing.value = result
    storageConfigured.value = true
    currentPath.value = result.path
    filterText.value = ''
  } catch (reason) {
    listing.value = null
    if (
      reason instanceof DocumentsApiError
      && reason.status === 409
      && reason.message === CONFIGURATION_ERROR
    ) {
      storageConfigured.value = false
      error.value = null
    } else {
      storageConfigured.value = true
      error.value = reason instanceof Error
        ? reason.message
        : 'Dokumente konnten nicht geladen werden.'
    }
  } finally {
    loading.value = false
  }
}

function openFolder(entry: DocumentEntry) {
  if (entry.entry_type === 'folder' && !actionLoading.value) void loadDocuments(entry.path)
}

function chooseFile() {
  if (!actionLoading.value) fileInput.value?.click()
}

async function selectedFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > MAX_UPLOAD_BYTES) {
    error.value = `${file.name} ist größer als das zulässige Limit von 100 MB.`
    return
  }
  await uploadFile(file, false)
}

async function uploadFile(file: File, overwrite: boolean) {
  actionLoading.value = true
  error.value = null
  success.value = null
  try {
    const result = await documentsApi.upload(currentPath.value, file, overwrite)
    success.value = result.overwritten
      ? `${result.item.name} wurde ersetzt. Nextcloud kann frühere Dateiversionen aufbewahren.`
      : `${result.item.name} wurde hochgeladen.`
    pendingOverwriteFile.value = null
    overwriteDialog.value = false
    await loadDocuments(currentPath.value)
  } catch (reason) {
    if (reason instanceof DocumentsApiError && reason.status === 409 && !overwrite) {
      pendingOverwriteFile.value = file
      overwriteDialog.value = true
    } else {
      error.value = reason instanceof Error
        ? reason.message
        : 'Dokument konnte nicht hochgeladen werden.'
    }
  } finally {
    actionLoading.value = false
  }
}

async function createFolder() {
  const name = folderName.value.trim()
  if (!name) return
  actionLoading.value = true
  error.value = null
  success.value = null
  try {
    const result = await documentsApi.createFolder(currentPath.value, name)
    folderDialog.value = false
    folderName.value = ''
    success.value = `Ordner ${result.item.name} wurde angelegt.`
    await loadDocuments(currentPath.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Ordner konnte nicht angelegt werden.'
  } finally {
    actionLoading.value = false
  }
}

async function startMove(entry: DocumentEntry) {
  moveTarget.value = entry
  moveName.value = entry.name
  moveParentPath.value = currentPath.value
  moveDialog.value = true
  await initializeMoveFolderTree()
}

function updateMoveFolderNode(path: string, patch: Partial<MoveFolderNode>) {
  const current = moveFolderTree.value[path]
  if (!current) return
  moveFolderTree.value = {
    ...moveFolderTree.value,
    [path]: { ...current, ...patch }
  }
}

function setMoveFolderExpanded(path: string, expanded: boolean) {
  const next = new Set(moveExpandedPaths.value)
  if (expanded) next.add(path)
  else next.delete(path)
  moveExpandedPaths.value = [...next]
}

async function loadMoveFolderChildren(path: string) {
  const node = moveFolderTree.value[path]
  if (!node || node.loading || node.loaded) return
  moveTreeError.value = null
  updateMoveFolderNode(path, { loading: true, error: null })
  try {
    const result = await documentsApi.list(path)
    const folders = result.items
      .filter((entry) => entry.entry_type === 'folder')
      .sort((left, right) => left.name.localeCompare(right.name, 'de'))
    const nextTree = { ...moveFolderTree.value }
    for (const folder of folders) {
      const existing = nextTree[folder.path]
      nextTree[folder.path] = existing
        ? { ...existing, name: folder.name }
        : {
            path: folder.path,
            name: folder.name,
            loaded: false,
            loading: false,
            children: [],
            error: null
          }
    }
    const currentNode = nextTree[path] ?? node
    nextTree[path] = {
      ...currentNode,
      loaded: true,
      loading: false,
      children: folders.map((folder) => folder.path),
      error: null
    }
    moveFolderTree.value = nextTree
  } catch (reason) {
    const message = reason instanceof Error
      ? reason.message
      : 'Unterordner konnten nicht geladen werden.'
    updateMoveFolderNode(path, { loading: false, error: message })
    moveTreeError.value = message
  }
}

async function initializeMoveFolderTree() {
  moveTreeInitializing.value = true
  moveTreeError.value = null
  moveFolderTree.value = {
    '': {
      path: '',
      name: 'Dokumente (Stammordner)',
      loaded: false,
      loading: false,
      children: [],
      error: null
    }
  }
  moveExpandedPaths.value = []
  try {
    for (const folderPath of folderPathChain(currentPath.value)) {
      setMoveFolderExpanded(folderPath, true)
      await loadMoveFolderChildren(folderPath)
    }
  } finally {
    moveTreeInitializing.value = false
  }
}

async function toggleMoveFolder(node: VisibleMoveFolderNode) {
  if (node.disabled || node.loading) return
  if (node.expanded) {
    setMoveFolderExpanded(node.path, false)
    return
  }
  setMoveFolderExpanded(node.path, true)
  await loadMoveFolderChildren(node.path)
}

function selectMoveFolder(node: VisibleMoveFolderNode) {
  if (node.disabled) return
  moveParentPath.value = node.path
}

async function retryMoveFolder(node: VisibleMoveFolderNode) {
  moveTreeError.value = null
  updateMoveFolderNode(node.path, { loaded: false, error: null })
  await loadMoveFolderChildren(node.path)
}

async function moveEntry() {
  const target = moveTarget.value
  const name = moveName.value.trim()
  const targetParentPath = moveParentPath.value.trim()
  if (!target || !name) return
  actionLoading.value = true
  error.value = null
  success.value = null
  try {
    const result = await documentsApi.move({
      source_path: target.path,
      target_parent_path: targetParentPath,
      name
    })
    moveDialog.value = false
    moveTarget.value = null
    success.value = result.item.path === target.path
      ? 'Der Dokumenteintrag war bereits am gewählten Ziel.'
      : `${target.name} wurde nach ${result.item.path} verschoben.`
    await loadDocuments(currentPath.value)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Dokumenteintrag konnte nicht verschoben werden.'
  } finally {
    actionLoading.value = false
  }
}

function startDelete(entry: DocumentEntry) {
  deleteTarget.value = entry
  deleteDialog.value = true
}

async function deleteEntry() {
  const target = deleteTarget.value
  if (!target) return
  actionLoading.value = true
  error.value = null
  success.value = null
  try {
    await documentsApi.remove(target.path)
    deleteDialog.value = false
    deleteTarget.value = null
    success.value = `${target.name} wurde gelöscht.`
    await loadDocuments(currentPath.value)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Dokumenteintrag konnte nicht gelöscht werden.'
  } finally {
    actionLoading.value = false
  }
}

function iconFor(entry: DocumentEntry): string {
  if (entry.entry_type === 'folder') return 'mdi-folder-outline'
  const type = entry.content_type ?? ''
  if (type.includes('pdf')) return 'mdi-file-pdf-box'
  if (type.startsWith('image/')) return 'mdi-file-image-outline'
  if (type.includes('spreadsheet') || type.includes('excel')) return 'mdi-file-excel-outline'
  if (type.includes('word') || type.includes('document')) return 'mdi-file-word-outline'
  if (type.startsWith('text/')) return 'mdi-file-document-outline'
  return 'mdi-file-outline'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value: string | null): string {
  if (!value) return 'Änderungszeit unbekannt'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Änderungszeit unbekannt' : date.toLocaleString()
}
</script>

<template>
  <v-container class="documents-container pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-column flex-md-row align-md-start justify-space-between ga-4 mb-6">
      <div>
        <h1>Dokumente</h1>
        <p class="text-medium-emphasis mb-0">
          Verwalte Anleitungen, Rechnungen, Prüfprotokolle und weitere Hausdokumente in Nextcloud.
        </p>
      </div>
      <v-chip
        v-if="configuredRoot"
        prepend-icon="mdi-folder-outline"
        variant="tonal"
      >
        {{ configuredRoot }}
      </v-chip>
    </div>

    <v-alert
      v-if="!storageConfigured"
      type="info"
      variant="tonal"
      class="mb-5"
      icon="mdi-cloud-alert-outline"
    >
      <div class="font-weight-medium mb-1">Nextcloud-Dokumentenspeicher ist noch nicht bereit.</div>
      Aktiviere Nextcloud, hinterlege Konto und App-Passwort und speichere einen Dokumenten-Stammordner.
      <template #append>
        <v-btn variant="text" to="/settings">Einstellungen öffnen</v-btn>
      </template>
    </v-alert>

    <template v-else>
      <v-alert
        v-if="error"
        type="error"
        variant="tonal"
        closable
        class="mb-4"
        @click:close="error = null"
      >
        {{ error }}
      </v-alert>
      <v-alert
        v-if="success"
        type="success"
        variant="tonal"
        closable
        class="mb-4"
        @click:close="success = null"
      >
        {{ success }}
      </v-alert>

      <v-card class="mb-4">
        <v-card-text>
          <div class="d-flex flex-wrap align-center ga-1 mb-4">
            <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
              <v-btn
                size="small"
                :variant="index === breadcrumbs.length - 1 ? 'tonal' : 'text'"
                :prepend-icon="index === 0 ? 'mdi-folder-home-outline' : undefined"
                :disabled="loading || actionLoading"
                @click="loadDocuments(crumb.path)"
              >
                {{ crumb.title }}
              </v-btn>
              <v-icon v-if="index < breadcrumbs.length - 1" icon="mdi-chevron-right" size="small" />
            </template>
          </div>

          <div class="d-flex flex-column flex-sm-row ga-3">
            <v-text-field
              v-model="filterText"
              label="Aktuellen Ordner filtern"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              class="flex-grow-1"
            />
            <div class="d-flex flex-wrap ga-2">
              <v-btn
                prepend-icon="mdi-folder-plus-outline"
                variant="tonal"
                :disabled="loading || actionLoading"
                @click="folderDialog = true"
              >
                Ordner
              </v-btn>
              <v-btn
                prepend-icon="mdi-upload"
                color="primary"
                :loading="actionLoading"
                :disabled="loading"
                @click="chooseFile"
              >
                Hochladen
              </v-btn>
              <v-btn
                icon="mdi-refresh"
                variant="text"
                aria-label="Dokumente aktualisieren"
                title="Dokumente aktualisieren"
                :loading="loading"
                :disabled="actionLoading"
                @click="loadDocuments(currentPath)"
              />
            </div>
          </div>
          <input
            ref="fileInput"
            type="file"
            class="d-none"
            @change="selectedFile"
          >
        </v-card-text>
      </v-card>

      <v-skeleton-loader v-if="loading" type="list-item-three-line@4" />

      <v-alert
        v-else-if="listing && !listing.root_exists"
        type="info"
        variant="tonal"
        icon="mdi-folder-plus-outline"
      >
        Der konfigurierte Stammordner existiert noch nicht. Er wird beim ersten Upload oder beim
        Anlegen eines Ordners erstellt.
      </v-alert>

      <v-alert
        v-else-if="visibleItems.length === 0"
        type="info"
        variant="tonal"
      >
        {{ filterActive ? 'Kein Eintrag passt zum Filter.' : 'Dieser Ordner ist leer.' }}
      </v-alert>

      <v-card v-else>
        <v-list lines="three" class="document-list">
          <v-list-item
            v-for="entry in visibleItems"
            :key="entry.path"
            :class="{ 'folder-entry': entry.entry_type === 'folder', 'search-focused-entry': focusedEntryPath === entry.path }"
            :disabled="actionLoading"
            @click="openFolder(entry)"
          >
            <template #prepend>
              <v-avatar color="surface-variant" rounded="lg">
                <v-icon :icon="iconFor(entry)" color="primary" />
              </v-avatar>
            </template>
            <v-list-item-title class="font-weight-medium">{{ entry.name }}</v-list-item-title>
            <v-list-item-subtitle>
              {{ entry.entry_type === 'folder' ? 'Ordner' : formatSize(entry.size_bytes) }}
              · {{ formatDate(entry.modified_at) }}
            </v-list-item-subtitle>
            <v-list-item-subtitle v-if="entry.content_type && entry.entry_type === 'file'">
              {{ entry.content_type }}
            </v-list-item-subtitle>
            <template #append>
              <div class="d-flex ga-1" @click.stop>
                <v-btn
                  v-if="entry.entry_type === 'file'"
                  :href="documentsApi.downloadUrl(entry.path)"
                  :download="entry.name"
                  icon="mdi-download"
                  variant="text"
                  :disabled="actionLoading"
                  aria-label="Dokument herunterladen"
                  title="Dokument herunterladen"
                />
                <v-btn
                  icon="mdi-rename-outline"
                  variant="text"
                  :disabled="actionLoading"
                  aria-label="Eintrag umbenennen oder verschieben"
                  title="Eintrag umbenennen oder verschieben"
                  @click="startMove(entry)"
                />
                <v-btn
                  icon="mdi-delete-outline"
                  variant="text"
                  color="error"
                  :disabled="actionLoading"
                  aria-label="Eintrag löschen"
                  title="Eintrag löschen"
                  @click="startDelete(entry)"
                />
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card>
    </template>

    <v-dialog v-model="folderDialog" max-width="500">
      <v-card title="Neuen Ordner anlegen" prepend-icon="mdi-folder-plus-outline">
        <v-card-text>
          <v-text-field
            v-model="folderName"
            label="Ordnername"
            maxlength="255"
            autofocus
            @keyup.enter="createFolder"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="actionLoading" @click="folderDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="actionLoading" @click="createFolder">Anlegen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="moveDialog" max-width="680">
      <v-card title="Eintrag umbenennen oder verschieben" prepend-icon="mdi-rename-outline">
        <v-card-text>
          <v-text-field
            v-model="moveName"
            label="Name am Ziel"
            maxlength="255"
            autofocus
            class="mb-2"
          />
          <div class="text-subtitle-2 mb-2">Zielordner auswählen</div>
          <v-sheet
            border
            rounded="lg"
            class="move-folder-tree"
            role="tree"
            aria-label="Zielordner auswählen"
          >
            <div v-if="moveTreeInitializing" class="pa-4 text-center">
              <v-progress-circular indeterminate size="24" class="mr-2" />
              Ordnerstruktur wird geladen …
            </div>
            <v-list v-else density="compact" nav class="pa-1">
              <template v-for="node in visibleMoveFolders" :key="node.path || '__root__'">
                <v-list-item
                  :active="moveParentPath === node.path"
                  active-color="primary"
                  :disabled="node.disabled"
                  :style="{ paddingInlineStart: `${8 + node.depth * 24}px` }"
                  role="treeitem"
                  :aria-level="node.depth + 1"
                  :aria-selected="moveParentPath === node.path"
                  :aria-expanded="node.expandable ? node.expanded : undefined"
                  @click="selectMoveFolder(node)"
                >
                  <template #prepend>
                    <div class="move-folder-tree__prepend" @click.stop>
                      <v-progress-circular
                        v-if="node.loading"
                        indeterminate
                        size="20"
                        width="2"
                      />
                      <v-btn
                        v-else-if="node.expandable"
                        :icon="node.expanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"
                        variant="text"
                        density="compact"
                        size="small"
                        :aria-label="node.expanded ? 'Ordner zuklappen' : 'Ordner aufklappen'"
                        @click="toggleMoveFolder(node)"
                      />
                      <span v-else class="move-folder-tree__spacer" />
                      <v-icon
                        :icon="node.path ? 'mdi-folder-outline' : 'mdi-folder-home-outline'"
                        :color="moveParentPath === node.path ? 'primary' : undefined"
                        class="ml-1"
                      />
                    </div>
                  </template>
                  <v-list-item-title>{{ node.name }}</v-list-item-title>
                  <v-list-item-subtitle v-if="node.disabled">
                    Ein Ordner kann nicht in sich selbst verschoben werden.
                  </v-list-item-subtitle>
                  <template v-if="node.error" #append>
                    <v-btn
                      icon="mdi-refresh"
                      variant="text"
                      size="small"
                      aria-label="Unterordner erneut laden"
                      title="Unterordner erneut laden"
                      @click.stop="retryMoveFolder(node)"
                    />
                  </template>
                </v-list-item>
              </template>
            </v-list>
          </v-sheet>
          <v-alert
            v-if="moveTreeError"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-3"
          >
            {{ moveTreeError }}
          </v-alert>
          <div class="text-caption text-medium-emphasis mt-2">
            Ausgewählt: <strong>{{ selectedMoveFolderLabel }}</strong>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="actionLoading" @click="moveDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            :loading="actionLoading"
            :disabled="moveTreeInitializing"
            @click="moveEntry"
          >
            Übernehmen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialog" max-width="560">
      <v-card title="Dokumenteintrag löschen?" prepend-icon="mdi-delete-alert-outline">
        <v-card-text>
          <p>
            <strong>{{ deleteTarget?.name }}</strong> wird dauerhaft aus Nextcloud gelöscht.
          </p>
          <v-alert
            v-if="deleteTarget?.entry_type === 'folder'"
            type="warning"
            variant="tonal"
            density="compact"
          >
            Aus Sicherheitsgründen können nur leere Ordner gelöscht werden.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="actionLoading" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" :loading="actionLoading" @click="deleteEntry">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="overwriteDialog" max-width="560" persistent>
      <v-card title="Vorhandenes Dokument ersetzen?" prepend-icon="mdi-file-replace-outline">
        <v-card-text>
          <p>
            <strong>{{ pendingOverwriteFile?.name }}</strong> existiert bereits in diesem Ordner.
            Das Ersetzen ist eine ausdrückliche Aktion. Eine aktivierte Nextcloud-Dateiversionierung
            kann die vorherige Version weiterhin aufbewahren.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            :disabled="actionLoading"
            @click="overwriteDialog = false; pendingOverwriteFile = null"
          >
            Abbrechen
          </v-btn>
          <v-btn
            color="warning"
            :loading="actionLoading"
            @click="pendingOverwriteFile && uploadFile(pendingOverwriteFile, true)"
          >
            Ersetzen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.documents-container {
  max-width: 1200px;
}

h1 {
  font-size: clamp(1.8rem, 4vw, 2.25rem);
}

.document-list :deep(.v-list-item) {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.search-focused-entry {
  background: rgba(var(--v-theme-primary), 0.16);
  box-shadow: inset 4px 0 0 rgb(var(--v-theme-primary));
}

.document-list :deep(.v-list-item:last-child) {
  border-bottom: 0;
}

.folder-entry {
  cursor: pointer;
}


.move-folder-tree {
  max-height: min(52vh, 440px);
  overflow-y: auto;
  background: rgb(var(--v-theme-surface));
}

.move-folder-tree__prepend {
  display: flex;
  align-items: center;
  min-width: 58px;
}

.move-folder-tree__spacer {
  display: inline-block;
  width: 36px;
  height: 28px;
}

@media (max-width: 600px) {
  .document-list :deep(.v-list-item__append) {
    align-self: center;
  }
}
</style>

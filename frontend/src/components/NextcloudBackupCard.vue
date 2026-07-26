<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { backupApi } from '../services/backupApi'
import type { RemoteBackupRecord } from '../types/backups'

const props = defineProps<{ enabled: boolean }>()
const emit = defineEmits<{ imported: [] }>()
const folder = ref('DocOfHome/Backups')
const backups = ref<RemoteBackupRecord[]>([])
const loading = ref(false)
const activeFilename = ref<string | null>(null)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const deleteDialog = ref(false)
const deleteFilename = ref<string | null>(null)

onMounted(() => {
  if (props.enabled) void loadRemoteBackups()
})

async function loadRemoteBackups() {
  if (!props.enabled) {
    error.value = 'Aktiviere und prüfe zuerst die Nextcloud-Integration in den Einstellungen.'
    return
  }
  loading.value = true
  error.value = null
  try {
    backups.value = (await backupApi.listRemote(folder.value)).items
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Nextcloud-Backups konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function importRemoteBackup(filename: string) {
  activeFilename.value = filename
  error.value = null
  success.value = null
  try {
    const record = await backupApi.importRemote(filename, folder.value)
    success.value = `Backup ${record.filename} wurde geprüft und lokal importiert.`
    emit('imported')
    await loadRemoteBackups()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Nextcloud-Backup konnte nicht importiert werden.'
  } finally {
    activeFilename.value = null
  }
}

function openDelete(filename: string) {
  deleteFilename.value = filename
  deleteDialog.value = true
}

async function deleteRemoteBackup() {
  if (!deleteFilename.value) return
  activeFilename.value = deleteFilename.value
  error.value = null
  success.value = null
  try {
    await backupApi.removeRemote(deleteFilename.value, folder.value)
    success.value = `Backup ${deleteFilename.value} wurde aus Nextcloud gelöscht.`
    deleteDialog.value = false
    await loadRemoteBackups()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Nextcloud-Backup konnte nicht gelöscht werden.'
  } finally {
    activeFilename.value = null
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <v-card title="Backups in Nextcloud" prepend-icon="mdi-cloud-outline" class="mb-5">
    <v-card-text>
      <p class="text-medium-emphasis mb-4">
        Zeigt DocOfHome-ZIP-Backups im angegebenen WebDAV-Ordner. Beim lokalen Import wird das
        Archiv vollständig geprüft. Das Löschen aus Nextcloud verändert keine lokale Kopie.
      </p>

      <v-alert v-if="!enabled" type="info" variant="tonal" class="mb-4">
        Die Nextcloud-Integration ist noch nicht aktiv. Aktiviere sie unter Einstellungen und führe
        dort den Verbindungstest aus. Danach kannst du Remote-Backups hier laden und verwalten.
      </v-alert>
      <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = null">
        {{ error }}
      </v-alert>
      <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = null">
        {{ success }}
      </v-alert>

      <div class="d-flex flex-column flex-sm-row ga-2 mb-4">
        <v-text-field
          v-model="folder"
          label="Nextcloud-Ordner"
          hint="Relativ zum Benutzerverzeichnis, zum Beispiel DocOfHome/Backups"
          persistent-hint
          hide-details="auto"
          :disabled="!enabled"
          @keyup.enter="loadRemoteBackups"
        />
        <v-btn
          color="primary"
          variant="tonal"
          prepend-icon="mdi-cloud-refresh-outline"
          :loading="loading"
          :disabled="!enabled"
          @click="loadRemoteBackups"
        >
          Laden
        </v-btn>
      </div>

      <v-skeleton-loader v-if="loading" type="list-item-three-line, list-item-three-line" />
      <v-alert v-else-if="enabled && backups.length === 0" type="info" variant="tonal">
        In diesem Nextcloud-Ordner wurden keine DocOfHome-Backups gefunden.
      </v-alert>
      <v-list v-else-if="enabled" lines="two" class="remote-list">
        <v-list-item v-for="backup in backups" :key="backup.filename">
          <template #prepend>
            <v-icon icon="mdi-cloud-check-outline" color="primary" />
          </template>
          <v-list-item-title>{{ backup.filename }}</v-list-item-title>
          <v-list-item-subtitle>
            {{ formatSize(backup.size_bytes) }}
            <template v-if="backup.modified_at">
              · geändert {{ new Date(backup.modified_at).toLocaleString() }}
            </template>
          </v-list-item-subtitle>
          <template #append>
            <div class="d-flex align-center ga-1">
              <v-chip
                v-if="backup.local_available"
                size="small"
                color="success"
                variant="tonal"
                prepend-icon="mdi-harddisk"
              >
                Lokal vorhanden
              </v-chip>
              <v-btn
                icon="mdi-cloud-download-outline"
                variant="text"
                color="primary"
                aria-label="Nextcloud-Backup lokal importieren"
                title="Nextcloud-Backup lokal importieren"
                :loading="activeFilename === backup.filename"
                @click="importRemoteBackup(backup.filename)"
              />
              <v-btn
                icon="mdi-delete-outline"
                variant="text"
                color="error"
                aria-label="Nextcloud-Backup löschen"
                title="Nextcloud-Backup löschen"
                @click="openDelete(backup.filename)"
              />
            </div>
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>

  <v-dialog v-model="deleteDialog" max-width="560">
    <v-card title="Backup aus Nextcloud löschen?" prepend-icon="mdi-cloud-remove-outline">
      <v-card-text>
        <v-alert type="warning" variant="tonal" class="mb-4">
          Nur die Datei in Nextcloud wird gelöscht. Eine vorhandene lokale Kopie bleibt erhalten.
        </v-alert>
        <strong>{{ deleteFilename }}</strong>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
        <v-btn
          color="error"
          :loading="activeFilename === deleteFilename"
          @click="deleteRemoteBackup"
        >
          Aus Nextcloud löschen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.remote-list { background: transparent; }
</style>

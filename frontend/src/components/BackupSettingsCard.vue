<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { backupApi } from '../services/backupApi'
import type {
  BackupRecord,
  BackupSchedule,
  BackupScheduleWrite,
  BackupValidationRead
} from '../types/backups'

const props = defineProps<{ nextcloudEnabled: boolean }>()

const backups = ref<BackupRecord[]>([])
const loading = ref(true)
const creating = ref(false)
const savingSchedule = ref(false)
const runningSchedule = ref(false)
const activeFilename = ref<string | null>(null)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const uploadToNextcloud = ref(false)
const nextcloudFolder = ref('DocOfHome/Backups')
const schedule = ref<BackupSchedule>({
  enabled: false,
  interval_hours: 24,
  retention_count: 10,
  upload_to_nextcloud: false,
  nextcloud_folder: 'DocOfHome/Backups',
  last_attempt_at: null,
  last_success_at: null,
  last_error: null
})
const validation = ref<Record<string, BackupValidationRead>>({})
const restoreDialog = ref(false)
const restoreFilename = ref<string | null>(null)
const restoreConfirmation = ref('')

const canUpload = computed(() => props.nextcloudEnabled)
const intervalOptions = [
  { title: 'Alle 6 Stunden', value: 6 },
  { title: 'Täglich', value: 24 },
  { title: 'Wöchentlich', value: 168 },
  { title: 'Monatlich (30 Tage)', value: 720 }
]

onMounted(() => void load())

async function load() {
  loading.value = true
  error.value = null
  try {
    const [backupList, storedSchedule] = await Promise.all([
      backupApi.list(),
      backupApi.readSchedule()
    ])
    backups.value = backupList.items
    schedule.value = storedSchedule
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backups konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function createBackup() {
  creating.value = true
  error.value = null
  success.value = null
  try {
    const record = await backupApi.create(uploadToNextcloud.value, nextcloudFolder.value)
    success.value = record.nextcloud_uploaded
      ? 'Backup wurde lokal erstellt und zu Nextcloud hochgeladen.'
      : 'Lokales Backup wurde erfolgreich erstellt.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backup konnte nicht erstellt werden.'
  } finally {
    creating.value = false
  }
}

async function saveSchedule() {
  savingSchedule.value = true
  error.value = null
  success.value = null
  try {
    const payload: BackupScheduleWrite = {
      enabled: schedule.value.enabled,
      interval_hours: schedule.value.interval_hours,
      retention_count: schedule.value.retention_count,
      upload_to_nextcloud: schedule.value.upload_to_nextcloud,
      nextcloud_folder: schedule.value.nextcloud_folder
    }
    schedule.value = await backupApi.updateSchedule(payload)
    success.value = 'Automatische Backup-Einstellungen wurden gespeichert.'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backup-Automatik konnte nicht gespeichert werden.'
  } finally {
    savingSchedule.value = false
  }
}

async function runScheduleNow() {
  runningSchedule.value = true
  error.value = null
  success.value = null
  try {
    schedule.value = await backupApi.runScheduleNow()
    if (schedule.value.last_error) {
      error.value = schedule.value.last_error
    } else {
      success.value = 'Automatisches Backup wurde jetzt ausgeführt.'
      await load()
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Automatisches Backup konnte nicht ausgeführt werden.'
  } finally {
    runningSchedule.value = false
  }
}

async function validateBackup(filename: string) {
  activeFilename.value = filename
  error.value = null
  try {
    validation.value[filename] = await backupApi.validate(filename)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backup konnte nicht geprüft werden.'
  } finally {
    activeFilename.value = null
  }
}

async function deleteBackup(filename: string) {
  if (!window.confirm(`Backup ${filename} wirklich dauerhaft löschen?`)) return
  activeFilename.value = filename
  error.value = null
  success.value = null
  try {
    await backupApi.remove(filename)
    delete validation.value[filename]
    success.value = 'Backup wurde dauerhaft gelöscht.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backup konnte nicht gelöscht werden.'
  } finally {
    activeFilename.value = null
  }
}

function openRestore(filename: string) {
  restoreFilename.value = filename
  restoreConfirmation.value = ''
  restoreDialog.value = true
}

async function scheduleRestore() {
  if (!restoreFilename.value) return
  activeFilename.value = restoreFilename.value
  error.value = null
  success.value = null
  try {
    const result = await backupApi.restore(restoreFilename.value, restoreConfirmation.value)
    success.value = result.message
    restoreDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wiederherstellung konnte nicht geplant werden.'
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
  <v-card title="Backup und Wiederherstellung" prepend-icon="mdi-database-arrow-up-outline" class="mb-5">
    <v-card-text>
      <p class="text-medium-emphasis mb-4">
        DocOfHome erstellt einen konsistenten SQLite-Snapshot mit Manifest und Prüfsumme. Eine
        Wiederherstellung wird zuerst vollständig geprüft und erst beim nächsten Containerstart angewendet.
      </p>

      <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = null">
        {{ error }}
      </v-alert>
      <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = null">
        {{ success }}
      </v-alert>

      <h3 class="text-h6 mb-3">Manuelles Backup</h3>
      <v-row align="center">
        <v-col cols="12" md="5">
          <v-switch
            v-model="uploadToNextcloud"
            label="Zusätzlich zu Nextcloud hochladen"
            color="primary"
            :disabled="!canUpload"
            hide-details
            inset
          />
          <div v-if="!canUpload" class="text-caption text-medium-emphasis mt-1">
            Aktiviere und prüfe zuerst die Nextcloud-Integration.
          </div>
        </v-col>
        <v-col cols="12" md="5">
          <v-text-field
            v-model="nextcloudFolder"
            label="Nextcloud-Zielordner"
            hint="Relativ zum Benutzerverzeichnis, zum Beispiel DocOfHome/Backups"
            persistent-hint
            :disabled="!uploadToNextcloud"
          />
        </v-col>
        <v-col cols="12" md="2" class="d-flex justify-end">
          <v-btn
            color="primary"
            prepend-icon="mdi-database-plus-outline"
            :loading="creating"
            @click="createBackup"
          >
            Backup erstellen
          </v-btn>
        </v-col>
      </v-row>

      <v-divider class="my-5" />

      <h3 class="text-h6 mb-3">Automatische Backups</h3>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        Der Container prüft stündlich, ob ein Backup fällig ist. Die Aufbewahrung gilt nur für
        DocOfHome-ZIP-Backups; Sicherheitskopien vor Wiederherstellungen werden nicht automatisch gelöscht.
      </v-alert>
      <v-row>
        <v-col cols="12" md="3">
          <v-switch v-model="schedule.enabled" label="Automatik aktiv" color="primary" inset hide-details />
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="schedule.interval_hours"
            label="Intervall"
            :items="intervalOptions"
            :disabled="!schedule.enabled"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field
            v-model.number="schedule.retention_count"
            label="Anzahl aufbewahren"
            type="number"
            min="1"
            max="100"
            :disabled="!schedule.enabled"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-switch
            v-model="schedule.upload_to_nextcloud"
            label="Auch zu Nextcloud"
            color="primary"
            inset
            hide-details
            :disabled="!schedule.enabled || !canUpload"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="schedule.nextcloud_folder"
            label="Automatischer Nextcloud-Zielordner"
            :disabled="!schedule.enabled || !schedule.upload_to_nextcloud"
          />
        </v-col>
        <v-col cols="12" md="6" class="d-flex flex-wrap justify-end align-center ga-2">
          <v-btn variant="tonal" prepend-icon="mdi-play" :loading="runningSchedule" @click="runScheduleNow">
            Jetzt ausführen
          </v-btn>
          <v-btn color="primary" prepend-icon="mdi-content-save" :loading="savingSchedule" @click="saveSchedule">
            Automatik speichern
          </v-btn>
        </v-col>
      </v-row>
      <div class="d-flex flex-wrap ga-2 mt-2">
        <v-chip v-if="schedule.last_success_at" prepend-icon="mdi-check-circle-outline" color="success" variant="tonal">
          Letzter Erfolg: {{ new Date(schedule.last_success_at).toLocaleString() }}
        </v-chip>
        <v-chip v-if="schedule.last_attempt_at" prepend-icon="mdi-clock-outline" variant="tonal">
          Letzter Versuch: {{ new Date(schedule.last_attempt_at).toLocaleString() }}
        </v-chip>
      </div>

      <v-divider class="my-5" />

      <div class="d-flex align-center justify-space-between mb-3">
        <h3 class="text-h6">Lokale Backups</h3>
        <v-btn icon="mdi-refresh" variant="text" aria-label="Backupliste aktualisieren" title="Backupliste aktualisieren" @click="load" />
      </div>

      <v-skeleton-loader v-if="loading" type="list-item-three-line, list-item-three-line" />
      <v-alert v-else-if="backups.length === 0" type="info" variant="tonal">
        Noch kein Backup vorhanden. Erstelle vor weiteren umfangreichen Änderungen das erste Backup.
      </v-alert>
      <v-list v-else lines="three" class="backup-list">
        <v-list-item v-for="backup in backups" :key="backup.filename">
          <template #prepend>
            <v-icon icon="mdi-folder-zip-outline" color="primary" />
          </template>
          <v-list-item-title>{{ new Date(backup.created_at).toLocaleString() }}</v-list-item-title>
          <v-list-item-subtitle>
            {{ backup.filename }} · {{ formatSize(backup.size_bytes) }} · App {{ backup.app_version }}
          </v-list-item-subtitle>
          <v-list-item-subtitle class="checksum">SHA-256: {{ backup.sha256 }}</v-list-item-subtitle>
          <template #append>
            <div class="d-flex ga-1">
              <v-btn
                :href="backupApi.downloadUrl(backup.filename)"
                icon="mdi-download"
                variant="text"
                aria-label="Backup herunterladen"
                title="Backup herunterladen"
              />
              <v-btn
                icon="mdi-shield-check-outline"
                variant="text"
                aria-label="Backup prüfen"
                title="Backup prüfen"
                :loading="activeFilename === backup.filename"
                @click="validateBackup(backup.filename)"
              />
              <v-btn
                icon="mdi-backup-restore"
                color="warning"
                variant="text"
                aria-label="Backup wiederherstellen"
                title="Backup wiederherstellen"
                @click="openRestore(backup.filename)"
              />
              <v-btn
                icon="mdi-delete-outline"
                color="error"
                variant="text"
                aria-label="Backup löschen"
                title="Backup löschen"
                :loading="activeFilename === backup.filename"
                @click="deleteBackup(backup.filename)"
              />
            </div>
          </template>
          <v-alert
            v-if="validation[backup.filename]"
            :type="validation[backup.filename].valid ? 'success' : 'error'"
            variant="tonal"
            density="compact"
            class="mt-2"
          >
            {{ validation[backup.filename].message }}
          </v-alert>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>

  <v-dialog v-model="restoreDialog" max-width="620">
    <v-card title="Datenbank wiederherstellen?" prepend-icon="mdi-alert-outline">
      <v-card-text>
        <v-alert type="warning" variant="tonal" class="mb-4">
          Beim nächsten Containerstart wird die aktuelle Datenbank durch das gewählte Backup ersetzt.
          Vorher wird automatisch eine zusätzliche Sicherheitskopie der aktuellen Datenbank angelegt.
        </v-alert>
        <p class="mb-3"><strong>{{ restoreFilename }}</strong></p>
        <v-text-field
          v-model="restoreConfirmation"
          label="Zur Bestätigung WIEDERHERSTELLEN eingeben"
          autocomplete="off"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="restoreDialog = false">Abbrechen</v-btn>
        <v-btn
          color="warning"
          :disabled="restoreConfirmation !== 'WIEDERHERSTELLEN'"
          :loading="activeFilename === restoreFilename"
          @click="scheduleRestore"
        >
          Für Neustart vormerken
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.backup-list { background: transparent; }
.checksum { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .72rem; }
</style>

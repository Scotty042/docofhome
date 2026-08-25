<script setup lang="ts">
import { computed, ref } from 'vue'

import { backupApi } from '../services/backupApi'

const emit = defineEmits<{ imported: [] }>()
const selectedValue = ref<File | File[] | null>(null)
const importing = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const selectedFile = computed<File | null>(() => {
  const value = selectedValue.value
  if (!value) return null
  return Array.isArray(value) ? value[0] ?? null : value
})

async function importBackup() {
  const file = selectedFile.value
  if (!file) {
    error.value = 'Bitte zuerst ein DocOfHome-ZIP-Backup auswählen.'
    return
  }

  importing.value = true
  error.value = null
  success.value = null
  try {
    const record = await backupApi.importArchive(file)
    success.value = `Backup ${record.filename} wurde geprüft und importiert.`
    selectedValue.value = null
    emit('imported')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Backup konnte nicht importiert werden.'
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <v-card title="Externes Backup importieren" prepend-icon="mdi-database-import-outline" class="mb-5">
    <v-card-text>
      <p class="text-medium-emphasis mb-4">
        Importiere ein zuvor aus DocOfHome heruntergeladenes ZIP-Backup. Struktur, Manifest,
        Prüfsumme und SQLite-Datenbank werden vor dem Speichern vollständig geprüft.
      </p>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="success" type="success" variant="tonal" class="mb-4">{{ success }}</v-alert>
      <v-row align="center">
        <v-col cols="12" md="9">
          <v-file-input
            v-model="selectedValue"
            label="DocOfHome-Backup auswählen"
            accept="application/zip,.zip"
            hint="Maximal 512 MB; beliebige ZIP-Archive werden abgelehnt."
            persistent-hint
            show-size
            clearable
          />
        </v-col>
        <v-col cols="12" md="3" class="d-flex justify-end">
          <v-btn
            color="primary"
            prepend-icon="mdi-database-import-outline"
            :disabled="!selectedFile"
            :loading="importing"
            @click="importBackup"
          >
            Prüfen und importieren
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

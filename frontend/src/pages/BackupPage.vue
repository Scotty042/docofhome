<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import BackupImportCard from '../components/BackupImportCard.vue'
import BackupSettingsCard from '../components/BackupSettingsCard.vue'
import NextcloudBackupCard from '../components/NextcloudBackupCard.vue'
import { useSettingsStore } from '../stores/settings'

const settings = useSettingsStore()
const backupListKey = ref(0)
const nextcloudEnabled = computed(() => Boolean(
  settings.configuration?.integrations.find((item) => item.kind === 'nextcloud')?.enabled
))

onMounted(async () => {
  if (!settings.configuration) await settings.fetchConfiguration()
})

function refreshBackups() {
  backupListKey.value += 1
}
</script>

<template>
  <v-container class="backup-page pa-4 pa-sm-6" fluid>
    <div class="mb-6">
      <h1>Backup und Wiederherstellung</h1>
      <p class="text-medium-emphasis mb-0">
        Sichere die DocOfHome-Datenbank, lokale Uploads und den Sicherungszeitplan lokal
        und optional zusätzlich in deiner Nextcloud. Neue Sicherungen benötigen zur
        Wiederherstellung Version 1.7.18 oder neuer (maximal 512 MiB entpackt).
        Alte Sicherungen enthalten nur die Datenbank. Archive sind nicht verschlüsselt
        und müssen vertraulich aufbewahrt werden; externe Dienste sind separat zu sichern.
      </p>
    </div>
    <BackupImportCard @imported="refreshBackups" />
    <NextcloudBackupCard
      :enabled="nextcloudEnabled"
      @imported="refreshBackups"
    />
    <BackupSettingsCard :key="backupListKey" :nextcloud-enabled="nextcloudEnabled" />
  </v-container>
</template>

<style scoped>
.backup-page { max-width: 1180px; }
h1 { font-size: clamp(1.8rem, 4vw, 2.25rem); }
</style>

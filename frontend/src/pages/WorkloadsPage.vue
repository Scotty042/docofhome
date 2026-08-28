<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { assetApi } from '../services/assetApi'
import { releaseApi } from '../services/releaseApi'
import type { Asset } from '../types/assets'
import type {
  DockerConnectionTest,
  DockerSyncSetting,
  DockerSyncSettingWrite,
  ServiceWorkload,
  ServiceWorkloadWrite
} from '../types/release'

const workloads = ref<ServiceWorkload[]>([])
const assets = ref<Asset[]>([])
const error = ref<string | null>(null)
const saving = ref(false)
const syncing = ref(false)
const testing = ref(false)
const settingsSaving = ref(false)
const dialog = ref(false)
const editing = ref<ServiceWorkload | null>(null)
const form = ref<ServiceWorkloadWrite>(emptyForm())
const dockerSettings = ref<DockerSyncSetting | null>(null)
const dockerForm = ref<DockerSyncSettingWrite>({
  enabled: false,
  socket_path: '/var/run/docker.sock',
  host_asset_id: null,
  refresh_interval_seconds: 300
})
const testResult = ref<DockerConnectionTest | null>(null)
let refreshTimer: number | null = null

const intervalItems = [
  { title: 'Deaktiviert', value: 0 },
  { title: '30 Sekunden', value: 30 },
  { title: '1 Minute', value: 60 },
  { title: '5 Minuten', value: 300 },
  { title: '15 Minuten', value: 900 },
  { title: '30 Minuten', value: 1800 }
]

const dockerManagedCount = computed(() => workloads.value.filter((item) => item.docker_managed).length)
const runningCount = computed(() => workloads.value.filter((item) => item.status === 'running').length)

function emptyForm(): ServiceWorkloadWrite {
  return {
    host_asset_id: '', name: '', image: null, image_tag: null, compose_project: null,
    network_mode: 'bridge', macvlan_address: null, ports: [],
    urls: { internal: null, external: null, administrative: null, api: null },
    reverse_proxy: null, dependency_ids: [], status: 'unknown', notes: null
  }
}

function formatDateTime(value: string | null) {
  if (!value) return 'Noch nicht'
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))
}

async function loadWorkloads() {
  workloads.value = await releaseApi.workloads()
}

async function refreshDockerView() {
  if (syncing.value) return
  try {
    const [items, settings] = await Promise.all([
      releaseApi.workloads(),
      releaseApi.dockerSyncSettings()
    ])
    workloads.value = items
    dockerSettings.value = settings
  } catch {
    // Keep the last known state visible. Sync failures are persisted by the backend.
  }
}

async function load() {
  try {
    const [items, assetPage, settings] = await Promise.all([
      releaseApi.workloads(),
      assetApi.allAssets(),
      releaseApi.dockerSyncSettings()
    ])
    workloads.value = items
    assets.value = assetPage
    dockerSettings.value = settings
    dockerForm.value = {
      enabled: settings.enabled,
      socket_path: settings.socket_path,
      host_asset_id: settings.host_asset_id,
      refresh_interval_seconds: settings.refresh_interval_seconds
    }
    configureTimer()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dienste konnten nicht geladen werden.'
  }
}

function configureTimer() {
  if (refreshTimer !== null) window.clearInterval(refreshTimer)
  refreshTimer = null
  const seconds = dockerSettings.value?.enabled ? dockerSettings.value.refresh_interval_seconds : 0
  if (!seconds) return
  refreshTimer = window.setInterval(() => void refreshDockerView(), seconds * 1000)
}

watch(() => dockerSettings.value?.refresh_interval_seconds, configureTimer)
watch(() => dockerSettings.value?.enabled, configureTimer)

function open(item?: ServiceWorkload) {
  editing.value = item ?? null
  form.value = item ? {
    host_asset_id: item.host_asset_id, name: item.name, image: item.image,
    image_tag: item.image_tag, compose_project: item.compose_project,
    network_mode: item.network_mode, macvlan_address: item.macvlan_address,
    ports: item.ports.map((port) => ({ ...port })), urls: { ...item.urls },
    reverse_proxy: item.reverse_proxy, dependency_ids: [...item.dependency_ids],
    status: item.status, notes: item.notes
  } : emptyForm()
  dialog.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) await releaseApi.updateWorkload(editing.value.id, form.value)
    else await releaseApi.createWorkload(form.value)
    dialog.value = false
    await loadWorkloads()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dienst konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archive(item: ServiceWorkload) {
  if (!confirm(`Dienst „${item.name}“ archivieren?`)) return
  await releaseApi.archiveWorkload(item.id)
  await loadWorkloads()
}

async function saveDockerSettings(): Promise<boolean> {
  settingsSaving.value = true
  error.value = null
  testResult.value = null
  try {
    dockerSettings.value = await releaseApi.updateDockerSyncSettings(dockerForm.value)
    dockerForm.value = {
      enabled: dockerSettings.value.enabled,
      socket_path: dockerSettings.value.socket_path,
      host_asset_id: dockerSettings.value.host_asset_id,
      refresh_interval_seconds: dockerSettings.value.refresh_interval_seconds
    }
    configureTimer()
    return true
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Docker-Einstellungen konnten nicht gespeichert werden.'
    return false
  } finally {
    settingsSaving.value = false
  }
}

async function testDocker() {
  testing.value = true
  error.value = null
  try {
    if (!await saveDockerSettings()) return
    testResult.value = await releaseApi.testDockerConnection()
  } finally {
    testing.value = false
  }
}

async function syncDocker(silent = false, persistSettings = true) {
  if (syncing.value) return
  syncing.value = true
  if (!silent) error.value = null
  try {
    if (persistSettings && !await saveDockerSettings()) return
    await releaseApi.syncDocker()
    const [items, settings] = await Promise.all([releaseApi.workloads(), releaseApi.dockerSyncSettings()])
    workloads.value = items
    dockerSettings.value = settings
  } catch (reason) {
    if (!silent) error.value = reason instanceof Error ? reason.message : 'Docker-Container konnten nicht aktualisiert werden.'
    try { dockerSettings.value = await releaseApi.dockerSyncSettings() } catch { /* keep prior state */ }
  } finally {
    syncing.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => {
  if (refreshTimer !== null) window.clearInterval(refreshTimer)
})
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div>
        <h1>Dienste & Container</h1>
        <p class="text-medium-emphasis mb-0">Docker-Container vom UGREEN NAS einlesen und eigene Dienstinformationen ergänzen.</p>
      </div>
      <v-spacer />
      <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="syncing" :disabled="!dockerForm.host_asset_id" @click="syncDocker(false, true)">Jetzt aktualisieren</v-btn>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="open()">Dienst</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

    <v-card class="mb-5" title="UGREEN NAS · Docker Engine" prepend-icon="mdi-nas">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="3">
            <v-switch v-model="dockerForm.enabled" label="Automatische Aktualisierung" color="primary" hide-details />
          </v-col>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="dockerForm.host_asset_id"
              :items="assets.map(asset => ({ value: asset.id, title: `${asset.name} · ${asset.jarvis_code}` }))"
              label="UGREEN NAS / Host-Asset"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select v-model="dockerForm.refresh_interval_seconds" :items="intervalItems" label="Aktualisierungsintervall" hide-details />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field v-model="dockerForm.socket_path" label="Docker-Socket" hide-details />
          </v-col>
        </v-row>
        <div class="d-flex flex-wrap align-center ga-2 mt-4">
          <v-btn variant="tonal" prepend-icon="mdi-content-save" :loading="settingsSaving" @click="saveDockerSettings">Einstellungen speichern</v-btn>
          <v-btn variant="text" prepend-icon="mdi-connection" :loading="testing" @click="testDocker">Verbindung testen</v-btn>
          <v-chip v-if="testResult" :color="testResult.success ? 'success' : 'error'" variant="tonal">
            {{ testResult.message }}<span v-if="testResult.docker_version"> · Docker {{ testResult.docker_version }}</span>
          </v-chip>
          <v-spacer />
          <span class="text-caption text-medium-emphasis">Letzter Erfolg: {{ formatDateTime(dockerSettings?.last_success_at ?? null) }}</span>
        </div>
        <v-alert v-if="dockerSettings?.last_error" type="warning" density="compact" variant="tonal" class="mt-3">
          Letzte Aktualisierung fehlgeschlagen: {{ dockerSettings.last_error }}
        </v-alert>
        <v-alert type="info" density="compact" variant="tonal" class="mt-3">
          DocOfHome verwendet ausschließlich lesende Docker-API-Aufrufe. Der Socket muss dem Container als <code>/var/run/docker.sock</code> bereitgestellt werden.
        </v-alert>
      </v-card-text>
    </v-card>

    <div class="d-flex flex-wrap ga-2 mb-4">
      <v-chip prepend-icon="mdi-docker" variant="tonal">{{ dockerManagedCount }} aus Docker</v-chip>
      <v-chip prepend-icon="mdi-play-circle-outline" color="success" variant="tonal">{{ runningCount }} laufen</v-chip>
      <v-chip variant="tonal">{{ workloads.length }} insgesamt</v-chip>
    </div>

    <v-row>
      <v-col v-for="item in workloads" :key="item.id" cols="12" md="6" xl="4">
        <v-card class="h-100" prepend-icon="mdi-docker">
          <v-card-title class="d-flex align-center ga-2">
            <span>{{ item.name }}</span>
            <v-chip v-if="item.docker_managed" size="x-small" color="primary" variant="tonal">Docker</v-chip>
          </v-card-title>
          <v-card-subtitle>{{ item.host_name }} · {{ item.image || 'Manueller Dienst' }}<span v-if="item.image_tag">:{{ item.image_tag }}</span></v-card-subtitle>
          <v-card-text>
            <v-chip size="small" class="mr-2">{{ item.network_mode }}</v-chip>
            <v-chip size="small" :color="item.status === 'running' ? 'success' : item.status === 'unknown' ? 'warning' : undefined">{{ item.status }}</v-chip>
            <div v-if="item.docker_status_text" class="text-caption text-medium-emphasis mt-2">{{ item.docker_status_text }}</div>
            <p v-if="item.ports.length" class="mt-3 mb-0"><strong>Ports:</strong> {{ item.ports.map(port => `${port.host_port ?? '–'}→${port.container_port}/${port.protocol}`).join(', ') }}</p>
            <p v-if="item.docker_networks.length" class="mt-2 mb-0"><strong>Netze:</strong> {{ item.docker_networks.join(', ') }}</p>
            <p v-if="item.docker_mounts.length" class="mt-2 mb-0"><strong>Mounts:</strong> {{ item.docker_mounts.join(' · ') }}</p>
            <p v-if="item.reverse_proxy" class="mt-2 mb-0">Reverse Proxy: {{ item.reverse_proxy }}</p>
            <div v-if="item.docker_last_seen_at" class="text-caption text-medium-emphasis mt-3">Zuletzt von Docker gesehen: {{ formatDateTime(item.docker_last_seen_at) }}</div>
          </v-card-text>
          <v-card-actions><v-btn variant="text" @click="open(item)">Bearbeiten</v-btn><v-spacer /><v-btn color="warning" variant="text" @click="archive(item)">Archivieren</v-btn></v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-empty-state v-if="!workloads.length" icon="mdi-docker" title="Noch keine Dienste" text="Wähle das UGREEN NAS als Host und starte den ersten Docker-Abgleich oder lege einen Dienst manuell an." />

    <v-dialog v-model="dialog" max-width="820">
      <v-card :title="editing ? 'Dienst bearbeiten' : 'Dienst anlegen'" prepend-icon="mdi-docker">
        <v-card-text>
          <v-alert v-if="editing?.docker_managed" type="info" variant="tonal" density="compact" class="mb-4">
            Docker-Status, Image, Ports, Netze und Mounts werden beim nächsten Abgleich erneut aus Docker übernommen. Notizen und URLs bleiben manuell gepflegt.
          </v-alert>
          <v-select v-model="form.host_asset_id" :items="assets.map(asset => ({ value: asset.id, title: `${asset.name} · ${asset.jarvis_code}` }))" label="Host-Asset" />
          <v-row><v-col cols="12" sm="6"><v-text-field v-model="form.name" label="Dienst-/Containername" autofocus /></v-col><v-col cols="12" sm="6"><v-select v-model="form.status" :items="['running','stopped','planned','unknown']" label="Status" /></v-col></v-row>
          <v-row><v-col cols="12" sm="6"><v-text-field v-model="form.image" label="Image" clearable /></v-col><v-col cols="12" sm="6"><v-text-field v-model="form.image_tag" label="Tag" clearable /></v-col></v-row>
          <v-row><v-col cols="12" sm="6"><v-text-field v-model="form.compose_project" label="Compose-Projekt" clearable /></v-col><v-col cols="12" sm="6"><v-select v-model="form.network_mode" :items="['bridge','host','macvlan','docker_network']" label="Netzwerkmodus" /></v-col></v-row>
          <v-text-field v-if="form.network_mode === 'macvlan'" v-model="form.macvlan_address" label="Eigene IP-Adresse" />
          <v-text-field v-model="form.reverse_proxy" label="Reverse-Proxy-Zuordnung" clearable />
          <v-row><v-col cols="12" sm="6"><v-text-field v-model="form.urls.internal" label="Interne URL" clearable /></v-col><v-col cols="12" sm="6"><v-text-field v-model="form.urls.external" label="Externe URL" clearable /></v-col></v-row>
          <v-textarea v-model="form.notes" label="Notizen" rows="4" clearable />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!form.host_asset_id || !form.name.trim()" @click="save">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

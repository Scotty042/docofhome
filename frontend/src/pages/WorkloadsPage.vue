<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { assetApi } from '../services/assetApi'
import { releaseApi } from '../services/releaseApi'
import type { Asset } from '../types/assets'
import type {
  DockerConnectionTest,
  DockerHost,
  DockerHostWrite,
  ServiceWorkload,
  ServiceWorkloadWrite
} from '../types/release'
import { copyText } from '../utils/clipboard'

const workloads = ref<ServiceWorkload[]>([])
const assets = ref<Asset[]>([])
const error = ref<string | null>(null)
const saving = ref(false)
const syncing = ref(false)
const dialog = ref(false)
const editing = ref<ServiceWorkload | null>(null)
const form = ref<ServiceWorkloadWrite>(emptyForm())
const dockerHosts = ref<DockerHost[]>([])
const hostDialog = ref(false)
const editingHost = ref<DockerHost | null>(null)
const hostForm = ref<DockerHostWrite>(emptyHostForm())
const hostSaving = ref(false)
const activeHostId = ref<string | null>(null)
const testResults = ref<Record<string, DockerConnectionTest>>({})
const copiedKey = ref<string | null>(null)
const selectedHostId = ref<string | null>(null)
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
const filteredWorkloads = computed(() => selectedHostId.value
  ? workloads.value.filter((item) => item.host_asset_id === selectedHostId.value)
  : workloads.value)

function emptyForm(): ServiceWorkloadWrite {
  return {
    host_asset_id: '', name: '', image: null, image_tag: null, compose_project: null,
    network_mode: 'bridge', macvlan_address: null, ports: [],
    urls: { internal: null, external: null, administrative: null, api: null },
    reverse_proxy: null, dependency_ids: [], status: 'unknown', notes: null
  }
}

function emptyHostForm(): DockerHostWrite {
  return {
    name: '', enabled: false, connection_type: 'ssh', host_asset_id: '',
    socket_path: null, ssh_host: null, ssh_port: 22, ssh_user: 'docofhome-monitor',
    ssh_host_key: null, refresh_interval_seconds: 300
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
    const [items, hosts] = await Promise.all([
      releaseApi.workloads(),
      releaseApi.dockerHosts()
    ])
    workloads.value = items
    dockerHosts.value = hosts
  } catch {
    // Keep the last known state visible. Sync failures are persisted by the backend.
  }
}

async function load() {
  try {
    const [items, assetPage, hosts] = await Promise.all([
      releaseApi.workloads(),
      assetApi.allAssets(),
      releaseApi.dockerHosts()
    ])
    workloads.value = items
    assets.value = assetPage
    dockerHosts.value = hosts
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dienste konnten nicht geladen werden.'
  }
}

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

function openHost(host?: DockerHost) {
  editingHost.value = host ?? null
  hostForm.value = host ? {
    name: host.name, enabled: host.enabled, connection_type: host.connection_type,
    host_asset_id: host.host_asset_id, socket_path: host.socket_path,
    ssh_host: host.ssh_host, ssh_port: host.ssh_port, ssh_user: host.ssh_user,
    ssh_host_key: host.ssh_host_key, refresh_interval_seconds: host.refresh_interval_seconds
  } : emptyHostForm()
  hostDialog.value = true
}

async function saveHost(): Promise<DockerHost | null> {
  hostSaving.value = true
  error.value = null
  try {
    if (hostForm.value.connection_type === 'socket' && !hostForm.value.socket_path) {
      hostForm.value.socket_path = '/var/run/docker.sock'
    }
    if (hostForm.value.connection_type === 'ssh' && !hostForm.value.ssh_user) {
      hostForm.value.ssh_user = 'docofhome-monitor'
    }
    const saved = editingHost.value
      ? await releaseApi.updateDockerHost(editingHost.value.id, hostForm.value)
      : await releaseApi.createDockerHost(hostForm.value)
    await refreshDockerView()
    editingHost.value = saved
    hostForm.value = { ...hostForm.value, ssh_host_key: saved.ssh_host_key }
    return saved
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Docker-Host konnte nicht gespeichert werden.'
    return null
  } finally {
    hostSaving.value = false
  }
}

async function scanHostKey() {
  const saved = await saveHost()
  if (!saved) return
  activeHostId.value = saved.id
  error.value = null
  try {
    const scanned = await releaseApi.scanDockerHostKey(saved.id)
    hostForm.value.ssh_host_key = scanned.host_key
    testResults.value[saved.id] = {
      success: true, message: `Server-Fingerabdruck: ${scanned.fingerprint}`, docker_version: null
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Server-Schlüssel konnte nicht gelesen werden.'
  } finally {
    activeHostId.value = null
  }
}

async function testDockerHost(host: DockerHost) {
  activeHostId.value = host.id
  error.value = null
  try {
    testResults.value[host.id] = await releaseApi.testDockerHost(host.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindung konnte nicht getestet werden.'
  } finally {
    activeHostId.value = null
  }
}

async function syncDockerHost(host: DockerHost) {
  activeHostId.value = host.id
  syncing.value = true
  error.value = null
  try {
    await releaseApi.syncDockerHost(host.id)
    await refreshDockerView()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Docker-Container konnten nicht aktualisiert werden.'
    await refreshDockerView()
  } finally {
    syncing.value = false
    activeHostId.value = null
  }
}

async function deleteHost(host: DockerHost) {
  if (!confirm(`Docker-Verbindung „${host.name}“ entfernen? Erfasste Dienste bleiben erhalten.`)) return
  await releaseApi.deleteDockerHost(host.id)
  await refreshDockerView()
}

async function copyPublicKey(host: DockerHost) {
  if (!host.public_key) return
  await copyText(host.public_key)
  copiedKey.value = host.id
}

onMounted(() => {
  void load()
  refreshTimer = window.setInterval(() => void refreshDockerView(), 30000)
})
onBeforeUnmount(() => {
  if (refreshTimer !== null) window.clearInterval(refreshTimer)
})
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div>
        <h1>Dienste & Container</h1>
        <p class="text-medium-emphasis mb-0">Container mehrerer Docker-Server per SSH oder lokalem Socket überwachen.</p>
      </div>
      <v-spacer />
      <v-btn variant="tonal" prepend-icon="mdi-server-plus" @click="openHost()">Docker-Host</v-btn>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="open()">Dienst</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

    <v-card class="mb-5" title="Docker-Hosts" prepend-icon="mdi-server-network">
      <v-card-text>
        <v-alert type="info" density="compact" variant="tonal" class="mt-3">
          Für SSH wird pro Host ein eigener Schlüssel erzeugt. Auf dem Server sollte der Public Key
          ausschließlich mit dem mitgelieferten, erzwungenen Lesebefehl freigeschaltet werden.
        </v-alert>
        <v-row class="mt-1">
          <v-col v-for="host in dockerHosts" :key="host.id" cols="12" lg="6">
            <v-card variant="outlined">
              <v-card-title class="d-flex align-center ga-2">
                <span>{{ host.name }}</span>
                <v-chip size="x-small" :color="host.enabled ? 'success' : undefined">{{ host.enabled ? 'aktiv' : 'inaktiv' }}</v-chip>
                <v-chip size="x-small" variant="tonal">{{ host.connection_type === 'ssh' ? 'SSH' : 'Socket' }}</v-chip>
              </v-card-title>
              <v-card-subtitle>{{ host.host_name }}<span v-if="host.ssh_host"> · {{ host.ssh_user }}@{{ host.ssh_host }}:{{ host.ssh_port }}</span></v-card-subtitle>
              <v-card-text>
                <div>Letzter Erfolg: {{ formatDateTime(host.last_success_at) }}</div>
                <div v-if="host.host_key_fingerprint" class="text-caption mt-1">Server: {{ host.host_key_fingerprint }}</div>
                <v-alert v-if="host.last_error" type="warning" density="compact" variant="tonal" class="mt-3">{{ host.last_error }}</v-alert>
                <v-alert v-if="testResults[host.id]" :type="testResults[host.id].success ? 'success' : 'error'" density="compact" variant="tonal" class="mt-3">
                  {{ testResults[host.id].message }}<span v-if="testResults[host.id].docker_version"> · Docker {{ testResults[host.id].docker_version }}</span>
                </v-alert>
              </v-card-text>
              <v-card-actions>
                <v-btn variant="text" @click="openHost(host)">Einrichten</v-btn>
                <v-btn variant="text" :loading="activeHostId === host.id" @click="testDockerHost(host)">Testen</v-btn>
                <v-btn variant="text" prepend-icon="mdi-refresh" :loading="syncing && activeHostId === host.id" @click="syncDockerHost(host)">Abgleichen</v-btn>
                <v-spacer />
                <v-btn color="warning" variant="text" @click="deleteHost(host)">Entfernen</v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        <v-empty-state v-if="!dockerHosts.length" icon="mdi-server-plus" title="Noch kein Docker-Host" text="Lege deinen NUC, dein NAS oder einen lokalen Docker-Host an." />
      </v-card-text>
    </v-card>

    <div class="d-flex flex-wrap ga-2 mb-4">
      <v-chip prepend-icon="mdi-docker" variant="tonal">{{ dockerManagedCount }} aus Docker</v-chip>
      <v-chip prepend-icon="mdi-play-circle-outline" color="success" variant="tonal">{{ runningCount }} laufen</v-chip>
      <v-chip variant="tonal">{{ workloads.length }} insgesamt</v-chip>
      <v-select
        v-model="selectedHostId"
        :items="dockerHosts.map(host => ({ value: host.host_asset_id, title: host.name }))"
        label="Nach Docker-Host filtern"
        clearable
        hide-details
        density="compact"
        style="max-width: 280px"
      />
    </div>

    <v-row>
      <v-col v-for="item in filteredWorkloads" :key="item.id" cols="12" md="6" xl="4">
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
    <v-empty-state v-if="!filteredWorkloads.length" icon="mdi-docker" title="Noch keine Dienste" text="Richte einen Docker-Host ein und starte den ersten Abgleich oder lege einen Dienst manuell an." />

    <v-dialog v-model="hostDialog" max-width="820" persistent>
      <v-card :title="editingHost ? 'Docker-Host einrichten' : 'Docker-Host anlegen'" prepend-icon="mdi-server-network">
        <v-card-text>
          <v-text-field v-model="hostForm.name" label="Bezeichnung" placeholder="Docker NUC" />
          <v-autocomplete
            v-model="hostForm.host_asset_id"
            :items="assets.map(asset => ({ value: asset.id, title: `${asset.name} · ${asset.jarvis_code}` }))"
            label="Host-Asset"
          />
          <v-row>
            <v-col cols="12" sm="6"><v-select v-model="hostForm.connection_type" :items="[{ title: 'SSH (empfohlen)', value: 'ssh' }, { title: 'Lokaler Docker-Socket', value: 'socket' }]" label="Verbindung" /></v-col>
            <v-col cols="12" sm="6"><v-select v-model="hostForm.refresh_interval_seconds" :items="intervalItems" label="Aktualisierungsintervall" /></v-col>
          </v-row>
          <v-switch v-model="hostForm.enabled" label="Automatische Aktualisierung" color="primary" />
          <v-text-field v-if="hostForm.connection_type === 'socket'" v-model="hostForm.socket_path" label="Docker-Socket" placeholder="/var/run/docker.sock" />
          <template v-else>
            <v-row>
              <v-col cols="12" sm="7"><v-text-field v-model="hostForm.ssh_host" label="Hostname oder IP-Adresse" /></v-col>
              <v-col cols="12" sm="5"><v-text-field v-model.number="hostForm.ssh_port" type="number" label="SSH-Port" /></v-col>
            </v-row>
            <v-text-field v-model="hostForm.ssh_user" label="SSH-Benutzer" />
            <v-alert type="warning" density="compact" variant="tonal" class="mb-4">
              Prüfe den angezeigten Fingerabdruck gegen den NUC, bevor du ihn speicherst.
            </v-alert>
            <div class="d-flex flex-wrap ga-2 mb-3">
              <v-btn variant="tonal" :loading="activeHostId === editingHost?.id" @click="scanHostKey">Server-Schlüssel abrufen</v-btn>
              <v-chip v-if="hostForm.ssh_host_key" color="success" variant="tonal">Serveridentität vorgemerkt</v-chip>
            </div>
            <v-textarea v-if="editingHost?.public_key" :model-value="editingHost.public_key" label="Public Key für authorized_keys" rows="3" readonly />
            <v-btn v-if="editingHost?.public_key" variant="text" prepend-icon="mdi-content-copy" @click="copyPublicKey(editingHost)">
              {{ copiedKey === editingHost.id ? 'Kopiert' : 'Public Key kopieren' }}
            </v-btn>
            <v-alert v-if="testResults[editingHost?.id ?? '']" type="info" density="compact" variant="tonal" class="mt-3">
              {{ testResults[editingHost?.id ?? ''].message }}
            </v-alert>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="hostDialog = false">Schließen</v-btn>
          <v-btn color="primary" :loading="hostSaving" :disabled="!hostForm.name.trim() || !hostForm.host_asset_id" @click="saveHost">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { assetApi } from '../services/assetApi'
import { releaseApi } from '../services/releaseApi'
import type { Asset } from '../types/assets'
import type { ServiceWorkload, ServiceWorkloadWrite } from '../types/release'

const workloads = ref<ServiceWorkload[]>([])
const assets = ref<Asset[]>([])
const error = ref<string | null>(null)
const saving = ref(false)
const dialog = ref(false)
const editing = ref<ServiceWorkload | null>(null)
const form = ref<ServiceWorkloadWrite>(emptyForm())

function emptyForm(): ServiceWorkloadWrite {
  return {
    host_asset_id: '', name: '', image: null, image_tag: null, compose_project: null,
    network_mode: 'bridge', macvlan_address: null, ports: [],
    urls: { internal: null, external: null, administrative: null, api: null },
    reverse_proxy: null, dependency_ids: [], status: 'unknown', notes: null
  }
}

async function load() {
  try {
    const [items, assetPage] = await Promise.all([releaseApi.workloads(), assetApi.list({ page_size: 100 })])
    workloads.value = items
    assets.value = assetPage.items
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
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dienst konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archive(item: ServiceWorkload) {
  if (!confirm(`Dienst „${item.name}“ archivieren?`)) return
  await releaseApi.archiveWorkload(item.id)
  await load()
}

onMounted(load)
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div><h1>Dienste & Container</h1><p class="text-medium-emphasis mb-0">Logische Workloads bleiben ihrem physischen Host-Asset zugeordnet.</p></div>
      <v-spacer /><v-btn color="primary" prepend-icon="mdi-plus" @click="open()">Dienst</v-btn>
    </div>
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-row>
      <v-col v-for="item in workloads" :key="item.id" cols="12" md="6" xl="4">
        <v-card class="h-100" prepend-icon="mdi-docker">
          <v-card-title>{{ item.name }}</v-card-title>
          <v-card-subtitle>{{ item.host_name }} · {{ item.image || 'Manueller Dienst' }}<span v-if="item.image_tag">:{{ item.image_tag }}</span></v-card-subtitle>
          <v-card-text>
            <v-chip size="small" class="mr-2">{{ item.network_mode }}</v-chip>
            <v-chip size="small" :color="item.status === 'running' ? 'success' : undefined">{{ item.status }}</v-chip>
            <p v-if="item.ports.length" class="mt-3 mb-0">{{ item.ports.map(port => `${port.host_port ?? '–'}→${port.container_port}/${port.protocol}`).join(', ') }}</p>
            <p v-if="item.reverse_proxy" class="mt-2 mb-0">Reverse Proxy: {{ item.reverse_proxy }}</p>
          </v-card-text>
          <v-card-actions><v-btn variant="text" @click="open(item)">Bearbeiten</v-btn><v-spacer /><v-btn color="warning" variant="text" @click="archive(item)">Archivieren</v-btn></v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-empty-state v-if="!workloads.length" icon="mdi-docker" title="Noch keine logischen Dienste" text="Die Pflege ist vollständig manuell möglich und benötigt keinen Docker-Socket." />

    <v-dialog v-model="dialog" max-width="820">
      <v-card :title="editing ? 'Dienst bearbeiten' : 'Dienst anlegen'" prepend-icon="mdi-docker">
        <v-card-text>
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

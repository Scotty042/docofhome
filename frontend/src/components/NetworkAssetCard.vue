<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { networkApi } from '../services/networkApi'
import type { NetworkDevice, NetworkDeviceWrite, NetworkRole } from '../types/network'
import { networkRoleIcons, networkRoleLabels } from '../types/network'

const props = defineProps<{ assetId: string; assetName: string; readOnly?: boolean }>()
const device = ref<NetworkDevice | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const dialog = ref(false)
const form = ref<NetworkDeviceWrite>({
  asset_id: props.assetId,
  role: 'other',
  hostname: null,
  management_url: null,
  notes: null
})
const roleItems = Object.entries(networkRoleLabels).map(([value, title]) => ({ value, title })) as Array<{ value: NetworkRole; title: string }>

async function load() {
  loading.value = true
  error.value = null
  try {
    const devices = await networkApi.devices({ includeArchived: false })
    device.value = devices.find((item) => item.asset_id === props.assetId) ?? null
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkrolle konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = {
    asset_id: props.assetId,
    role: 'other',
    hostname: null,
    management_url: null,
    notes: null
  }
  dialog.value = true
}

async function create() {
  saving.value = true
  error.value = null
  try {
    device.value = await networkApi.createDevice(form.value)
    dialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkrolle konnte nicht angelegt werden.'
  } finally {
    saving.value = false
  }
}

onMounted(() => void load())
watch(() => props.assetId, () => void load())
</script>

<template>
  <v-card title="Netzwerk" prepend-icon="mdi-lan" class="mb-5">
    <template #append>
      <v-btn
        v-if="device"
        size="small"
        variant="tonal"
        prepend-icon="mdi-open-in-new"
        :to="`/network/devices/${device.id}`"
      >Öffnen</v-btn>
      <v-btn
        v-else-if="!readOnly"
        size="small"
        variant="tonal"
        prepend-icon="mdi-lan-connect"
        @click="openCreate"
      >Netzwerkrolle</v-btn>
    </template>
    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
    <v-list v-if="device" lines="two">
      <v-list-item :prepend-icon="networkRoleIcons[device.role]">
        <v-list-item-title>{{ networkRoleLabels[device.role] }}<span v-if="device.hostname"> · {{ device.hostname }}</span></v-list-item-title>
        <v-list-item-subtitle>{{ device.interface_count }} Schnittstellen · {{ device.address_count }} IP-Adressen · {{ device.connection_count }} Verbindungen</v-list-item-subtitle>
      </v-list-item>
    </v-list>
    <v-card-text v-else-if="!loading" class="text-medium-emphasis">
      Dieses Asset besitzt noch keine Netzwerkrolle.
    </v-card-text>
  </v-card>

  <v-dialog v-model="dialog" max-width="660">
    <v-card title="Netzwerkrolle anlegen" prepend-icon="mdi-server-network">
      <v-card-text>
        <v-alert type="info" variant="tonal" density="compact" class="mb-4">
          Das vorhandene Asset „{{ assetName }}“ bleibt die Geräteidentität. Das Netzwerkmodul ergänzt nur technische Netzwerkdaten.
        </v-alert>
        <v-select v-model="form.role" :items="roleItems" label="Rolle" class="mb-3" />
        <v-text-field v-model="form.hostname" label="Hostname" class="mb-3" />
        <v-text-field v-model="form.management_url" label="Management-URL" class="mb-3" />
        <v-textarea v-model="form.notes" label="Netzwerknotizen" rows="3" />
      </v-card-text>
      <v-card-actions><v-spacer /><v-btn @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="create">Anlegen</v-btn></v-card-actions>
    </v-card>
  </v-dialog>
</template>

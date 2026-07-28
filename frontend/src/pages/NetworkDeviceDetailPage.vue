<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import NotesCard from '../components/NotesCard.vue'
import { networkApi } from '../services/networkApi'
import { releaseApi } from '../services/releaseApi'
import type {
  NetworkAddress,
  NetworkAddressWrite,
  NetworkAssignmentType,
  NetworkConnection,
  NetworkDevice,
  NetworkDeviceWrite,
  NetworkInterface,
  NetworkInterfaceType,
  NetworkInterfaceWrite,
  NetworkIpOverview,
  NetworkPoeMode,
  NetworkRole,
  NetworkSegment
} from '../types/network'
import { networkRoleIcons, networkRoleLabels } from '../types/network'
import type { NetworkPath, PortGenerationPreview, PortGroupWrite } from '../types/release'

const route = useRoute()
const router = useRouter()
const deviceId = computed(() => String(route.params.id))
const device = ref<NetworkDevice | null>(null)
const interfaces = ref<NetworkInterface[]>([])
const addresses = ref<NetworkAddress[]>([])
const segments = ref<NetworkSegment[]>([])
const connections = ref<NetworkConnection[]>([])
const ipOverview = ref<NetworkIpOverview[]>([])
const ipMismatches = computed(() => ipOverview.value.filter((item) => item.status === 'mismatch' || item.status === 'conflict'))
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const portDialog = ref(false)
const pathDialog = ref(false)
const portPreview = ref<PortGenerationPreview | null>(null)
const documentedPath = ref<NetworkPath | null>(null)
const portGroups = ref<PortGroupWrite[]>([
  { group: 'copper', count: 24, scheme: 'numeric', start: 1, speed_mbps: 1000, poe_capable: false }
])

const deviceDialog = ref(false)
const deviceForm = ref<NetworkDeviceWrite>({ asset_id: '', role: 'other', hostname: null, management_url: null, notes: null })
const interfaceDialog = ref(false)
const editingInterface = ref<NetworkInterface | null>(null)
const interfaceForm = ref<NetworkInterfaceWrite>({
  network_device_id: '', name: '', interface_type: 'ethernet', mac_address: null,
  speed_mbps: null, poe_mode: 'none', enabled: true, is_primary: false, logical_interface_id: null, description: null
})
const addressDialog = ref(false)
const editingAddress = ref<NetworkAddress | null>(null)
const addressForm = ref<NetworkAddressWrite>({
  interface_id: '', segment_id: null, address: '', assignment_type: 'unknown',
  hostname: null, is_primary: false, notes: null
})

const roleItems = Object.entries(networkRoleLabels).map(([value, title]) => ({
  value: value as NetworkRole, title
}))
const interfaceTypeItems: Array<{ value: NetworkInterfaceType; title: string }> = [
  { value: 'ethernet', title: 'Ethernet/Kupfer' }, { value: 'fiber', title: 'Glasfaser' },
  { value: 'wifi', title: 'WLAN' }, { value: 'virtual', title: 'Virtuell' },
  { value: 'cellular', title: 'Mobilfunk' }, { value: 'other', title: 'Sonstiges' }
]
const poeItems: Array<{ value: NetworkPoeMode; title: string }> = [
  { value: 'none', title: 'Kein PoE' }, { value: 'source', title: 'PoE-Quelle (PSE)' },
  { value: 'sink', title: 'PoE-Verbraucher (PD)' }, { value: 'passive', title: 'Passives PoE' },
  { value: 'unknown', title: 'Unbekannt' }
]
const connectionTypeLabels: Record<NetworkConnection['connection_type'], string> = {
  physical: 'Physisch', logical: 'Logisch', wireless: 'WLAN/Funk'
}
const connectionStatusLabels: Record<NetworkConnection['status'], string> = {
  active: 'Aktiv', planned: 'Geplant', inactive: 'Inaktiv'
}
const speedItems = [
  { value: 100, title: '100 Mbit/s' },
  { value: 1000, title: '1 Gbit/s' },
  { value: 2500, title: '2,5 Gbit/s' }
]
const assignmentItems: Array<{ value: NetworkAssignmentType; title: string }> = [
  { value: 'static', title: 'Statisch' }, { value: 'dhcp', title: 'DHCP' },
  { value: 'reservation', title: 'DHCP-Reservierung' }, { value: 'link_local', title: 'Link-local' },
  { value: 'unknown', title: 'Unbekannt' }
]
const segmentItems = computed(() => segments.value.map((item) => ({
  value: item.id, title: `${item.name} · ${item.cidr}${item.vlan_id ? ` · VLAN ${item.vlan_id}` : ''}`
})))
const logicalInterfaceItems = computed(() => interfaces.value
  .filter((item) => item.interface_type === 'virtual' && item.id !== editingInterface.value?.id)
  .map((item) => ({ value: item.id, title: `${item.name}${item.address_count ? ` · ${item.address_count} IP` : ''}` })))

const connectedInterfaceIds = computed(() => new Set(connections.value
  .filter((item) => item.status === 'active')
  .flatMap((item) => [item.source_interface_id, item.target_interface_id])))
function portNumber(name: string): number {
  const match = name.match(/(\d+)(?!.*\d)/)
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER
}
const physicalInterfaces = computed(() => interfaces.value.filter(
  (item) => item.interface_type !== 'virtual'
).sort((left, right) => portNumber(left.name) - portNumber(right.name) || left.name.localeCompare(right.name, 'de', { numeric: true })))
const standardSwitchPorts = computed(() => physicalInterfaces.value.filter(
  (item) => !/sfp|uplink/i.test(item.name)
))
const switchPortRows = computed(() => {
  if (device.value?.switch_port_layout === 'sequential_halves') {
    const split = Math.ceil(standardSwitchPorts.value.length / 2)
    return [standardSwitchPorts.value.slice(0, split), standardSwitchPorts.value.slice(split)]
  }
  return [
    standardSwitchPorts.value.filter((item) => portNumber(item.name) % 2 === 1),
    standardSwitchPorts.value.filter((item) => portNumber(item.name) % 2 === 0)
  ]
})
const switchUplinkPorts = computed(() => physicalInterfaces.value.filter(
  (item) => /sfp|uplink/i.test(item.name)
))
const hostnameError = computed(() => {
  const value = deviceForm.value.hostname?.trim() ?? ''
  if (!value) return ''
  if (value.includes('_')) return 'Unterstriche sind in Hostnamen nicht erlaubt. Verwenden Sie stattdessen einen Bindestrich.'
  return /^[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?$/.test(value)
    ? ''
    : 'Nur Buchstaben, Ziffern, Punkte und Bindestriche sind erlaubt.'
})
const hostnameSuggestion = computed(() => deviceForm.value.hostname?.replaceAll('_', '-') ?? '')
function applyHostnameSuggestion() {
  deviceForm.value.hostname = hostnameSuggestion.value || null
}
function isNeutralFreePort(item: NetworkInterface) {
  return item.enabled
    && ['ethernet', 'fiber', 'other'].includes(item.interface_type)
    && !connectedInterfaceIds.value.has(item.id)
}

const addressesByInterface = computed(() => {
  const result = new Map<string, NetworkAddress[]>()
  for (const item of interfaces.value) result.set(item.id, [])
  for (const item of addresses.value) result.get(item.interface_id)?.push(item)
  return result
})

async function load() {
  loading.value = true
  error.value = null
  try {
    const [deviceData, interfaceData, addressData, segmentData, connectionData, ipData] = await Promise.all([
      networkApi.device(deviceId.value), networkApi.interfaces(deviceId.value),
      networkApi.addresses({ deviceId: deviceId.value }), networkApi.segments(),
      networkApi.connections(deviceId.value), networkApi.ipAddresses({ deviceId: deviceId.value })
    ])
    device.value = deviceData
    interfaces.value = interfaceData
    addresses.value = addressData
    segments.value = segmentData
    connections.value = connectionData
    ipOverview.value = ipData
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkgerät konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function openDeviceEditor() {
  if (!device.value) return
  deviceForm.value = {
    asset_id: device.value.asset_id,
    role: device.value.role,
    hostname: device.value.hostname,
    management_url: device.value.management_url,
    notes: device.value.notes
  }
  deviceDialog.value = true
}

async function saveDevice() {
  if (!device.value) return
  saving.value = true
  error.value = null
  try {
    device.value = await networkApi.updateDevice(device.value.id, deviceForm.value)
    deviceDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Gerät konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function openInterface(item?: NetworkInterface) {
  editingInterface.value = item ?? null
  interfaceForm.value = item ? {
    network_device_id: item.network_device_id,
    name: item.name,
    interface_type: item.interface_type,
    mac_address: item.mac_address,
    speed_mbps: item.speed_mbps,
    poe_mode: item.poe_mode,
    enabled: item.enabled,
    is_primary: item.is_primary,
    logical_interface_id: item.logical_interface_id,
    description: item.description
  } : {
    network_device_id: deviceId.value, name: '', interface_type: 'ethernet', mac_address: null,
    speed_mbps: null, poe_mode: 'none', enabled: true, is_primary: false, logical_interface_id: null, description: null
  }
  interfaceDialog.value = true
}

async function saveInterface() {
  const rawSpeed = interfaceForm.value.speed_mbps as number | string | null
  interfaceForm.value.speed_mbps = rawSpeed === null || rawSpeed === '' ? null : Number(rawSpeed)
  saving.value = true
  error.value = null
  try {
    if (editingInterface.value) await networkApi.updateInterface(editingInterface.value.id, interfaceForm.value)
    else await networkApi.createInterface(interfaceForm.value)
    interfaceDialog.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Schnittstelle konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeInterface(item: NetworkInterface) {
  if (!confirm(`Schnittstelle „${item.name}“ archivieren? Zugeordnete IP-Adressen und Verbindungen werden ebenfalls archiviert.`)) return
  try {
    await networkApi.deleteInterface(item.id)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Schnittstelle konnte nicht archiviert werden.'
  }
}

function openAddress(interfaceId: string, item?: NetworkAddress) {
  editingAddress.value = item ?? null
  addressForm.value = item ? {
    interface_id: item.interface_id,
    segment_id: item.segment_id,
    address: item.address,
    assignment_type: item.assignment_type,
    hostname: item.hostname,
    is_primary: item.is_primary,
    notes: item.notes
  } : {
    interface_id: interfaceId, segment_id: null, address: '', assignment_type: 'unknown',
    hostname: device.value?.hostname ?? null, is_primary: addresses.value.length === 0, notes: null
  }
  addressDialog.value = true
}

async function saveAddress() {
  saving.value = true
  error.value = null
  try {
    if (editingAddress.value) await networkApi.updateAddress(editingAddress.value.id, addressForm.value)
    else await networkApi.createAddress(addressForm.value)
    addressDialog.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'IP-Adresse konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeAddress(item: NetworkAddress) {
  if (!confirm(`IP-Adresse ${item.address} archivieren?`)) return
  try {
    await networkApi.deleteAddress(item.id)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'IP-Adresse konnte nicht archiviert werden.'
  }
}

async function archiveDevice() {
  if (!device.value || !confirm(`Netzwerkrolle von „${device.value.asset_name}“ archivieren? Das Asset selbst bleibt erhalten.`)) return
  try {
    await networkApi.deleteDevice(device.value.id)
    await router.push('/network')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkgerät konnte nicht archiviert werden.'
  }
}

async function previewPorts() {
  saving.value = true
  try {
    portPreview.value = await releaseApi.previewPorts(deviceId.value, portGroups.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Portvorschau konnte nicht erstellt werden.'
  } finally {
    saving.value = false
  }
}

async function generatePorts() {
  saving.value = true
  try {
    portPreview.value = await releaseApi.generatePorts(deviceId.value, portGroups.value)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Ports konnten nicht erzeugt werden.'
  } finally {
    saving.value = false
  }
}

async function showPath() {
  try {
    documentedPath.value = await releaseApi.networkPath(deviceId.value)
    pathDialog.value = true
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindungspfad konnte nicht ermittelt werden.'
  }
}

onMounted(() => void load())
watch(deviceId, () => void load())
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <v-btn icon="mdi-arrow-left" variant="text" aria-label="Zur Netzwerkübersicht" to="/network" />
      <div v-if="device">
        <h1 class="text-h4 d-flex align-center ga-2"><v-icon :icon="networkRoleIcons[device.role]" />{{ device.asset_name }}</h1>
        <p class="text-medium-emphasis mb-0">{{ networkRoleLabels[device.role] }} · {{ device.asset_code }}<span v-if="device.hostname"> · {{ device.hostname }}</span></p>
      </div>
      <v-spacer />
      <v-btn v-if="device" variant="tonal" prepend-icon="mdi-package-variant-closed" :to="`/assets/${device.asset_id}`">Asset öffnen</v-btn>
      <v-btn v-if="device" variant="tonal" prepend-icon="mdi-map-marker-path" @click="showPath">Verbindungspfad</v-btn>
      <v-btn v-if="device?.role === 'switch'" variant="tonal" prepend-icon="mdi-ethernet-cable" @click="portDialog = true">Ports erzeugen</v-btn>
      <v-btn v-if="device" variant="tonal" prepend-icon="mdi-pencil" @click="openDeviceEditor">Bearbeiten</v-btn>
      <v-btn v-if="device" color="warning" variant="tonal" prepend-icon="mdi-archive-outline" @click="archiveDevice">Archivieren</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = null">{{ error }}</v-alert>
    <v-alert v-if="ipMismatches.length" type="warning" variant="tonal" class="mb-4" title="IP-Abweichung erkannt">
      <div v-for="item in ipMismatches" :key="item.key">
        {{ item.interface_name || 'Schnittstelle' }}: dokumentiert <strong>{{ item.documented_address || '–' }}</strong>, ausgelesen <strong>{{ item.observed_address || '–' }}</strong>.
      </div>
      <template #append><v-btn variant="text" :to="{ path: '/network', query: { tab: 'ip-addresses' } }">IP-Übersicht</v-btn></template>
    </v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <template v-if="device">
      <v-row class="mb-2">
        <v-col cols="12" md="7">
          <v-card title="Netzwerkprofil" prepend-icon="mdi-information-outline" class="h-100">
            <v-card-text>
              <v-list density="compact" bg-color="transparent">
                <v-list-item prepend-icon="mdi-console-network-outline" title="Hostname" :subtitle="device.hostname ?? 'Nicht hinterlegt'" />
                <v-list-item prepend-icon="mdi-map-marker-outline" title="Standort" :subtitle="device.location_name ?? 'Nicht zugeordnet'" />
                <v-list-item prepend-icon="mdi-package-variant" title="Asset-Typ / Produkt" :subtitle="[device.asset_type, device.product_name].filter(Boolean).join(' · ')" />
                <v-list-item v-if="device.management_url" prepend-icon="mdi-web" title="Management" :href="device.management_url" target="_blank" :subtitle="device.management_url" />
              </v-list>
              <p v-if="device.notes" class="mt-3 mb-0 text-pre-wrap">{{ device.notes }}</p>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="5">
          <v-card title="Zusammenfassung" prepend-icon="mdi-chart-box-outline" class="h-100">
            <v-card-text class="d-flex flex-wrap ga-3">
              <v-chip size="large" prepend-icon="mdi-ethernet">{{ interfaces.length }} Schnittstellen</v-chip>
              <v-chip size="large" prepend-icon="mdi-ip-outline">{{ device.primary_address || `${addresses.length} IP-Adressen` }}</v-chip>
              <v-chip size="large" prepend-icon="mdi-lan-connect">{{ connections.length }} Verbindungen</v-chip>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-card title="Schnittstellen und IP-Adressen" prepend-icon="mdi-ethernet" class="mb-5">
        <template #append><v-btn color="primary" size="small" prepend-icon="mdi-plus" @click="openInterface()">Schnittstelle</v-btn></template>
        <v-card-text v-if="interfaces.length">
          <v-expansion-panels multiple>
            <v-expansion-panel v-for="item in interfaces" :key="item.id">
              <v-expansion-panel-title>
                <div class="d-flex flex-wrap align-center ga-2 w-100">
                  <v-icon :icon="item.interface_type === 'wifi' ? 'mdi-wifi' : item.interface_type === 'fiber' ? 'mdi-lan-connect' : 'mdi-ethernet'" />
                  <strong>{{ item.name }}</strong>
                  <v-chip size="x-small" variant="tonal">{{ item.interface_type }}</v-chip>
                  <v-chip v-if="item.is_primary" size="x-small" color="primary" variant="tonal">Primär</v-chip>
                  <v-chip v-if="item.mac_address" size="x-small" variant="outlined">{{ item.mac_address }}</v-chip>
                  <v-chip v-if="item.logical_interface_name" size="x-small" color="info" prepend-icon="mdi-bridge">Mitglied von {{ item.logical_interface_name }}</v-chip>
                  <v-chip v-if="item.interface_type === 'virtual' && item.member_count" size="x-small" color="primary" prepend-icon="mdi-ethernet">{{ item.member_count }} Mitgliedsports</v-chip>
                  <v-chip v-if="item.speed_mbps" size="x-small" variant="outlined">{{ item.speed_mbps === 1000 ? '1 Gbit/s' : item.speed_mbps === 2500 ? '2,5 Gbit/s' : `${item.speed_mbps} Mbit/s` }}</v-chip>
                  <v-chip v-if="isNeutralFreePort(item)" size="x-small" variant="outlined" color="secondary">Frei</v-chip>
                  <v-chip v-if="!item.enabled" size="x-small" color="warning">Deaktiviert</v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="d-flex flex-wrap ga-2 mb-3">
                  <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="openAddress(item.id)">IP-Adresse</v-btn>
                  <v-btn size="small" variant="text" prepend-icon="mdi-pencil" @click="openInterface(item)">Bearbeiten</v-btn>
                  <v-btn size="small" variant="text" color="warning" prepend-icon="mdi-archive-outline" @click="removeInterface(item)">Archivieren</v-btn>
                </div>
                <v-list v-if="addressesByInterface.get(item.id)?.length" border rounded lines="two">
                  <v-list-item v-for="address in addressesByInterface.get(item.id)" :key="address.id" :prepend-icon="address.is_primary ? 'mdi-star-circle' : 'mdi-ip-outline'">
                    <v-list-item-title><code>{{ address.address }}</code><span v-if="address.hostname"> · {{ address.hostname }}</span></v-list-item-title>
                    <v-list-item-subtitle>{{ address.segment_name ?? 'Ohne Netzzuordnung' }} · {{ address.assignment_type }}</v-list-item-subtitle>
                    <template #append><v-btn icon="mdi-pencil" variant="text" size="small" @click="openAddress(item.id, address)" /><v-btn icon="mdi-archive-outline" color="warning" variant="text" size="small" @click="removeAddress(address)" /></template>
                  </v-list-item>
                </v-list>
                <p v-else class="text-medium-emphasis mb-0">Noch keine IP-Adresse dokumentiert.</p>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-empty-state v-else icon="mdi-ethernet-off" title="Keine Schnittstellen" text="Lege physische oder virtuelle Netzwerkanschlüsse an." />
      </v-card>

      <v-card v-if="device.role === 'switch' && physicalInterfaces.length" title="Switch-Frontansicht" prepend-icon="mdi-switch" class="mb-5">
        <v-card-text>
          <div class="switch-front-scroll" role="region" aria-label="Dokumentierte Switch-Ports">
            <div class="switch-front">
              <div v-for="(row, rowIndex) in switchPortRows" :key="rowIndex" class="switch-port-row" role="list">
                <v-tooltip v-for="port in row" :key="port.id" :text="`${port.name}: ${port.speed_mbps ? (port.speed_mbps === 1000 ? '1 Gbit/s' : port.speed_mbps === 2500 ? '2,5 Gbit/s' : `${port.speed_mbps} Mbit/s`) : 'Geschwindigkeit unbekannt'}`">
                  <template #activator="{ props: tooltipProps }">
                    <button v-bind="tooltipProps" class="switch-port" :class="{ disabled: !port.enabled }" type="button">{{ port.name }}</button>
                  </template>
                </v-tooltip>
              </div>
              <div v-if="switchUplinkPorts.length" class="switch-uplink-block" aria-label="SFP- und Uplink-Ports">
                <v-tooltip v-for="port in switchUplinkPorts" :key="port.id" :text="port.name">
                  <template #activator="{ props: tooltipProps }"><button v-bind="tooltipProps" class="switch-port uplink" type="button">{{ port.name }}</button></template>
                </v-tooltip>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <v-card title="Verbindungen" prepend-icon="mdi-lan-connect" class="mb-5">
        <template #append><v-btn size="small" variant="tonal" prepend-icon="mdi-open-in-new" to="/network?tab=connections">Verwalten</v-btn></template>
        <v-list v-if="connections.length" lines="two">
          <v-list-item v-for="connection in connections" :key="connection.id" prepend-icon="mdi-lan-connect">
            <v-list-item-title>{{ connection.source_device_name }} · {{ connection.source_interface_name }} ↔ {{ connection.target_device_name }} · {{ connection.target_interface_name }}</v-list-item-title>
            <v-list-item-subtitle>{{ connectionTypeLabels[connection.connection_type] }} · {{ connectionStatusLabels[connection.status] }}<span v-if="connection.cable_label"> · {{ connection.cable_label }}</span></v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <v-card-text v-else class="text-medium-emphasis">Noch keine Verbindung dokumentiert.</v-card-text>
      </v-card>

      <NotesCard target-type="asset" :target-id="device.asset_id" />
      <DocumentLinksCard target-type="asset" :target-id="device.asset_id" />
    </template>

    <v-dialog v-model="deviceDialog" max-width="680">
      <v-card title="Netzwerkprofil bearbeiten" prepend-icon="mdi-server-network">
        <v-card-text>
          <v-select v-model="deviceForm.role" :items="roleItems" label="Rolle" class="mb-3" />
          <v-text-field v-model="deviceForm.hostname" label="Hostname" :error-messages="hostnameError ? [hostnameError] : []" class="mb-1" />
          <v-btn v-if="hostnameError && hostnameSuggestion !== deviceForm.hostname" size="small" variant="text" prepend-icon="mdi-auto-fix" class="mb-3" @click="applyHostnameSuggestion">Vorschlag übernehmen: {{ hostnameSuggestion }}</v-btn>
          <v-text-field v-model="deviceForm.management_url" label="Management-URL" class="mb-3" />
          <v-textarea v-model="deviceForm.notes" label="Netzwerknotizen" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="deviceDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveDevice">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="interfaceDialog" max-width="720">
      <v-card :title="editingInterface ? 'Schnittstelle bearbeiten' : 'Schnittstelle anlegen'" prepend-icon="mdi-ethernet">
        <v-card-text>
          <v-row><v-col cols="12" sm="7"><v-text-field v-model="interfaceForm.name" label="Name / Port" placeholder="eth0, LAN 1, Port 24 …" /></v-col><v-col cols="12" sm="5"><v-select v-model="interfaceForm.interface_type" :items="interfaceTypeItems" label="Typ" /></v-col></v-row>
          <v-select
            v-if="interfaceForm.interface_type !== 'virtual'"
            v-model="interfaceForm.logical_interface_id"
            :items="logicalInterfaceItems"
            label="Mitglied einer logischen Schnittstelle / Bridge (optional)"
            hint="Zum Beispiel LAN 1–4 als Mitglieder der LAN-Bridge. Die Geräte-IP wird an der Bridge gepflegt."
            persistent-hint
            clearable
            class="mb-3"
          />
          <v-row><v-col cols="12" sm="7"><v-text-field v-model="interfaceForm.mac_address" label="MAC-Adresse" placeholder="AA:BB:CC:DD:EE:FF" /></v-col><v-col cols="12" sm="5"><v-select v-model="interfaceForm.speed_mbps" :items="speedItems" label="Geschwindigkeit" clearable /></v-col></v-row>
          <v-select v-model="interfaceForm.poe_mode" :items="poeItems" label="PoE" class="mb-3" />
          <v-switch v-model="interfaceForm.enabled" color="primary" label="Schnittstelle aktiv" />
          <v-switch v-model="interfaceForm.is_primary" color="primary" label="Primäre Schnittstelle dieses Geräts" hint="Nur eine Schnittstelle je Gerät kann primär sein." persistent-hint />
          <v-textarea v-model="interfaceForm.description" label="Beschreibung" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="interfaceDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!interfaceForm.name" @click="saveInterface">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="addressDialog" max-width="680">
      <v-card :title="editingAddress ? 'IP-Adresse bearbeiten' : 'IP-Adresse anlegen'" prepend-icon="mdi-ip-outline">
        <v-card-text>
          <v-text-field v-model="addressForm.address" label="IP-Adresse" placeholder="192.168.10.20" class="mb-3" />
          <v-select v-model="addressForm.segment_id" :items="segmentItems" label="IP-Netz (optional)" clearable class="mb-3" />
          <v-select v-model="addressForm.assignment_type" :items="assignmentItems" label="Vergabe" class="mb-3" />
          <v-text-field v-model="addressForm.hostname" label="Hostname für diese Adresse" class="mb-3" />
          <v-switch v-model="addressForm.is_primary" color="primary" label="Primäre Adresse dieses Geräts" />
          <v-textarea v-model="addressForm.notes" label="Notizen" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="addressDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!addressForm.address" @click="saveAddress">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="portDialog" max-width="820">
      <v-card title="Switch-Ports sicher erzeugen" prepend-icon="mdi-ethernet-cable">
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            Bestehende Ports bleiben erhalten; es werden ausschließlich fehlende Namen ergänzt.
          </v-alert>
          <v-row v-for="(group, index) in portGroups" :key="index">
            <v-col cols="12" sm="3"><v-select v-model="group.group" label="Gruppe" :items="[{title:'Kupfer',value:'copper'},{title:'SFP',value:'sfp'},{title:'SFP+',value:'sfp_plus'},{title:'Uplink',value:'uplink'}]" /></v-col>
            <v-col cols="6" sm="2"><v-text-field v-model.number="group.count" type="number" min="0" max="256" label="Anzahl" /></v-col>
            <v-col cols="6" sm="3"><v-select v-model="group.scheme" label="Schema" :items="[{title:'1–N',value:'numeric'},{title:'Gi1/0/N',value:'gigabit'},{title:'ethN',value:'ethernet'}]" /></v-col>
            <v-col cols="6" sm="2"><v-text-field v-model.number="group.speed_mbps" type="number" label="Mbit/s" /></v-col>
            <v-col cols="6" sm="2"><v-checkbox v-model="group.poe_capable" label="PoE" /></v-col>
          </v-row>
          <v-btn variant="text" prepend-icon="mdi-plus" @click="portGroups.push({ group: 'sfp', count: 2, scheme: 'numeric', start: 1, speed_mbps: 10000, poe_capable: false })">Gruppe</v-btn>
          <v-sheet v-if="portPreview" border rounded class="pa-3 mt-3">
            <strong>{{ portPreview.create_names.length }} neue Ports</strong>
            <p class="mb-0">{{ portPreview.create_names.join(', ') || 'Keine Ergänzung erforderlich.' }}</p>
          </v-sheet>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="portDialog = false">Schließen</v-btn><v-btn :loading="saving" @click="previewPorts">Vorschau</v-btn><v-btn color="primary" :loading="saving" :disabled="!portPreview?.create_names.length" @click="generatePorts">Erzeugen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="pathDialog" max-width="700">
      <v-card title="Dokumentierter Verbindungspfad" prepend-icon="mdi-map-marker-path">
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">Dies ist der in DocOfHome dokumentierte Pfad, kein IP-Traceroute.</v-alert>
          <v-timeline side="end" density="compact">
            <v-timeline-item v-for="node in documentedPath?.nodes ?? []" :key="node.device_id" dot-color="primary">
              <strong>{{ node.name }}</strong><div class="text-medium-emphasis">{{ node.role }}</div>
            </v-timeline-item>
          </v-timeline>
          <v-alert v-for="warning in documentedPath?.warnings ?? []" :key="warning" type="warning" variant="tonal" class="mt-2">{{ warning }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="pathDialog = false">Schließen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
code { color: rgb(var(--v-theme-primary)); }
.text-pre-wrap { white-space: pre-wrap; }
.switch-front-scroll { overflow-x: auto; padding-bottom: 6px; }
.switch-front { display: inline-grid; grid-template-columns: max-content max-content; grid-template-rows: repeat(2, 48px); gap: 10px 16px; min-width: max-content; padding: 16px; border: 4px solid rgba(var(--v-theme-on-surface), .35); border-radius: 12px; background: rgba(var(--v-theme-on-surface), .05); }
.switch-port-row { display: flex; gap: 10px; min-height: 48px; grid-column: 1; }
.switch-port-row:first-child { grid-row: 1; }
.switch-port-row:nth-child(2) { grid-row: 2; }
.switch-uplink-block { grid-column: 2; grid-row: 1 / span 2; display: grid; grid-template-columns: repeat(2, 76px); gap: 10px; border-left: 2px solid rgba(var(--v-theme-on-surface), .25); padding-left: 16px; }
.switch-port { width: 76px; min-height: 48px; border: 2px solid rgb(var(--v-theme-primary)); border-radius: 5px; background: rgb(var(--v-theme-surface)); color: rgb(var(--v-theme-on-surface)); cursor: default; font-size: .75rem; }
.switch-port.disabled { opacity: .45; border-style: dashed; }
.switch-port.uplink { border-color: rgb(var(--v-theme-secondary)); }
</style>

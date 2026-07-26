<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { networkApi } from '../services/networkApi'
import { releaseApi } from '../services/releaseApi'
import { useNotificationStore } from '../stores/notifications'
import type {
  NetworkConnection,
  NetworkConnectionStatus,
  NetworkConnectionType,
  NetworkDevice,
  NetworkDeviceCandidate,
  NetworkDeviceWrite,
  NetworkInterface,
  NetworkRole,
  NetworkSegment,
  NetworkSegmentWrite,
  NetworkSummary,
  NetworkTopology,
  NetworkTopologyEdge
} from '../types/network'
import { networkRoleIcons, networkRoleLabels } from '../types/network'
import type { FritzBoxDevice } from '../types/release'

const route = useRoute()
const router = useRouter()
const notifications = useNotificationStore()
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const devices = ref<NetworkDevice[]>([])
const candidates = ref<NetworkDeviceCandidate[]>([])
const segments = ref<NetworkSegment[]>([])
const interfaces = ref<NetworkInterface[]>([])
const connections = ref<NetworkConnection[]>([])
const fritzBoxDevices = ref<FritzBoxDevice[]>([])
const fritzBoxLoading = ref(false)
const fritzBoxError = ref<string | null>(null)
const fritzAssignDialog = ref(false)
const selectedFritzDevice = ref<FritzBoxDevice | null>(null)
const fritzTargetDeviceId = ref('')
const fritzTargetRole = ref<NetworkRole>('other')
const summary = ref<NetworkSummary | null>(null)
const topology = ref<NetworkTopology | null>(null)

watch(error, (message) => {
  if (message) notifications.error(message)
})
const search = ref('')
const roleFilter = ref<NetworkRole | ''>('')
const allowedTabs = new Set(['devices', 'segments', 'connections', 'topology', 'fritzbox'])
const requestedTab = typeof route.query.tab === 'string' ? route.query.tab : 'devices'
const tab = ref(allowedTabs.has(requestedTab) ? requestedTab : 'devices')

const deviceDialog = ref(false)
const editingDevice = ref<NetworkDevice | null>(null)
const deviceForm = ref<NetworkDeviceWrite>({
  asset_id: '', role: 'other', hostname: null, management_url: null, notes: null
})
const segmentDialog = ref(false)
const editingSegment = ref<NetworkSegment | null>(null)
const segmentDns = ref('')
const segmentForm = ref<NetworkSegmentWrite>({
  name: '', cidr: '', vlan_id: null, gateway: null, dns_servers: [], description: null
})
const connectionDialog = ref(false)
const editingConnection = ref<NetworkConnection | null>(null)
const connectionForm = ref({
  source_interface_id: '',
  target_interface_id: '',
  connection_type: 'physical' as NetworkConnectionType,
  status: 'active' as NetworkConnectionStatus,
  cable_type: '',
  cable_label: '',
  description: ''
})

const roleItems = Object.entries(networkRoleLabels).map(([value, title]) => ({
  value: value as NetworkRole, title
}))
const candidateItems = computed(() => candidates.value.map((item) => ({
  value: item.asset_id,
  title: `${item.name} · ${item.jarvis_code}`,
  subtitle: [item.asset_type, item.product_name, item.location_name].filter(Boolean).join(' · ')
})))
const fritzAssignmentItems = computed(() => [
  ...devices.value.map((item) => ({
    value: `device:${item.id}`,
    title: item.asset_name,
    subtitle: `${item.asset_code} · ${networkRoleLabels[item.role]} · Netzwerkgerät vorhanden`,
    candidate: false
  })),
  ...candidates.value.map((item) => ({
    value: `asset:${item.asset_id}`,
    title: item.name,
    subtitle: `${item.jarvis_code} · ${item.asset_type}${item.location_name ? ` · ${item.location_name}` : ''} · Netzwerkrolle wird angelegt`,
    candidate: true
  }))
])
const fritzTargetNeedsRole = computed(() => fritzTargetDeviceId.value.startsWith('asset:'))

const connectionTypeLabels: Record<NetworkConnectionType, string> = {
  physical: 'Physisch', logical: 'Logisch', wireless: 'WLAN/Funk'
}
const connectionStatusLabels: Record<NetworkConnectionStatus, string> = {
  active: 'Aktiv', planned: 'Geplant', inactive: 'Inaktiv'
}
const interfaceItems = computed(() => interfaces.value.map((item) => ({
  value: item.id,
  title: `${item.device_name} · ${item.name}`,
  subtitle: item.mac_address ?? item.interface_type
})))
const filteredDevices = computed(() => devices.value.filter((device) => {
  const query = search.value.trim().toLocaleLowerCase()
  const matchesRole = !roleFilter.value || device.role === roleFilter.value
  const haystack = [
    device.asset_name, device.asset_code, device.asset_type, device.product_name,
    device.location_name, device.hostname, networkRoleLabels[device.role], device.notes
  ].filter(Boolean).join(' ').toLocaleLowerCase()
  return matchesRole && (!query || haystack.includes(query))
}))
const deviceById = computed(() => new Map(devices.value.map((item) => [item.id, item])))
const normalizedMac = (value: string | null | undefined) => (value ?? '').replace(/[^0-9a-f]/gi, '').toUpperCase()
const interfaceByMac = computed(() => new Map(
  interfaces.value.filter((item) => item.mac_address).map((item) => [normalizedMac(item.mac_address), item])
))
const fritzRows = computed(() => fritzBoxDevices.value.map((item) => {
  const networkInterface = interfaceByMac.value.get(normalizedMac(item.mac_address)) ?? null
  const matchedDevice = networkInterface ? deviceById.value.get(networkInterface.network_device_id) ?? null : null
  return { ...item, networkInterface, matchedDevice }
}))
const fritzKnownCount = computed(() => fritzRows.value.filter((item) => item.matchedDevice).length)
const fritzOnlineCount = computed(() => fritzRows.value.filter((item) => item.active).length)
const edgesByDevice = computed(() => {
  const result = new Map<string, NetworkTopologyEdge[]>()
  for (const node of topology.value?.nodes ?? []) result.set(node.id, [])
  for (const edge of topology.value?.edges ?? []) {
    result.get(edge.source_device_id)?.push(edge)
    result.get(edge.target_device_id)?.push(edge)
  }
  return result
})

watch(tab, (value) => {
  void router.replace({ query: { ...route.query, tab: value } })
  if (value === 'fritzbox' && !fritzBoxLoading.value && fritzBoxDevices.value.length === 0) {
    void loadFritzBoxDevices()
  }
})

async function loadAll() {
  loading.value = true
  error.value = null
  const labels = [
    'Geräte', 'Gerätekandidaten', 'IP-Netze', 'Schnittstellen',
    'Verbindungen', 'Übersicht', 'Topologie'
  ]
  const results = await Promise.allSettled([
    networkApi.devices(), networkApi.candidates(), networkApi.segments(), networkApi.interfaces(),
    networkApi.connections(), networkApi.summary(), networkApi.topology()
  ])

  const [deviceData, candidateData, segmentData, interfaceData, connectionData, summaryData, topologyData] = results
  if (deviceData.status === 'fulfilled') devices.value = deviceData.value as NetworkDevice[]
  if (candidateData.status === 'fulfilled') candidates.value = candidateData.value as NetworkDeviceCandidate[]
  if (segmentData.status === 'fulfilled') segments.value = segmentData.value as NetworkSegment[]
  if (interfaceData.status === 'fulfilled') interfaces.value = interfaceData.value as NetworkInterface[]
  if (connectionData.status === 'fulfilled') connections.value = connectionData.value as NetworkConnection[]
  if (summaryData.status === 'fulfilled') summary.value = summaryData.value as NetworkSummary
  if (topologyData.status === 'fulfilled') topology.value = topologyData.value as NetworkTopology

  const failed = results.flatMap((result, index) => {
    if (result.status === 'fulfilled') return []
    const detail = result.reason instanceof Error ? result.reason.message : 'unbekannter Fehler'
    return [`${labels[index]}: ${detail}`]
  })
  if (failed.length) {
    error.value = `Ein Teil der Netzwerkdaten konnte nicht geladen werden. ${failed.join(' · ')}`
  }

  try {
    if (tab.value === 'fritzbox') await loadFritzBoxDevices()
  } finally {
    loading.value = false
  }
}

function openDevice(device?: NetworkDevice) {
  editingDevice.value = device ?? null
  deviceForm.value = device ? {
    asset_id: device.asset_id,
    role: device.role,
    hostname: device.hostname,
    management_url: device.management_url,
    notes: device.notes
  } : { asset_id: '', role: 'other', hostname: null, management_url: null, notes: null }
  deviceDialog.value = true
}

async function saveDevice() {
  if (!deviceForm.value.asset_id) return
  saving.value = true
  error.value = null
  try {
    if (editingDevice.value) await networkApi.updateDevice(editingDevice.value.id, deviceForm.value)
    else await networkApi.createDevice(deviceForm.value)
    deviceDialog.value = false
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkgerät konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeDevice(device: NetworkDevice) {
  if (!confirm(`Netzwerkrolle von „${device.asset_name}“ archivieren? Schnittstellen, IP-Adressen und Verbindungen werden ebenfalls archiviert. Das Asset bleibt erhalten.`)) return
  try {
    await networkApi.deleteDevice(device.id)
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netzwerkgerät konnte nicht archiviert werden.'
  }
}

function openSegment(segment?: NetworkSegment) {
  editingSegment.value = segment ?? null
  segmentForm.value = segment ? {
    name: segment.name,
    cidr: segment.cidr,
    vlan_id: segment.vlan_id,
    gateway: segment.gateway,
    dns_servers: [...segment.dns_servers],
    description: segment.description
  } : { name: '', cidr: '', vlan_id: null, gateway: null, dns_servers: [], description: null }
  segmentDns.value = segment?.dns_servers.join(', ') ?? ''
  segmentDialog.value = true
}

async function saveSegment() {
  const rawVlan = segmentForm.value.vlan_id as number | string | null
  segmentForm.value.vlan_id = rawVlan === null || rawVlan === '' ? null : Number(rawVlan)
  segmentForm.value.dns_servers = segmentDns.value.split(/[;,\s]+/).map((item) => item.trim()).filter(Boolean)
  saving.value = true
  error.value = null
  try {
    if (editingSegment.value) await networkApi.updateSegment(editingSegment.value.id, segmentForm.value)
    else await networkApi.createSegment(segmentForm.value)
    segmentDialog.value = false
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'IP-Netz konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeSegment(segment: NetworkSegment) {
  if (!confirm(`Netz „${segment.name}“ archivieren?`)) return
  try {
    await networkApi.deleteSegment(segment.id)
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Netz konnte nicht archiviert werden.'
  }
}

function openConnection(connection?: NetworkConnection) {
  editingConnection.value = connection ?? null
  connectionForm.value = connection ? {
    source_interface_id: connection.source_interface_id,
    target_interface_id: connection.target_interface_id,
    connection_type: connection.connection_type,
    status: connection.status,
    cable_type: connection.cable_type ?? '',
    cable_label: connection.cable_label ?? '',
    description: connection.description ?? ''
  } : {
    source_interface_id: '', target_interface_id: '', connection_type: 'physical', status: 'active',
    cable_type: '', cable_label: '', description: ''
  }
  connectionDialog.value = true
}

async function saveConnection() {
  if (!connectionForm.value.source_interface_id || !connectionForm.value.target_interface_id) return
  saving.value = true
  error.value = null
  const payload = {
    ...connectionForm.value,
    cable_type: connectionForm.value.cable_type.trim() || null,
    cable_label: connectionForm.value.cable_label.trim() || null,
    description: connectionForm.value.description.trim() || null
  }
  try {
    if (editingConnection.value) await networkApi.updateConnection(editingConnection.value.id, payload)
    else await networkApi.createConnection(payload)
    connectionDialog.value = false
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindung konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeConnection(connection: NetworkConnection) {
  if (!confirm('Netzwerkverbindung archivieren?')) return
  try {
    await networkApi.deleteConnection(connection.id)
    await loadAll()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindung konnte nicht archiviert werden.'
  }
}

async function loadFritzBoxDevices() {
  fritzBoxLoading.value = true
  fritzBoxError.value = null
  try {
    fritzBoxDevices.value = await releaseApi.fritzBoxDevices()
  } catch (reason) {
    fritzBoxDevices.value = []
    fritzBoxError.value = reason instanceof Error ? reason.message : 'FRITZ!Box-Geräte konnten nicht geladen werden.'
  } finally {
    fritzBoxLoading.value = false
  }
}

function openFritzAssignment(device: FritzBoxDevice) {
  selectedFritzDevice.value = device
  fritzTargetDeviceId.value = ''
  fritzTargetRole.value = 'other'
  fritzAssignDialog.value = true
}

function fritzInterfaceType(device: FritzBoxDevice): 'ethernet' | 'wifi' | 'other' {
  const value = (device.interface_type ?? device.connected_via ?? '').toLocaleLowerCase()
  if (value.includes('wlan') || value.includes('wifi') || value.includes('wireless')) return 'wifi'
  if (value.includes('ethernet') || value.includes('lan')) return 'ethernet'
  return 'other'
}

async function assignFritzDevice() {
  const discovered = selectedFritzDevice.value
  if (!discovered || !fritzTargetDeviceId.value || !discovered.mac_address) return
  saving.value = true
  error.value = null
  let createdDeviceId: string | null = null
  const createdInterfaceIds: string[] = []
  try {
    let targetDeviceId = fritzTargetDeviceId.value
    let targetRole: NetworkRole
    if (targetDeviceId.startsWith('asset:')) {
      targetRole = fritzTargetRole.value
      const createdDevice = await networkApi.createDevice({
        asset_id: targetDeviceId.slice('asset:'.length),
        role: targetRole,
        hostname: null,
        management_url: null,
        notes: 'Netzwerkrolle bei bestätigter Übernahme aus der FRITZ!Box-Geräteliste angelegt.'
      })
      targetDeviceId = createdDevice.id
      createdDeviceId = createdDevice.id
    } else if (targetDeviceId.startsWith('device:')) {
      targetDeviceId = targetDeviceId.slice('device:'.length)
      targetRole = devices.value.find((item) => item.id === targetDeviceId)?.role ?? 'other'
    } else {
      throw new Error('Bitte wähle ein gültiges DocOfHome-Objekt aus.')
    }

    let logicalInterfaceId: string | null = null
    if (discovered.ipv4) {
      const bridgeName = ['router', 'firewall', 'access_point'].includes(targetRole)
        ? 'LAN-Bridge'
        : 'Management'
      const logicalInterface = await networkApi.createInterface({
        network_device_id: targetDeviceId,
        name: bridgeName,
        interface_type: 'virtual',
        mac_address: null,
        speed_mbps: null,
        poe_mode: 'none',
        enabled: true,
        logical_interface_id: null,
        description: 'Logische Geräteschnittstelle für die gemeinsame Management-IP.'
      })
      logicalInterfaceId = logicalInterface.id
      createdInterfaceIds.push(logicalInterface.id)
    }

    const createdInterface = await networkApi.createInterface({
      network_device_id: targetDeviceId,
      name: `FRITZ ${normalizedMac(discovered.mac_address).slice(-6)}`,
      interface_type: fritzInterfaceType(discovered),
      mac_address: discovered.mac_address,
      speed_mbps: discovered.connection_rate_mbps,
      poe_mode: 'unknown',
      enabled: true,
      logical_interface_id: logicalInterfaceId,
      description: 'Physische bzw. drahtlose Schnittstelle aus der FRITZ!Box-Geräteliste. Manuelle Daten werden nicht überschrieben.'
    })
    createdInterfaceIds.push(createdInterface.id)
    if (discovered.ipv4 && logicalInterfaceId) {
      await networkApi.createAddress({
        interface_id: logicalInterfaceId,
        segment_id: null,
        address: discovered.ipv4,
        assignment_type: discovered.dhcp_reservation ? 'reservation' : 'dhcp',
        hostname: discovered.name || null,
        is_primary: true,
        notes: 'Geräte-IP aus der FRITZ!Box-Geräteliste; gilt für die logische Management-/LAN-Schnittstelle.'
      })
    }
    fritzAssignDialog.value = false
    await loadAll()
  } catch (reason) {
    for (const interfaceId of createdInterfaceIds.reverse()) {
      await networkApi.deleteInterface(interfaceId).catch(() => undefined)
    }
    if (createdDeviceId) {
      await networkApi.deleteDevice(createdDeviceId).catch(() => undefined)
    }
    error.value = reason instanceof Error ? reason.message : 'FRITZ!Box-Gerät konnte nicht zugeordnet werden.'
  } finally {
    saving.value = false
  }
}

function otherNode(edge: NetworkTopologyEdge, nodeId: string): string {
  const otherId = edge.source_device_id === nodeId ? edge.target_device_id : edge.source_device_id
  return deviceById.value.get(otherId)?.asset_name ?? 'Unbekanntes Gerät'
}

onMounted(() => void loadAll())
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div>
        <h1 class="text-h4">Netzwerk</h1>
        <p class="text-medium-emphasis mb-0">Geräte, Schnittstellen, IP-Netze und Verbindungen dokumentieren. VLANs können bei Bedarf optional ergänzt werden.</p>
      </div>
      <v-spacer />
      <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="loading" @click="loadAll">Aktualisieren</v-btn>
      <v-btn color="primary" prepend-icon="mdi-lan-connect" @click="openDevice()">Netzwerkgerät</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = null">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-row v-if="summary" class="mb-2">
      <v-col v-for="item in [
        ['Geräte', summary.device_count, 'mdi-server-network'],
        ['Netze', summary.segment_count, 'mdi-ip-network-outline'],
        ['Schnittstellen', summary.interface_count, 'mdi-ethernet'],
        ['IP-Adressen', summary.address_count, 'mdi-ip-outline'],
        ['Verbindungen', summary.connection_count, 'mdi-lan-connect']
      ]" :key="String(item[0])" cols="6" sm="4" lg="2">
        <v-card variant="tonal" class="h-100">
          <v-card-text class="d-flex align-center ga-3">
            <v-icon :icon="String(item[2])" size="32" />
            <div><div class="text-h5">{{ item[1] }}</div><div class="text-caption">{{ item[0] }}</div></div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" lg="2">
        <v-card :color="summary.device_without_connection_count ? 'warning' : undefined" variant="tonal" class="h-100">
          <v-card-text class="d-flex align-center ga-3">
            <v-icon icon="mdi-lan-disconnect" size="32" />
            <div><div class="text-h5">{{ summary.device_without_connection_count }}</div><div class="text-caption">Geräte ohne Verbindung</div><div class="text-caption text-medium-emphasis">{{ summary.free_interface_count }} freie Ports sind normal</div></div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="devices" prepend-icon="mdi-server-network">Geräte</v-tab>
      <v-tab value="segments" prepend-icon="mdi-ip-network-outline">IP-Netze</v-tab>
      <v-tab value="connections" prepend-icon="mdi-lan-connect">Verbindungen</v-tab>
      <v-tab value="topology" prepend-icon="mdi-vector-polyline">Topologie</v-tab>
      <v-tab value="fritzbox" prepend-icon="mdi-router-wireless">FRITZ!Box</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="devices">
        <v-card class="mb-4">
          <v-card-text class="d-flex flex-wrap ga-3">
            <v-text-field v-model="search" label="Geräte durchsuchen" prepend-inner-icon="mdi-magnify" hide-details clearable class="flex-grow-1" />
            <v-select v-model="roleFilter" :items="[{ value: '', title: 'Alle Rollen' }, ...roleItems]" label="Rolle" hide-details clearable min-width="220" />
          </v-card-text>
        </v-card>
        <v-row v-if="filteredDevices.length">
          <v-col v-for="device in filteredDevices" :key="device.id" cols="12" md="6" xl="4">
            <v-card class="h-100" :to="`/network/devices/${device.id}`">
              <v-card-title class="d-flex align-center ga-2">
                <v-icon :icon="networkRoleIcons[device.role]" />
                <span class="text-truncate">{{ device.asset_name }}</span>
              </v-card-title>
              <v-card-subtitle>{{ networkRoleLabels[device.role] }} · {{ device.asset_code }}</v-card-subtitle>
              <v-card-text>
                <div class="d-flex flex-wrap ga-2 mb-3">
                  <v-chip v-if="device.hostname" size="small" prepend-icon="mdi-console-network-outline">{{ device.hostname }}</v-chip>
                  <v-chip v-if="device.location_name" size="small" prepend-icon="mdi-map-marker-outline">{{ device.location_name }}</v-chip>
                </div>
                <div class="d-flex ga-4 text-caption text-medium-emphasis">
                  <span><v-icon icon="mdi-ethernet" size="small" /> {{ device.interface_count }}</span>
                  <span><v-icon icon="mdi-ip-outline" size="small" /> {{ device.address_count }}</span>
                  <span><v-icon icon="mdi-lan-connect" size="small" /> {{ device.connection_count }}</span>
                </div>
              </v-card-text>
              <v-card-actions @click.stop.prevent>
                <v-btn variant="text" prepend-icon="mdi-pencil" @click="openDevice(device)">Bearbeiten</v-btn>
                <v-spacer />
                <v-btn icon="mdi-archive-outline" color="warning" variant="text" aria-label="Netzwerkgerät archivieren" @click="removeDevice(device)" />
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        <v-empty-state v-else icon="mdi-server-network-off" title="Keine Netzwerkgeräte" text="Lege aus einem vorhandenen Asset eine Netzwerkrolle an." />
      </v-window-item>

      <v-window-item value="segments">
        <div class="d-flex justify-end mb-3"><v-btn color="primary" prepend-icon="mdi-plus" @click="openSegment()">IP-Netz anlegen</v-btn></div>
        <v-card>
          <v-table>
            <thead><tr><th>Name</th><th>Netz</th><th>VLAN (optional)</th><th>Gateway</th><th>Adressen</th><th class="text-right">Aktionen</th></tr></thead>
            <tbody>
              <tr v-for="segment in segments" :key="segment.id" :class="{ 'bg-primary-lighten-5': route.query.segment === segment.id }">
                <td><strong>{{ segment.name }}</strong><div class="text-caption text-medium-emphasis">{{ segment.description }}</div></td>
                <td><code>{{ segment.cidr }}</code></td><td>{{ segment.vlan_id ?? '–' }}</td><td>{{ segment.gateway ?? '–' }}</td><td>{{ segment.address_count }}</td>
                <td class="text-right"><v-btn icon="mdi-pencil" variant="text" @click="openSegment(segment)" /><v-btn icon="mdi-archive-outline" color="warning" variant="text" @click="removeSegment(segment)" /></td>
              </tr>
            </tbody>
          </v-table>
          <v-empty-state v-if="!segments.length" icon="mdi-ip-network-outline" title="Noch keine Netze" text="Dokumentiere Subnetze und optionale VLAN-IDs." />
        </v-card>
      </v-window-item>

      <v-window-item value="connections">
        <div class="d-flex justify-end mb-3"><v-btn color="primary" prepend-icon="mdi-link-plus" :disabled="interfaces.length < 2" @click="openConnection()">Verbindung</v-btn></div>
        <v-card>
          <v-list v-if="connections.length" lines="three">
            <v-list-item v-for="connection in connections" :key="connection.id" prepend-icon="mdi-lan-connect">
              <v-list-item-title>{{ connection.source_device_name }} · {{ connection.source_interface_name }} ↔ {{ connection.target_device_name }} · {{ connection.target_interface_name }}</v-list-item-title>
              <v-list-item-subtitle>{{ connectionTypeLabels[connection.connection_type] }} · {{ connectionStatusLabels[connection.status] }}<span v-if="connection.cable_label"> · {{ connection.cable_label }}</span><span v-if="connection.cable_type"> · {{ connection.cable_type }}</span></v-list-item-subtitle>
              <template #append><v-btn icon="mdi-pencil" variant="text" @click="openConnection(connection)" /><v-btn icon="mdi-archive-outline" color="warning" variant="text" @click="removeConnection(connection)" /></template>
            </v-list-item>
          </v-list>
          <v-empty-state v-else icon="mdi-lan-disconnect" title="Noch keine Verbindungen" text="Erfasse zuerst mindestens zwei Schnittstellen an Netzwerkgeräten." />
        </v-card>
      </v-window-item>

      <v-window-item value="topology">
        <v-alert type="info" variant="tonal" class="mb-4">Die Topologie zeigt dokumentierte Verbindungen. Es findet keine automatische Netzwerkerkennung statt.</v-alert>
        <v-row v-if="topology?.nodes.length">
          <v-col v-for="node in topology.nodes" :key="node.id" cols="12" md="6" xl="4">
            <v-card :to="`/network/devices/${node.id}`" class="h-100">
              <v-card-title><v-icon :icon="networkRoleIcons[node.role]" class="mr-2" />{{ node.name }}</v-card-title>
              <v-card-subtitle>{{ node.hostname ?? networkRoleLabels[node.role] }}<span v-if="node.location_name"> · {{ node.location_name }}</span></v-card-subtitle>
              <v-card-text>
                <div v-if="edgesByDevice.get(node.id)?.length" class="d-flex flex-column ga-2">
                  <v-chip v-for="edge in edgesByDevice.get(node.id)" :key="edge.id" prepend-icon="mdi-lan-connect" variant="outlined">
                    {{ otherNode(edge, node.id) }} · {{ edge.source_device_id === node.id ? edge.source_label : edge.target_label }}
                  </v-chip>
                </div>
                <span v-else class="text-medium-emphasis">Keine dokumentierte Verbindung</span>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        <v-empty-state v-else icon="mdi-vector-polyline" title="Topologie ist leer" text="Lege Geräte, Schnittstellen und Verbindungen an." />
      </v-window-item>

      <v-window-item value="fritzbox">
        <v-card>
          <v-card-title class="d-flex flex-wrap align-center ga-2">
            <v-icon icon="mdi-router-wireless" />
            <span>Von der FRITZ!Box erkannte Geräte</span>
            <v-spacer />
            <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="fritzBoxLoading" @click="loadFritzBoxDevices">Neu einlesen</v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              Die Liste wird live und ausschließlich lesend über TR-064 geladen. Ein Gerät gilt als bekannt,
              wenn seine MAC-Adresse bereits an einer DocOfHome-Netzwerkschnittstelle hinterlegt ist.
            </v-alert>
            <v-alert v-if="fritzBoxError" type="warning" variant="tonal" class="mb-4">{{ fritzBoxError }}</v-alert>
            <div v-if="fritzRows.length" class="d-flex flex-wrap ga-2 mb-4">
              <v-chip color="success" variant="tonal">{{ fritzOnlineCount }} online</v-chip>
              <v-chip color="primary" variant="tonal">{{ fritzKnownCount }} zugeordnet</v-chip>
              <v-chip variant="tonal">{{ fritzRows.length - fritzKnownCount }} noch unbekannt</v-chip>
            </div>
            <v-table v-if="fritzRows.length" density="comfortable">
              <thead>
                <tr><th>Status</th><th>Gerät</th><th>Adresse</th><th>Verbindung</th><th>DocOfHome-Bezug</th><th class="text-right">Aktion</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in fritzRows" :key="item.mac_address ?? `${item.name}-${item.ipv4}`">
                  <td><v-chip size="small" :color="item.active ? 'success' : undefined" variant="tonal">{{ item.active ? 'Online' : 'Offline' }}</v-chip></td>
                  <td><strong>{{ item.name }}</strong><div class="text-caption text-medium-emphasis">{{ item.mac_address || 'Keine MAC-Adresse' }}</div></td>
                  <td><code>{{ item.ipv4 || item.ipv6 || '–' }}</code><div v-if="item.dhcp_reservation" class="text-caption">Feste DHCP-Zuordnung</div></td>
                  <td>{{ item.interface_type || 'Unbekannt' }}<div class="text-caption text-medium-emphasis">{{ item.connected_via || '–' }}<span v-if="item.connection_rate_mbps"> · {{ item.connection_rate_mbps }} Mbit/s</span></div></td>
                  <td>
                    <v-chip v-if="item.matchedDevice" color="success" variant="tonal" size="small" prepend-icon="mdi-link-variant">{{ item.matchedDevice.asset_name }}</v-chip>
                    <v-chip v-else color="warning" variant="tonal" size="small">Noch nicht zugeordnet</v-chip>
                  </td>
                  <td class="text-right">
                    <v-btn v-if="item.matchedDevice" variant="text" prepend-icon="mdi-open-in-new" :to="`/network/devices/${item.matchedDevice.id}`">Öffnen</v-btn>
                    <template v-else>
                      <v-btn variant="text" prepend-icon="mdi-link-plus" :disabled="!item.mac_address" @click="openFritzAssignment(item)">Zuordnen</v-btn>
                      <v-btn variant="text" prepend-icon="mdi-plus" :to="{ path: '/assets/new', query: { name: item.name, description: `Von der FRITZ!Box erkannt: ${item.mac_address || ''} ${item.ipv4 || ''}`, return_to: '/network?tab=fritzbox' } }">Asset anlegen</v-btn>
                    </template>
                  </td>
                </tr>
              </tbody>
            </v-table>
            <v-empty-state v-else-if="!fritzBoxLoading && !fritzBoxError" icon="mdi-router-wireless" title="Keine Geräte gemeldet" text="Die FRITZ!Box hat aktuell keine Hosteinträge geliefert." />
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>

    <v-dialog v-model="fritzAssignDialog" max-width="680">
      <v-card title="FRITZ!Box-Gerät zuordnen" prepend-icon="mdi-link-plus">
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            Es wird eine neue Schnittstelle mit MAC-Adresse und optional eine primäre DHCP-Adresse angelegt.
            Vorhandene manuelle Daten werden nicht überschrieben.
          </v-alert>
          <v-text-field :model-value="selectedFritzDevice?.name" label="Erkanntes Gerät" disabled />
          <v-text-field :model-value="selectedFritzDevice?.mac_address" label="MAC-Adresse" disabled />
          <v-autocomplete
            v-model="fritzTargetDeviceId"
            :items="fritzAssignmentItems"
            item-title="title"
            item-value="value"
            label="Vorhandenes Asset oder Netzwerkgerät"
            hint="Assets ohne Netzwerkrolle können hier direkt als Netzwerkgerät übernommen werden."
            persistent-hint
            class="mb-3"
          >
            <template #item="{ props, item }">
              <v-list-item v-bind="props" :title="item.raw.title" :subtitle="item.raw.subtitle" />
            </template>
          </v-autocomplete>
          <v-select
            v-if="fritzTargetNeedsRole"
            v-model="fritzTargetRole"
            :items="roleItems"
            label="Netzwerkrolle für das Asset"
          />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="fritzAssignDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!fritzTargetDeviceId" @click="assignFritzDevice">Zuordnen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deviceDialog" max-width="680">
      <v-card :title="editingDevice ? 'Netzwerkgerät bearbeiten' : 'Netzwerkgerät anlegen'" prepend-icon="mdi-server-network">
        <v-card-text>
          <v-text-field v-if="editingDevice" :model-value="editingDevice.asset_name" label="Asset" disabled class="mb-3" />
          <v-select v-else v-model="deviceForm.asset_id" :items="candidateItems" item-title="title" item-value="value" label="Asset" hint="Nur Assets ohne aktive Netzwerkrolle werden angeboten." persistent-hint class="mb-3" />
          <v-select v-model="deviceForm.role" :items="roleItems" label="Rolle" class="mb-3" />
          <v-text-field v-model="deviceForm.hostname" label="Hostname" prepend-inner-icon="mdi-console-network-outline" class="mb-3" />
          <v-text-field v-model="deviceForm.management_url" label="Management-URL" placeholder="https://switch.example.test" prepend-inner-icon="mdi-web" class="mb-3" />
          <v-textarea v-model="deviceForm.notes" label="Netzwerknotizen" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="deviceDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!deviceForm.asset_id" @click="saveDevice">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="segmentDialog" max-width="680">
      <v-card :title="editingSegment ? 'IP-Netz bearbeiten' : 'IP-Netz anlegen'" prepend-icon="mdi-ip-network-outline">
        <v-card-text>
          <v-row><v-col cols="12" sm="8"><v-text-field v-model="segmentForm.name" label="Name" /></v-col><v-col cols="12" sm="4"><v-text-field v-model.number="segmentForm.vlan_id" type="number" min="1" max="4094" label="VLAN-ID (optional)" hint="Leer lassen, wenn zuhause keine VLANs verwendet werden." persistent-hint clearable /></v-col></v-row>
          <v-text-field v-model="segmentForm.cidr" label="Netz/CIDR" placeholder="192.168.10.0/24" class="mb-3" />
          <v-text-field v-model="segmentForm.gateway" label="Gateway" placeholder="192.168.10.1" class="mb-3" />
          <v-text-field v-model="segmentDns" label="DNS-Server" hint="Mehrere Adressen mit Komma trennen" persistent-hint class="mb-3" />
          <v-textarea v-model="segmentForm.description" label="Beschreibung" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="segmentDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!segmentForm.name || !segmentForm.cidr" @click="saveSegment">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="connectionDialog" max-width="760">
      <v-card :title="editingConnection ? 'Verbindung bearbeiten' : 'Verbindung anlegen'" prepend-icon="mdi-lan-connect">
        <v-card-text>
          <v-select v-model="connectionForm.source_interface_id" :items="interfaceItems" label="Schnittstelle A" class="mb-3" />
          <v-select v-model="connectionForm.target_interface_id" :items="interfaceItems.filter((item) => item.value !== connectionForm.source_interface_id)" label="Schnittstelle B" class="mb-3" />
          <v-row><v-col cols="12" sm="6"><v-select v-model="connectionForm.connection_type" :items="[{value:'physical',title:'Physisch'},{value:'logical',title:'Logisch'},{value:'wireless',title:'WLAN/Funk'}]" label="Verbindungsart" /></v-col><v-col cols="12" sm="6"><v-select v-model="connectionForm.status" :items="[{value:'active',title:'Aktiv'},{value:'planned',title:'Geplant'},{value:'inactive',title:'Inaktiv'}]" label="Status" /></v-col></v-row>
          <v-row><v-col cols="12" sm="6"><v-text-field v-model="connectionForm.cable_type" label="Kabeltyp" placeholder="Cat 6A, OM4 …" /></v-col><v-col cols="12" sm="6"><v-text-field v-model="connectionForm.cable_label" label="Kabel-/Dosenkennung" /></v-col></v-row>
          <v-textarea v-model="connectionForm.description" label="Beschreibung" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="connectionDialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!connectionForm.source_interface_id || !connectionForm.target_interface_id" @click="saveConnection">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
code { color: rgb(var(--v-theme-primary)); }
</style>

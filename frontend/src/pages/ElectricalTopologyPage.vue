<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import PhaseSupplyPathsCard from '../components/PhaseSupplyPathsCard.vue'
import { electricalApi, loadAllConnectionEndpoints } from '../services/electricalApi'
import {
  endpointKindIcons,
  endpointKindLabels,
  endpointTitle,
  electricalPhaseColors,
  phaseDistributionGroups,
  phaseConnectionCounts,
  topologyRows
} from '../services/electricalTopology'
import { createEmptyElectricalConnection } from '../types/electrical'
import type {
  ElectricalConnection,
  ElectricalConnectionType,
  ElectricalConnectionWrite,
  ElectricalEndpoint,
  ElectricalPhase,
  ElectricalTopology
} from '../types/electrical'

const topology = ref<ElectricalTopology>({ nodes: [], connections: [], measurement_points: [] })
const route = useRoute()
const endpoints = ref<ElectricalEndpoint[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const dialogError = ref<string | null>(null)
const success = ref<string | null>(null)
const dialogOpen = ref(false)
const editingConnection = ref<ElectricalConnection | null>(null)
const sourceKey = ref('')
const targetKey = ref('')
const form = ref<ElectricalConnectionWrite>(createEmptyElectricalConnection())
const highlightedKey = ref<string | null>(null)

const connectionTypeItems: Array<{ title: string; value: ElectricalConnectionType }> = [
  { title: 'Noch nicht genauer dokumentiert', value: 'unknown' },
  { title: 'Kabel', value: 'cable' },
  { title: 'Einzelader / Draht', value: 'wire' },
  { title: 'Sammelschiene / Phasenschiene', value: 'busbar' },
  { title: 'Interne Geräteverbindung', value: 'internal' }
]
const phaseItems: Array<{ title: string; value: ElectricalPhase }> = [
  { title: 'L1', value: 'L1' },
  { title: 'L2', value: 'L2' },
  { title: 'L3', value: 'L3' },
  { title: 'Neutralleiter N', value: 'N' },
  { title: 'Schutzleiter PE', value: 'PE' }
]
const rows = computed(() => topologyRows(topology.value))
const phaseCounts = computed(() => phaseConnectionCounts(topology.value))
const phaseBlocks = computed(() => phaseDistributionGroups(topology.value))
const endpointItems = computed(() => endpoints.value.map((endpoint) => ({
  title: endpointTitle(endpoint),
  value: endpoint.key,
  endpoint
})))
const sourceItems = computed(() => endpointItems.value.filter(
  (item) => item.value !== targetKey.value
))
const targetItems = computed(() => endpointItems.value.filter(
  (item) => item.value !== sourceKey.value && item.endpoint.kind !== 'grid_connection'
))
const rcdNodes = computed(() => topology.value.nodes.filter(
  (node) => node.endpoint.device_type === 'rcd'
))
const rootCount = computed(() => rows.value.filter((row) => row.depth === 0).length)
const showCableDetails = computed(() => (
  form.value.connection_type === 'cable' || form.value.connection_type === 'wire'
))
const linePhases: ElectricalPhase[] = ['L1', 'L2', 'L3']
const selectedConnectionEndpoints = computed(() => [
  endpointByKey(sourceKey.value),
  endpointByKey(targetKey.value)
].filter((endpoint): endpoint is ElectricalEndpoint => Boolean(endpoint)))
const protectivePhaseRequirements = computed(() => selectedConnectionEndpoints.value
  .filter((endpoint) => endpoint.kind === 'protective_device')
  .map((endpoint) => (endpoint.effective_phases ?? []).filter(
    (phase): phase is ElectricalPhase => linePhases.includes(phase)
  ))
  .filter((phases) => phases.length > 0))
const forcedLinePhases = computed<ElectricalPhase[]>(() => (
  protectivePhaseRequirements.value[0] ?? []
))
const forcedPhaseConflict = computed(() => {
  if (protectivePhaseRequirements.value.length < 2) return false
  const expected = forcedLinePhases.value.join('|')
  return protectivePhaseRequirements.value.some((phases) => phases.join('|') !== expected)
})
const connectionPhaseItems = computed(() => phaseItems.map((item) => ({
  ...item,
  props: {
    disabled: forcedLinePhases.value.length > 0 && linePhases.includes(item.value)
  }
})))
const forcedPhaseHint = computed(() => {
  if (forcedPhaseConflict.value) {
    return 'Die ausgewählten Schutzgeräte besitzen widersprüchliche wirksame Phasen.'
  }
  if (!forcedLinePhases.value.length) return null
  return `Durch Sammel-/Phasenschiene fest vorgegeben: ${forcedLinePhases.value.join(', ')}`
})

function optionalText(value: string | null): string | null {
  return value?.trim() || null
}

function endpointByKey(key: string): ElectricalEndpoint | undefined {
  return endpoints.value.find((endpoint) => endpoint.key === key)
}

function enforceCalculatedLinePhases(): void {
  if (!forcedLinePhases.value.length) return
  const preserved = form.value.phases.filter((phase) => !linePhases.includes(phase))
  form.value.phases = [...forcedLinePhases.value, ...preserved]
}

function updateConnectionPhases(value: ElectricalPhase[]): void {
  if (!forcedLinePhases.value.length) {
    form.value.phases = value
    return
  }
  const preserved = value.filter((phase) => !linePhases.includes(phase))
  form.value.phases = [...forcedLinePhases.value, ...preserved]
}

function endpointRoute(endpoint: ElectricalEndpoint): string | null {
  if (endpoint.kind === 'asset') {
    return `/assets/${endpoint.id}${endpoint.deleted_at ? '?archived=1' : ''}`
  }
  if (endpoint.kind === 'distribution') return `/electrical/distributions/${endpoint.id}`
  if (endpoint.kind === 'protective_device') {
    return `/electrical/protective-devices/${endpoint.id}/edit`
  }
  if (endpoint.kind === 'circuit') return `/electrical/circuits/${endpoint.id}`
  return null
}

function displayPhases(connection: ElectricalConnection): ElectricalPhase[] {
  return connection.effective_phases.length ? connection.effective_phases : connection.phases
}

function phaseColor(phase: ElectricalPhase): string {
  return electricalPhaseColors[phase]
}

function connectionTypeName(connectionType: ElectricalConnectionType): string {
  return connectionTypeItems.find((item) => item.value === connectionType)?.title
    ?? connectionType
}

function connectionDetails(connection: ElectricalConnection): string {
  return [
    connection.label,
    connectionTypeName(connection.connection_type),
    connection.cable_type,
    connection.cores ? `${connection.cores} Adern` : null,
    connection.cross_section_mm2 ? `${connection.cross_section_mm2} mm²` : null,
    connection.length_m ? `${connection.length_m} m` : null
  ].filter(Boolean).join(' · ')
}

function measurementPointsForConnection(connectionId: string) {
  return (topology.value.measurement_points ?? []).filter(
    (point) => point.connection_id === connectionId
  )
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [topologyResult, endpointResult] = await Promise.all([
      electricalApi.topology(),
      loadAllConnectionEndpoints()
    ])
    topology.value = topologyResult
    endpoints.value = endpointResult
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Versorgungstopologie konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function openCreate(preselectedTarget = '') {
  dialogError.value = null
  editingConnection.value = null
  sourceKey.value = ''
  targetKey.value = preselectedTarget
  form.value = createEmptyElectricalConnection()
  dialogOpen.value = true
}

async function focusEndpoint(key: string) {
  highlightedKey.value = key
  await nextTick()
  const layout = window.matchMedia('(min-width: 960px)').matches ? 'desktop' : 'mobile'
  document.getElementById(`topology-${layout}-${key}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  })
}

async function initialize() {
  await load()
  const requestedTarget = typeof route.query.target === 'string' ? route.query.target : ''
  const requestedFocus = typeof route.query.focus === 'string' ? route.query.focus : ''
  if (
    route.query.connect === '1'
    && requestedTarget
    && endpointByKey(requestedTarget)
  ) {
    openCreate(requestedTarget)
    return
  }
  const focus = requestedFocus || requestedTarget
  if (focus) await focusEndpoint(focus)
}

function openEdit(connection: ElectricalConnection) {
  dialogError.value = null
  editingConnection.value = connection
  sourceKey.value = connection.source.key
  targetKey.value = connection.target.key
  form.value = {
    source_kind: connection.source.kind,
    source_id: connection.source.id,
    target_kind: connection.target.kind,
    target_id: connection.target.id,
    connection_type: connection.connection_type,
    label: connection.label,
    phases: [...connection.phases],
    cable_type: connection.cable_type,
    cores: connection.cores,
    cross_section_mm2: connection.cross_section_mm2,
    length_m: connection.length_m,
    route: connection.route,
    notes: connection.notes
  }
  enforceCalculatedLinePhases()
  dialogOpen.value = true
}

async function saveConnection() {
  const source = endpointByKey(sourceKey.value)
  const target = endpointByKey(targetKey.value)
  if (!source || !target) {
    dialogError.value = 'Bitte Quelle und versorgtes Ziel auswählen.'
    return
  }
  saving.value = true
  dialogError.value = null
  try {
    const payload: ElectricalConnectionWrite = {
      ...form.value,
      source_kind: source.kind,
      source_id: source.id,
      target_kind: target.kind,
      target_id: target.id,
      label: optionalText(form.value.label),
      cable_type: showCableDetails.value ? optionalText(form.value.cable_type) : null,
      cores: showCableDetails.value ? form.value.cores : null,
      cross_section_mm2: showCableDetails.value ? form.value.cross_section_mm2 : null,
      length_m: showCableDetails.value ? form.value.length_m : null,
      route: optionalText(form.value.route),
      notes: optionalText(form.value.notes)
    }
    if (editingConnection.value) {
      await electricalApi.updateConnection(editingConnection.value.id, payload)
    } else {
      await electricalApi.createConnection(payload)
    }
    dialogOpen.value = false
    success.value = 'Versorgungsverbindung wurde gespeichert.'
    await load()
  } catch (reason) {
    dialogError.value = reason instanceof Error
      ? reason.message
      : 'Versorgungsverbindung konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function removeConnection(connection: ElectricalConnection) {
  if (!window.confirm(
    `Verbindung von „${connection.source.name}“ zu „${connection.target.name}“ entfernen?`
  )) return
  error.value = null
  try {
    await electricalApi.removeConnection(connection.id)
    success.value = 'Versorgungsverbindung wurde historisch entfernt.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Versorgungsverbindung konnte nicht entfernt werden.'
  }
}

watch([sourceKey, targetKey], () => {
  dialogError.value = null
  enforceCalculatedLinePhases()
})

onMounted(() => void initialize())
</script>

<template>
  <v-container class="topology-page pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/electrical" class="mb-3">
      Zur Elektroübersicht
    </v-btn>
    <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
      <div>
        <h1>Versorgungswege</h1>
        <p class="text-medium-emphasis mb-0">
          Vom Hausanschluss über Zähler und Schutzgeräte bis zum Endgerät.
        </p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-connection" @click="openCreate()">
        Verbindung anlegen
      </v-btn>
    </div>

    <v-alert type="info" variant="tonal" icon="mdi-source-branch" class="mb-5" title="So funktioniert die Topologie">
      Jede Verbindung bedeutet „Quelle versorgt Ziel“. Hausanschluss und Zähler können vorhandene
      Assets sein; Verteilungen, Schutzgeräte und Stromkreise werden automatisch angeboten. Aus den
      Verbindungen berechnet DocOfHome gemeinsame Einspeisungen, Phasen und nachgelagerte Geräte.
      Die Ansicht dokumentiert den Bestand und ersetzt keine Elektroplanung oder Prüfung.
    </v-alert>
    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = null">
      {{ success }}
    </v-alert>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />

    <template v-else>
      <v-row class="mb-2">
        <v-col cols="6" sm="3">
          <v-card variant="tonal"><v-card-text><div class="text-h5">{{ rootCount }}</div><div class="text-medium-emphasis">Einspeisungen</div></v-card-text></v-card>
        </v-col>
        <v-col cols="6" sm="2">
          <v-card variant="tonal"><v-card-text><div class="text-h5">{{ topology.connections.length }}</div><div class="text-medium-emphasis">Verbindungen</div></v-card-text></v-card>
        </v-col>
        <v-col cols="6" sm="2">
          <v-card variant="tonal"><v-card-text><div class="text-h5">{{ topology.measurement_points?.length ?? 0 }}</div><div class="text-medium-emphasis">CT-Messpunkte</div></v-card-text></v-card>
        </v-col>
        <v-col v-for="phase in (['L1', 'L2', 'L3'] as const)" :key="phase" cols="4" sm="2">
          <v-card variant="tonal"><v-card-text><div class="text-h5">{{ phaseCounts[phase] }}</div><div class="text-medium-emphasis">mit {{ phase }}</div></v-card-text></v-card>
        </v-col>
      </v-row>

      <v-card v-if="rcdNodes.length" class="mb-5" title="FI-/RCD-Übersicht" prepend-icon="mdi-shield-outline">
        <v-card-text>
          <v-row>
            <v-col v-for="node in rcdNodes" :key="node.endpoint.key" cols="12" md="6" lg="4">
              <v-card variant="outlined">
                <v-card-title class="text-wrap">{{ node.endpoint.name }}</v-card-title>
                <v-card-subtitle>{{ node.endpoint.code }} · Einspeisung {{ node.source_names.join(', ') }}</v-card-subtitle>
                <v-card-text class="d-flex flex-wrap ga-2">
                  <v-chip color="primary" variant="tonal">{{ node.downstream_protective_device_count }} Sicherungen dahinter</v-chip>
                  <v-chip variant="tonal">{{ node.downstream_circuit_count }} Stromkreise</v-chip>
                  <v-chip variant="tonal">{{ node.downstream_asset_count }} End-Assets</v-chip>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <PhaseSupplyPathsCard
        v-if="phaseBlocks.length"
        class="mb-5"
        :blocks="phaseBlocks"
      />

      <v-card title="Versorgungstopologie" prepend-icon="mdi-file-tree-outline">
        <v-card-text v-if="rows.length === 0" class="text-center py-12">
          <v-icon icon="mdi-source-branch-remove" size="52" color="secondary" />
          <h2 class="text-h6 mt-3">Noch keine Versorgungsverbindungen</h2>
          <p class="text-medium-emphasis">
            Beginne beispielsweise mit Hausanschluss → Zähler oder Hauptsicherung.
          </p>
          <v-btn color="primary" prepend-icon="mdi-connection" @click="openCreate()">Erste Verbindung</v-btn>
        </v-card-text>

        <div v-else class="d-none d-md-block">
          <v-table hover>
            <thead><tr><th>Versorgungsweg</th><th>Phasen / Verbindung</th><th>Einspeisung</th><th>Nachgelagert</th><th /></tr></thead>
            <tbody>
              <tr
                v-for="row in rows"
                :id="`topology-desktop-${row.node.endpoint.key}`"
                :key="row.node.endpoint.key"
                :class="{ 'focus-row': highlightedKey === row.node.endpoint.key }"
              >
                <td>
                  <div class="d-flex align-center ga-2" :style="{ paddingLeft: `${row.depth * 30}px` }">
                    <v-icon v-if="row.depth" icon="mdi-subdirectory-arrow-right" size="small" class="text-medium-emphasis" />
                    <v-avatar size="34" color="surface-variant"><v-icon :icon="endpointKindIcons[row.node.endpoint.kind]" size="small" /></v-avatar>
                    <div>
                      <strong>{{ row.node.endpoint.name }}</strong>
                      <v-chip v-if="row.node.endpoint.deleted_at" size="x-small" color="warning" variant="tonal" class="ml-1">Archiviert</v-chip>
                      <div class="text-caption text-medium-emphasis">
                        {{ row.node.endpoint.code }} · {{ row.node.endpoint.type_name }}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <template v-if="row.incomingConnections.length">
                    <div v-for="connection in row.incomingConnections" :key="connection.id" class="mb-2">
                      <div class="text-caption font-weight-medium">von {{ connection.source.name }}</div>
                      <div class="d-flex flex-wrap ga-1 mb-1">
                        <v-chip v-for="phase in displayPhases(connection)" :key="`${connection.id}-${phase}`" :color="phaseColor(phase)" size="x-small" variant="tonal">{{ phase }}</v-chip>
                        <v-chip v-if="!displayPhases(connection).length" size="x-small" variant="tonal">Phase unbekannt</v-chip>
                      </div>
                      <div class="text-caption text-medium-emphasis">{{ connectionDetails(connection) }}</div>
                      <v-alert v-for="warning in connection.phase_warnings" :key="warning" type="warning" variant="tonal" density="compact" class="mt-1">{{ warning }}</v-alert>
                      <div v-if="measurementPointsForConnection(connection.id).length" class="d-flex flex-wrap ga-1 mt-1">
                        <v-chip
                          v-for="point in measurementPointsForConnection(connection.id)"
                          :key="point.id"
                          size="x-small"
                          color="teal"
                          variant="tonal"
                          prepend-icon="mdi-current-ac"
                          :to="`/assets/${point.smart_meter_asset_id}`"
                        >
                          {{ point.channel_name }} · {{ point.smart_meter_asset_name }}<span v-if="point.phase"> · {{ point.phase }}</span>
                        </v-chip>
                      </div>
                    </div>
                  </template>
                  <v-chip v-else color="primary" size="small" variant="tonal">Einspeisepunkt</v-chip>
                </td>
                <td>{{ row.node.source_names.join(', ') }}</td>
                <td>
                  <span v-if="row.node.downstream_protective_device_count">{{ row.node.downstream_protective_device_count }} Sicherungen</span>
                  <span v-if="row.node.downstream_circuit_count"> · {{ row.node.downstream_circuit_count }} Stromkreise</span>
                  <span v-if="row.node.downstream_asset_count"> · {{ row.node.downstream_asset_count }} Assets</span>
                  <span v-if="!row.node.downstream_protective_device_count && !row.node.downstream_circuit_count && !row.node.downstream_asset_count" class="text-medium-emphasis">Endpunkt</span>
                </td>
                <td class="text-right text-no-wrap">
                  <v-btn v-if="endpointRoute(row.node.endpoint)" icon="mdi-open-in-new" variant="text" size="small" :to="endpointRoute(row.node.endpoint) ?? ''" title="Datensatz öffnen" aria-label="Datensatz öffnen" />
                  <template v-for="connection in row.incomingConnections" :key="connection.id">
                    <v-btn icon="mdi-pencil" variant="text" size="small" :title="`Verbindung von ${connection.source.name} bearbeiten`" :aria-label="`Verbindung von ${connection.source.name} bearbeiten`" @click="openEdit(connection)" />
                    <v-btn icon="mdi-link-variant-off" variant="text" color="warning" size="small" :title="`Verbindung von ${connection.source.name} entfernen`" :aria-label="`Verbindung von ${connection.source.name} entfernen`" @click="removeConnection(connection)" />
                  </template>
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>

        <v-card-text class="d-md-none pa-3">
          <v-card
            v-for="row in rows"
            :id="`topology-mobile-${row.node.endpoint.key}`"
            :key="row.node.endpoint.key"
            variant="outlined"
            class="mb-3"
            :class="{ 'focus-card': highlightedKey === row.node.endpoint.key }"
            :style="{ marginLeft: `${Math.min(row.depth, 3) * 10}px` }"
          >
            <v-card-title class="d-flex align-center ga-2 text-wrap">
              <v-icon :icon="endpointKindIcons[row.node.endpoint.kind]" />{{ row.node.endpoint.name }}
              <v-chip v-if="row.node.endpoint.deleted_at" size="x-small" color="warning">Archiviert</v-chip>
            </v-card-title>
            <v-card-subtitle>{{ row.node.endpoint.code }} · {{ endpointKindLabels[row.node.endpoint.kind] }}</v-card-subtitle>
            <v-card-text>
              <div v-for="connection in row.incomingConnections" :key="connection.id" class="mb-2">
                <div class="text-caption font-weight-medium">von {{ connection.source.name }}</div>
                <div class="d-flex flex-wrap ga-1">
                  <v-chip v-for="phase in displayPhases(connection)" :key="`${connection.id}-${phase}`" :color="phaseColor(phase)" size="x-small" variant="tonal">{{ phase }}</v-chip>
                  <span class="text-caption">{{ connectionDetails(connection) }}</span>
                </div>
                <div v-if="measurementPointsForConnection(connection.id).length" class="d-flex flex-wrap ga-1 mt-1">
                  <v-chip
                    v-for="point in measurementPointsForConnection(connection.id)"
                    :key="point.id"
                    size="x-small"
                    color="teal"
                    variant="tonal"
                    prepend-icon="mdi-current-ac"
                    :to="`/assets/${point.smart_meter_asset_id}`"
                  >
                    {{ point.channel_name }} · {{ point.smart_meter_asset_name }}
                  </v-chip>
                </div>
              </div>
              <div class="text-caption">Einspeisung: {{ row.node.source_names.join(', ') }}</div>
            </v-card-text>
            <v-card-actions>
              <v-btn v-if="endpointRoute(row.node.endpoint)" variant="text" prepend-icon="mdi-open-in-new" :to="endpointRoute(row.node.endpoint) ?? ''">Öffnen</v-btn>
              <v-spacer />
              <template v-for="connection in row.incomingConnections" :key="connection.id">
                <v-btn icon="mdi-pencil" variant="text" :title="`Verbindung von ${connection.source.name} bearbeiten`" @click="openEdit(connection)" />
                <v-btn icon="mdi-link-variant-off" variant="text" color="warning" :title="`Verbindung von ${connection.source.name} entfernen`" @click="removeConnection(connection)" />
              </template>
            </v-card-actions>
          </v-card>
        </v-card-text>
      </v-card>
    </template>

    <v-dialog v-model="dialogOpen" max-width="850" scrollable>
      <v-card :title="editingConnection ? 'Versorgungsverbindung bearbeiten' : 'Versorgungsverbindung anlegen'" prepend-icon="mdi-connection">
        <v-card-text>
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            Die Quelle versorgt das Ziel. Ein Ziel darf mehrere aktive Einspeisungen besitzen,
            beispielsweise Netzanschluss, PV-Wechselrichter und Speicher. Identische Verbindungen
            bleiben ausgeschlossen und Kreise werden weiterhin verhindert.
          </v-alert>
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="sourceKey" label="Quelle" :items="sourceItems" item-title="title" item-value="value" prepend-inner-icon="mdi-export" clearable />
            </v-col>
            <v-col cols="12" md="6">
              <v-autocomplete v-model="targetKey" label="Versorgtes Ziel" :items="targetItems" item-title="title" item-value="value" prepend-inner-icon="mdi-import" clearable />
            </v-col>
            <v-col cols="12" md="6">
              <v-select v-model="form.connection_type" label="Verbindungsart" :items="connectionTypeItems" item-title="title" item-value="value" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="form.label" label="Bezeichnung (optional)" placeholder="z. B. Zuleitung HV" maxlength="150" />
            </v-col>
            <v-col cols="12">
              <v-alert
                v-if="forcedPhaseHint"
                :type="forcedPhaseConflict ? 'error' : 'info'"
                variant="tonal"
                density="compact"
                class="mb-3"
              >
                {{ forcedPhaseHint }} Die Außenleiterphase kann in dieser Verbindung nicht manuell geändert werden.
              </v-alert>
              <v-select
                :model-value="form.phases"
                label="Leiter / Phasen"
                :items="connectionPhaseItems"
                item-title="title"
                item-value="value"
                multiple
                chips
                closable-chips
                :error="forcedPhaseConflict"
                :hint="forcedLinePhases.length
                  ? 'L1/L2/L3 werden aus Position und Startphase der Schiene berechnet. N und PE bleiben auswählbar.'
                  : 'Jeder Leiter bleibt von Quelle bis Ziel identisch: L1 wird mit L1, L2 mit L2 verbunden. Bei Schrankkomponenten sind die Leiter Pflicht.'"
                persistent-hint
                @update:model-value="updateConnectionPhases"
              />
            </v-col>
            <template v-if="showCableDetails">
              <v-col cols="12" sm="6"><v-text-field v-model="form.cable_type" label="Kabel-/Leitungstyp" placeholder="z. B. NYM-J" /></v-col>
              <v-col cols="4" sm="2"><v-text-field v-model.number="form.cores" label="Adern" type="number" min="1" clearable /></v-col>
              <v-col cols="4" sm="2"><v-text-field v-model.number="form.cross_section_mm2" label="mm²" type="number" min="0.01" step="0.01" clearable /></v-col>
              <v-col cols="4" sm="2"><v-text-field v-model.number="form.length_m" label="Länge m" type="number" min="0.01" step="0.1" clearable /></v-col>
            </template>
            <v-col cols="12"><v-text-field v-model="form.route" label="Verlegeweg / Verlauf (optional)" /></v-col>
            <v-col cols="12"><v-textarea v-model="form.notes" label="Notizen (optional)" rows="2" auto-grow /></v-col>
          </v-row>
        </v-card-text>
        <v-alert
          v-if="dialogError"
          type="error"
          variant="tonal"
          density="compact"
          closable
          class="mx-6 mb-2"
          @click:close="dialogError = null"
        >
          {{ dialogError }}
        </v-alert>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialogOpen = false">Abbrechen</v-btn>
          <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="forcedPhaseConflict" @click="saveConnection">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.topology-page { max-width: 1600px; }
h1 { font-size: clamp(1.7rem, 4vw, 2.2rem); }
.focus-row { background: rgba(var(--v-theme-primary), 0.12); }
.focus-card { border: 2px solid rgb(var(--v-theme-primary)); }
</style>

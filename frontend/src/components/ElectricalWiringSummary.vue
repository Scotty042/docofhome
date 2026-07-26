<script setup lang="ts">
import { computed } from 'vue'

import {
  electricalPhaseColors,
  incomingTopologyConnections,
  topologyFocusLocation,
  topologyNode
} from '../services/electricalTopology'
import type {
  ElectricalEndpointKind,
  ElectricalPhase,
  ElectricalTopology
} from '../types/electrical'

const props = withDefaults(defineProps<{
  topology: ElectricalTopology
  endpointKind: ElectricalEndpointKind
  endpointId: string
  compact?: boolean
  showButton?: boolean
}>(), {
  compact: false,
  showButton: true
})

const node = computed(() => topologyNode(
  props.topology,
  props.endpointKind,
  props.endpointId
))
const incomingConnections = computed(() => incomingTopologyConnections(
  props.topology,
  props.endpointKind,
  props.endpointId
))
const connected = computed(() => incomingConnections.value.length > 0)
const phases = computed(() => {
  const collected = new Set(incomingConnections.value.flatMap((connection) => connection.phases))
  if (collected.size) {
    const phaseOrder: ElectricalPhase[] = ['L1', 'L2', 'L3', 'N', 'PE']
    return phaseOrder.filter((phase) => collected.has(phase))
  }
  return node.value?.incoming_phases ?? []
})
const sourceNames = computed(() => {
  if (node.value?.source_names.length) return node.value.source_names.join(', ')
  const names = [...new Set(incomingConnections.value.map((connection) => connection.source.name))]
  return names.length ? names.join(', ') : null
})
const downstreamParts = computed(() => {
  if (!node.value) return []
  return [
    node.value.downstream_protective_device_count
      ? `${node.value.downstream_protective_device_count} Schutzgeräte`
      : null,
    node.value.downstream_circuit_count
      ? `${node.value.downstream_circuit_count} Stromkreise`
      : null,
    node.value.downstream_asset_count
      ? `${node.value.downstream_asset_count} Assets`
      : null
  ].filter((value): value is string => Boolean(value))
})
const compactDownstreamParts = computed(() => {
  if (!node.value) return []
  return [
    node.value.downstream_protective_device_count
      ? `${node.value.downstream_protective_device_count} SG`
      : null,
    node.value.downstream_circuit_count
      ? `${node.value.downstream_circuit_count} SK`
      : null,
    node.value.downstream_asset_count
      ? `${node.value.downstream_asset_count} A`
      : null
  ].filter((value): value is string => Boolean(value))
})
const location = computed(() => topologyFocusLocation(
  props.endpointKind,
  props.endpointId,
  connected.value
))
</script>

<template>
  <div class="electrical-wiring-summary" :class="{ 'is-compact': compact }">
    <div class="d-flex flex-wrap align-center ga-1">
      <v-chip
        v-for="phase in phases"
        :key="phase"
        :color="electricalPhaseColors[phase]"
        :size="compact ? 'x-small' : 'small'"
        variant="tonal"
        :title="`Diese Verbindung führt ${phase}.`"
      >
        {{ phase }}
      </v-chip>
      <v-chip
        v-if="!connected"
        color="warning"
        :size="compact ? 'x-small' : 'small'"
        variant="tonal"
        title="Für dieses Element ist noch keine eingehende Versorgungsverbindung dokumentiert."
      >
        {{ compact ? 'Nicht verk.' : 'Nicht verkabelt' }}
      </v-chip>
      <v-chip
        v-else-if="phases.length === 0"
        color="warning"
        :size="compact ? 'x-small' : 'small'"
        variant="outlined"
        title="Die Verbindung ist dokumentiert, aber die geführten Phasen fehlen noch."
      >
        Phase unbekannt
      </v-chip>
    </div>

    <div v-if="incomingConnections.length > 1" class="text-caption mt-1 font-weight-medium">
      {{ incomingConnections.length }} dokumentierte Einspeisungen
    </div>
    <div v-if="sourceNames" class="text-caption mt-1" title="Ursprüngliche Einspeisungen dieses Versorgungswegs">
      Einspeisung: {{ sourceNames }}
    </div>
    <div
      v-if="connected"
      class="text-caption text-medium-emphasis mt-1"
      title="Alle dokumentierten Schutzgeräte, Stromkreise und Assets hinter diesem Element"
    >
      <template v-if="compact">
        Dahinter: {{ compactDownstreamParts.length ? compactDownstreamParts.join(' · ') : 'kein Abgang' }}
      </template>
      <template v-else>
        Dahinter: {{ downstreamParts.length ? downstreamParts.join(' · ') : 'kein dokumentierter Abgang' }}
      </template>
    </div>

    <v-btn
      v-if="showButton"
      class="mt-2"
      :size="compact ? 'x-small' : 'small'"
      variant="tonal"
      :color="connected ? 'primary' : 'warning'"
      :icon="compact ? (connected ? 'mdi-eye-outline' : 'mdi-connection') : undefined"
      :prepend-icon="compact ? undefined : (connected ? 'mdi-eye-outline' : 'mdi-connection')"
      :to="location"
      :aria-label="connected ? 'Versorgungsweg anzeigen' : 'Verkabelung anlegen'"
      :title="connected
        ? 'Dieses Element mit allen Einspeisungen im Versorgungsbaum anzeigen'
        : 'Neue Versorgungsverbindung mit diesem Ziel anlegen'"
    >
      <template v-if="!compact">{{ connected ? 'Versorgungsweg' : 'Verkabeln' }}</template>
    </v-btn>
  </div>
</template>

<style scoped>
.electrical-wiring-summary { min-width: 0; overflow-wrap: anywhere; }
.electrical-wiring-summary.is-compact { line-height: 1.25; }
.electrical-wiring-summary.is-compact :deep(.v-chip) { max-width: 100%; }
</style>

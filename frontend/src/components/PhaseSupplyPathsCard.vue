<script setup lang="ts">
import { electricalPhaseColors } from '../services/electricalTopology'
import type {
  PhaseDistributionGroup,
  PhaseSupplyGroupKey,
  PhaseSupplyPath
} from '../services/electricalTopology'
import type {
  ElectricalConnection,
  ElectricalEndpoint,
  ElectricalPhase
} from '../types/electrical'

withDefaults(defineProps<{
  blocks: PhaseDistributionGroup[]
  compact?: boolean
  title?: string
}>(), {
  compact: false,
  title: 'Versorgungswege nach Phasen'
})

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

function phaseColor(phase: ElectricalPhase): string {
  return electricalPhaseColors[phase]
}

function phaseChipClass(phase: ElectricalPhase): string {
  return `phase-supply-chip phase-supply-chip-${phase.toLowerCase()}`
}

function groupClass(key: PhaseSupplyGroupKey): string {
  return `phase-supply-group-${key.toLowerCase()}`
}

function pathWarnings(path: PhaseSupplyPath): string[] {
  return [
    path.phaseMismatch
      ? 'Phasenwechsel oder Phasenerweiterung im dokumentierten Weg'
      : null,
    path.missingPhaseData
      ? 'Mindestens eine Verbindung besitzt keine Phasenzuordnung'
      : null,
    path.cycleDetected
      ? 'Zyklischer Versorgungsweg erkannt'
      : null
  ].filter((item): item is string => item !== null)
}

function connectionDetails(connection: ElectricalConnection): string {
  return [
    connection.label,
    connection.cable_type,
    connection.route
  ].filter(Boolean).join(' · ')
}
</script>

<template>
  <v-card class="phase-supply-card" :density="compact ? 'compact' : 'default'">
    <v-card-title class="d-flex align-center ga-2">
      <v-icon icon="mdi-source-branch" />
      <span>{{ title }}</span>
    </v-card-title>
    <v-card-subtitle>
      Vollständige Reihenfolge ab Phasenverteilerblock; jede Verbindung zeigt ihre Leiter.
    </v-card-subtitle>
    <v-card-text>
      <v-expansion-panels multiple variant="accordion">
        <v-expansion-panel
          v-for="block in blocks"
          :key="block.block.endpoint.key"
          class="phase-supply-block"
        >
          <v-expansion-panel-title>
            <div class="d-flex align-center flex-wrap ga-2">
              <v-icon icon="mdi-call-split" size="small" />
              <strong>{{ block.block.endpoint.name }}</strong>
              <v-chip size="x-small" variant="tonal">
                {{ block.groups.reduce((sum, group) => sum + group.paths.length, 0) }}
                Versorgungswege
              </v-chip>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-expansion-panels multiple variant="accordion">
              <v-expansion-panel
                v-for="group in block.groups"
                :key="group.key"
                :class="['phase-supply-group', groupClass(group.key)]"
              >
                <v-expansion-panel-title>
                  <div class="d-flex align-center flex-wrap ga-2">
                    <strong>{{ group.label }}</strong>
                    <v-chip size="x-small" variant="tonal">
                      {{ group.paths.length }}
                      {{ group.paths.length === 1 ? 'Weg' : 'Wege' }}
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <article
                    v-for="(path, pathIndex) in group.paths"
                    :key="path.id"
                    class="phase-supply-path"
                    :aria-label="`${group.label}, Versorgungsweg ${pathIndex + 1}`"
                  >
                    <header class="d-flex align-center flex-wrap ga-2 mb-2">
                      <span class="text-caption font-weight-bold">
                        Versorgungsweg {{ pathIndex + 1 }}
                      </span>
                      <v-chip
                        v-for="phase in path.effectivePhases"
                        :key="`${path.id}-effective-${phase}`"
                        :color="phaseColor(phase)"
                        :class="phaseChipClass(phase)"
                        size="x-small"
                        variant="flat"
                      >
                        {{ phase }}
                      </v-chip>
                      <v-chip
                        v-if="!path.effectivePhases.length"
                        color="warning"
                        size="x-small"
                        variant="tonal"
                      >
                        Phase nicht zugeordnet
                      </v-chip>
                    </header>

                    <div class="phase-supply-flow">
                      <div class="phase-supply-node phase-supply-source">
                        <v-icon icon="mdi-call-split" size="small" />
                        <span>{{ block.block.endpoint.name }}</span>
                      </div>
                      <template
                        v-for="connection in path.connections"
                        :key="`${path.id}-${connection.id}`"
                      >
                        <div class="phase-supply-edge">
                          <v-icon icon="mdi-arrow-right" size="small" />
                          <div class="d-flex flex-wrap justify-center ga-1">
                            <v-chip
                              v-for="phase in connection.effective_phases"
                              :key="`${connection.id}-${phase}`"
                              :color="phaseColor(phase)"
                              :class="phaseChipClass(phase)"
                              size="x-small"
                              variant="flat"
                            >
                              {{ phase }}
                            </v-chip>
                            <v-chip
                              v-if="!connection.effective_phases.length"
                              color="warning"
                              size="x-small"
                              variant="tonal"
                            >
                              ?
                            </v-chip>
                          </div>
                          <span
                            v-if="connectionDetails(connection)"
                            class="phase-supply-edge-details"
                            :title="connectionDetails(connection)"
                          >
                            {{ connectionDetails(connection) }}
                          </span>
                        </div>
                        <v-chip
                          class="phase-supply-node"
                          size="small"
                          variant="outlined"
                          :prepend-icon="connection.target.kind === 'asset'
                            ? 'mdi-package-variant'
                            : connection.target.kind === 'protective_device'
                              ? 'mdi-shield-outline'
                              : connection.target.kind === 'circuit'
                                ? 'mdi-transmission-tower'
                                : 'mdi-electric-switch'"
                          :to="endpointRoute(connection.target) ?? undefined"
                          :title="connection.target.type_name"
                        >
                          {{ connection.target.name }}
                        </v-chip>
                      </template>
                    </div>

                    <v-alert
                      v-if="pathWarnings(path).length"
                      type="warning"
                      variant="tonal"
                      density="compact"
                      class="mt-2"
                    >
                      {{ pathWarnings(path).join(' · ') }}
                    </v-alert>
                  </article>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.phase-supply-block { border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.phase-supply-group { border-inline-start: 4px solid rgba(var(--v-theme-primary), 0.6); }
.phase-supply-group-l1 { border-inline-start-color: #8d6e63; }
.phase-supply-group-l2 { border-inline-start-color: #90a4ae; }
.phase-supply-group-l3 { border-inline-start-color: #424242; }
.phase-supply-group-multi { border-inline-start-color: #7e57c2; }
.phase-supply-group-unassigned { border-inline-start-color: #fb8c00; }
.phase-supply-chip {
  border: 1px solid transparent;
  color: #fff !important;
  font-weight: 800;
}
.phase-supply-chip-l1 { background: #795548 !important; }
.phase-supply-chip-l2 { background: #111 !important; color: #fff !important; border-color: rgba(255, 255, 255, 0.28); }
.phase-supply-chip-l3 { background: #616161 !important; color: #fff !important; border-color: #9e9e9e; }
.phase-supply-chip-n { background: #1565c0 !important; }
.phase-supply-chip-pe { background: #2e7d32 !important; }
.phase-supply-path {
  padding: 12px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 8px;
}
.phase-supply-path + .phase-supply-path { margin-top: 12px; }
.phase-supply-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 4px 2px 10px;
  overflow-x: auto;
}
.phase-supply-node {
  flex: 0 0 auto;
  max-width: 220px;
}
.phase-supply-source {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(var(--v-theme-primary), 0.12);
  font-size: 0.78rem;
  font-weight: 700;
}
.phase-supply-edge {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.phase-supply-edge-details {
  max-width: 120px;
  overflow: hidden;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 0.66rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

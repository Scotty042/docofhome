<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type {
  ElectricalConnection,
  ElectricalEndpoint,
  ElectricalPhase,
  ElectricalTopology
} from '../types/electrical'

const props = defineProps<{
  topology: ElectricalTopology
  active: boolean
}>()

type Point = { x: number; y: number }
type Anchor = Point & {
  key: string
  endpoint: ElectricalEndpoint
  external: boolean
  width: number
  height: number
  left: number
  right: number
  top: number
  bottom: number
  flowThrough: boolean
}
type ConnectionPort = Point & {
  side: 'top' | 'bottom'
}
type FlowPortMarker = Point & {
  key: string
  label: 'IN' | 'OUT'
}
type VisualConnection = {
  id: string
  source: ElectricalEndpoint
  target: ElectricalEndpoint
  phases: Array<ElectricalPhase | 'unknown'>
}
type ResolvedConnection = {
  connection: VisualConnection
  source: Anchor
  target: Anchor
}
type WiringPath = {
  id: string
  phase: ElectricalPhase | 'unknown'
  d: string
  label: string
}
type ExternalNode = {
  key: string
  x: number
  y: number
  label: string
  shape: 'triangle' | 'circle' | 'square'
  direction: 'incoming' | 'outgoing'
}

const svg = ref<SVGSVGElement | null>(null)
const width = ref(0)
const height = ref(0)
const paths = ref<WiringPath[]>([])
const externalNodes = ref<ExternalNode[]>([])
const flowPortMarkers = ref<FlowPortMarker[]>([])
let resizeObserver: ResizeObserver | null = null
let animationFrame = 0
let container: HTMLElement | null = null

const phaseOrder: ElectricalPhase[] = ['L1', 'L2', 'L3', 'N', 'PE']
const phaseLabels: Record<ElectricalPhase | 'unknown', string> = {
  L1: 'L1',
  L2: 'L2',
  L3: 'L3',
  N: 'N',
  PE: 'PE',
  unknown: 'Leiter nicht angegeben'
}

function escapeAttribute(value: string): string {
  if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') return CSS.escape(value)
  return value.replace(/["\\]/g, '\\$&')
}

function endpointElement(key: string): HTMLElement | null {
  if (!container) return null
  return container.querySelector<HTMLElement>(
    `[data-electrical-endpoint-key="${escapeAttribute(key)}"]`
  )
}

function relativeRect(element: HTMLElement): DOMRect {
  const elementRect = element.getBoundingClientRect()
  const containerRect = container?.getBoundingClientRect() ?? new DOMRect()
  return new DOMRect(
    elementRect.left - containerRect.left + (container?.scrollLeft ?? 0),
    elementRect.top - containerRect.top + (container?.scrollTop ?? 0),
    elementRect.width,
    elementRect.height
  )
}

function representedAnchor(endpoint: ElectricalEndpoint): Anchor | null {
  const element = endpointElement(endpoint.key)
  if (!element) return null
  const rect = relativeRect(element)
  return {
    key: endpoint.key,
    endpoint,
    external: false,
    width: rect.width,
    height: rect.height,
    left: rect.left,
    right: rect.right,
    top: rect.top,
    bottom: rect.bottom,
    flowThrough: element.dataset.electricalFlowThrough === 'true'
      || endpoint.device_type === 'rcd',
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2
  }
}

function externalShape(endpoint: ElectricalEndpoint, source: boolean): ExternalNode['shape'] {
  if (endpoint.kind === 'grid_connection') return 'triangle'
  if (endpoint.kind === 'distribution') return 'square'
  return source ? 'triangle' : 'circle'
}

function activeConnections(): ElectricalConnection[] {
  return props.topology.connections.filter((connection) => connection.deleted_at === null)
}

function isFlowThroughEndpoint(endpoint: ElectricalEndpoint): boolean {
  return endpoint.device_type === 'rcd'
    || endpointElement(endpoint.key)?.dataset.electricalFlowThrough === 'true'
}

function isAutomaticBusbarContact(connection: ElectricalConnection): boolean {
  return connection.connection_type === 'busbar'
    && connection.source.kind === 'cabinet_component'
    && ['phase_rail', 'busbar'].includes(connection.source.device_type ?? '')
    && !isFlowThroughEndpoint(connection.target)
}

function isIndividualCircuitBranch(connection: ElectricalConnection): boolean {
  // Nur die Verbindung vom Schutzgerät zum eigentlichen Stromkreis wird in der
  // Schrankgrafik ausgeblendet. Eine manuelle Einspeisung zu einem LS/MCB/RCBO
  // bleibt sichtbar, damit z. B. Phasenverteilerblock → Sicherung dargestellt wird.
  return connection.source.kind === 'circuit' || connection.target.kind === 'circuit'
}

function conductorPhases(connection: ElectricalConnection): Array<ElectricalPhase | 'unknown'> {
  const phases = connection.effective_phases.length
    ? connection.effective_phases
    : connection.phases
  const unique = [...new Set(phases)]
  const ordered = phaseOrder.filter((phase) => unique.includes(phase))
  return ordered.length ? ordered : ['unknown']
}

function visibleConnections(): VisualConnection[] {
  const connections = activeConnections()
  const grouped = new Map<string, VisualConnection>()

  for (const connection of connections) {
    if (isAutomaticBusbarContact(connection)) continue
    if (isIndividualCircuitBranch(connection)) continue
    if (!endpointElement(connection.source.key) && !endpointElement(connection.target.key)) continue

    // Mehrere Datensätze zwischen denselben Hauptkomponenten werden zu einem sichtbaren
    // Leitungsweg gebündelt. Die einzelnen Leiter bleiben mit festem Abstand erkennbar.
    const key = `${connection.source.key}->${connection.target.key}`
    const existing = grouped.get(key)
    const phases = conductorPhases(connection)
    if (existing) {
      const combined = new Set([...existing.phases, ...phases])
      existing.phases = [
        ...phaseOrder.filter((phase) => combined.has(phase)),
        ...(combined.has('unknown') ? ['unknown' as const] : [])
      ]
      continue
    }
    grouped.set(key, {
      id: connection.id,
      source: connection.source,
      target: connection.target,
      phases
    })
  }

  return [...grouped.values()]
}

function externalAnchors(connections: VisualConnection[]): Map<string, Anchor> {
  const references = new Map<string, { endpoint: ElectricalEndpoint; points: Point[]; source: boolean }>()
  for (const connection of connections) {
    const sourceElement = endpointElement(connection.source.key)
    const targetElement = endpointElement(connection.target.key)
    if (!sourceElement && targetElement) {
      const rect = relativeRect(targetElement)
      const entry = references.get(connection.source.key) ?? {
        endpoint: connection.source,
        points: [],
        source: true
      }
      entry.points.push({ x: rect.left + rect.width / 2, y: rect.top })
      references.set(connection.source.key, entry)
    }
    if (sourceElement && !targetElement) {
      const rect = relativeRect(sourceElement)
      const entry = references.get(connection.target.key) ?? {
        endpoint: connection.target,
        points: [],
        source: false
      }
      entry.points.push({ x: rect.left + rect.width / 2, y: rect.bottom })
      references.set(connection.target.key, entry)
    }
  }

  const incomingEntries = [...references.entries()].filter(([, entry]) => entry.source)
  const outgoingEntries = [...references.entries()].filter(([, entry]) => !entry.source)
  const anchors = new Map<string, Anchor>()
  const nodes: ExternalNode[] = []
  const horizontalPadding = 34
  const verticalPadding = 28

  incomingEntries.forEach(([key, entry], index) => {
    const averageX = entry.points.reduce((sum, point) => sum + point.x, 0) / entry.points.length
    const x = Math.min(Math.max(averageX, horizontalPadding), Math.max(horizontalPadding, width.value - horizontalPadding))
    const y = entry.endpoint.kind === 'grid_connection'
      ? Math.max(verticalPadding, height.value - verticalPadding)
      : verticalPadding + index * 18
    anchors.set(key, {
      key,
      endpoint: entry.endpoint,
      external: true,
      width: 0,
      height: 0,
      left: x,
      right: x,
      top: y,
      bottom: y,
      flowThrough: false,
      x,
      y
    })
    nodes.push({
      key,
      x,
      y,
      label: entry.endpoint.kind === 'grid_connection' ? 'Hausanschluss' : entry.endpoint.name,
      shape: externalShape(entry.endpoint, true),
      direction: 'incoming'
    })
  })

  outgoingEntries.forEach(([key, entry], index) => {
    const averageX = entry.points.reduce((sum, point) => sum + point.x, 0) / entry.points.length
    const x = Math.min(Math.max(averageX, horizontalPadding), Math.max(horizontalPadding, width.value - horizontalPadding))
    const y = Math.max(verticalPadding, height.value - verticalPadding - (index + 2) * 18)
    anchors.set(key, {
      key,
      endpoint: entry.endpoint,
      external: true,
      width: 0,
      height: 0,
      left: x,
      right: x,
      top: y,
      bottom: y,
      flowThrough: false,
      x,
      y
    })
    nodes.push({
      key,
      x,
      y,
      label: entry.endpoint.name,
      shape: externalShape(entry.endpoint, false),
      direction: 'outgoing'
    })
  })

  externalNodes.value = nodes
  return anchors
}

function connectionPortOffsets(connections: ResolvedConnection[]): Map<string, number> {
  const groups = new Map<string, Array<{ connectionId: string; oppositeX: number; width: number }>>()

  const add = (role: 'source' | 'target', item: ResolvedConnection) => {
    const anchor = role === 'source' ? item.source : item.target
    if (anchor.external) return
    const opposite = role === 'source' ? item.target : item.source
    const key = `${role}:${anchor.key}`
    const group = groups.get(key) ?? []
    group.push({ connectionId: item.connection.id, oppositeX: opposite.x, width: anchor.width })
    groups.set(key, group)
  }

  for (const item of connections) {
    add('source', item)
    add('target', item)
  }

  const offsets = new Map<string, number>()
  for (const [groupKey, group] of groups) {
    group.sort((left, right) => left.oppositeX - right.oppositeX || left.connectionId.localeCompare(right.connectionId))
    const availableWidth = Math.max(0, Math.min(group[0]?.width ?? 0, 96) * 0.62)
    const spacing = group.length > 1
      ? Math.min(14, Math.max(8, availableWidth / Math.max(1, group.length - 1)))
      : 0
    const center = (group.length - 1) / 2
    const role = groupKey.split(':')[0]
    group.forEach((entry, index) => {
      offsets.set(`${entry.connectionId}:${role}`, (index - center) * spacing)
    })
  }
  return offsets
}

function shiftedAnchor(anchor: Anchor, offset: number): Anchor {
  return {
    ...anchor,
    x: anchor.x + offset,
    left: anchor.left + offset,
    right: anchor.right + offset
  }
}

function choosePort(
  anchor: Anchor,
  opposite: Anchor,
  role: 'source' | 'target'
): ConnectionPort {
  if (anchor.external) return { x: anchor.x, y: anchor.y, side: 'top' }

  const verticalDelta = opposite.y - anchor.y
  const side: ConnectionPort['side'] = verticalDelta < -12 ? 'top' : 'bottom'
  const y = side === 'top' ? anchor.top : anchor.bottom

  if (anchor.flowThrough) {
    // FI/RCD werden als echtes Durchgangsgerät dargestellt: Eingang und Ausgang
    // erhalten getrennte Anschlusszonen. Dadurch ist insbesondere beim Neutralleiter
    // eindeutig sichtbar: Hausanschluss → FI-Eingang → FI-Ausgang → N-Schiene.
    const horizontalOffset = Math.min(28, Math.max(12, anchor.width * 0.22))
    return {
      x: anchor.x + (role === 'target' ? -horizontalOffset : horizontalOffset),
      y,
      side
    }
  }

  return { x: anchor.x, y, side }
}

function routeGroup(item: ResolvedConnection): string {
  const centerY = (item.source.y + item.target.y) / 2
  return `band:${Math.round(centerY / 96)}`
}

function laneAssignments(connections: ResolvedConnection[]): Map<string, number> {
  const groups = new Map<string, ResolvedConnection[]>()
  for (const item of connections) {
    const key = routeGroup(item)
    const group = groups.get(key) ?? []
    group.push(item)
    groups.set(key, group)
  }

  const assignments = new Map<string, number>()
  for (const group of groups.values()) {
    group.sort((left, right) => {
      return Math.min(left.source.x, left.target.x) - Math.min(right.source.x, right.target.x)
        || Math.min(left.source.y, left.target.y) - Math.min(right.source.y, right.target.y)
        || left.connection.id.localeCompare(right.connection.id)
    })
    const center = (group.length - 1) / 2
    group.forEach((item, index) => {
      // Die Wege dürfen innerhalb des Schrankbilds verlaufen. Ein begrenzter Spurversatz
      // verhindert deckungsgleiche Verbindungen, ohne sie an einen Außenrand zu zwingen.
      assignments.set(item.connection.id, Math.max(-42, Math.min(42, (index - center) * 12)))
    })
  }
  return assignments
}

function orthogonalPath(source: Anchor, target: Anchor, lane: number, conductorOffset: number): string {
  const sourcePort = choosePort(source, target, 'source')
  const targetPort = choosePort(target, source, 'target')
  const sx = sourcePort.x + conductorOffset
  const sy = sourcePort.y
  const tx = targetPort.x + conductorOffset
  const ty = targetPort.y

  // Nahezu gleiche Höhe: innerhalb der Darstellung mit leichtem Abstand horizontal führen.
  if (Math.abs(ty - sy) <= 12) {
    const trackY = sy + lane + conductorOffset
    return `M ${sx} ${sy} L ${sx} ${trackY} L ${tx} ${trackY} L ${tx} ${ty}`
  }

  // Auf- und absteigende Leitungen werden direkt in die passende Richtung geführt.
  // So gehen Verbindungen zu einer oberhalb liegenden Sammelschiene unmittelbar nach oben,
  // während von unten kommende Leitungen sauber an der Unterseite eines Geräts enden.
  const baseMidY = sy + (ty - sy) / 2
  const trackY = baseMidY + lane + conductorOffset
  return `M ${sx} ${sy} L ${sx} ${trackY} L ${tx} ${trackY} L ${tx} ${ty}`
}

function rebuild() {
  cancelAnimationFrame(animationFrame)
  animationFrame = requestAnimationFrame(() => {
    if (!props.active || !svg.value) {
      paths.value = []
      externalNodes.value = []
      flowPortMarkers.value = []
      return
    }
    container = svg.value.parentElement
    if (!container) return
    width.value = Math.max(container.clientWidth, container.scrollWidth)
    height.value = Math.max(container.clientHeight, container.scrollHeight)

    const connections = visibleConnections()
    const external = externalAnchors(connections)
    const resolved = connections.flatMap<ResolvedConnection>((connection) => {
      const source = representedAnchor(connection.source) ?? external.get(connection.source.key)
      const target = representedAnchor(connection.target) ?? external.get(connection.target.key)
      return source && target ? [{ connection, source, target }] : []
    })
    const portOffsets = connectionPortOffsets(resolved)
    const lanes = laneAssignments(resolved)
    const nextPaths: WiringPath[] = []
    const nextFlowPortMarkers = new Map<string, FlowPortMarker>()

    resolved.forEach((item) => {
      const source = shiftedAnchor(item.source, portOffsets.get(`${item.connection.id}:source`) ?? 0)
      const target = shiftedAnchor(item.target, portOffsets.get(`${item.connection.id}:target`) ?? 0)
      const lane = lanes.get(item.connection.id) ?? 0

      if (source.flowThrough) {
        const port = choosePort(source, target, 'source')
        nextFlowPortMarkers.set(`${source.key}:out:${port.side}`, {
          key: `${source.key}:out:${port.side}`,
          x: port.x,
          y: port.y,
          label: 'OUT'
        })
      }
      if (target.flowThrough) {
        const port = choosePort(target, source, 'target')
        nextFlowPortMarkers.set(`${target.key}:in:${port.side}`, {
          key: `${target.key}:in:${port.side}`,
          x: port.x,
          y: port.y,
          label: 'IN'
        })
      }

      item.connection.phases.forEach((phase, phaseIndex) => {
        const center = (item.connection.phases.length - 1) / 2
        // 8 px Abstand sorgt dafür, dass auch horizontale L1/L2/L3/N/PE-Abschnitte
        // nicht deckungsgleich übereinanderliegen.
        const conductorOffset = (phaseIndex - center) * 8
        nextPaths.push({
          id: `${item.connection.id}:${phase}`,
          phase,
          d: orthogonalPath(source, target, lane, conductorOffset),
          label: `${item.connection.source.name} → ${item.connection.target.name} · ${phaseLabels[phase]}`
        })
      })
    })
    paths.value = nextPaths
    flowPortMarkers.value = [...nextFlowPortMarkers.values()]
  })
}

function scheduleRebuild() {
  void nextTick().then(rebuild)
}

onMounted(() => {
  container = svg.value?.parentElement ?? null
  resizeObserver = new ResizeObserver(scheduleRebuild)
  if (container) {
    resizeObserver.observe(container)
    container.addEventListener('scroll', scheduleRebuild, true)
  }
  window.addEventListener('resize', scheduleRebuild)
  scheduleRebuild()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  container?.removeEventListener('scroll', scheduleRebuild, true)
  window.removeEventListener('resize', scheduleRebuild)
})

watch(() => [props.active, props.topology], scheduleRebuild, { deep: true })
</script>

<template>
  <svg
    v-show="active"
    ref="svg"
    class="cabinet-wiring-overlay"
    :width="width"
    :height="height"
    :viewBox="`0 0 ${width} ${height}`"
    role="img"
    aria-label="Visuelle Hauptverkabelung des Schaltschranks"
  >
    <g class="wiring-paths wiring-path-halos" aria-hidden="true">
      <path
        v-for="path in paths"
        :key="`halo:${path.id}`"
        :d="path.d"
        class="wiring-path-halo"
        vector-effect="non-scaling-stroke"
      />
    </g>
    <g class="wiring-paths">
      <path
        v-for="path in paths"
        :key="path.id"
        :d="path.d"
        :class="['wiring-path', `wire-${path.phase.toLowerCase()}`]"
        vector-effect="non-scaling-stroke"
      >
        <title>{{ path.label }}</title>
      </path>
    </g>

    <g class="flow-port-markers">
      <g v-for="marker in flowPortMarkers" :key="marker.key" class="flow-port-marker">
        <circle :cx="marker.x" :cy="marker.y" r="4.5" />
        <text :x="marker.x + 7" :y="marker.y - 6">{{ marker.label }}</text>
      </g>
    </g>

    <g v-for="node in externalNodes" :key="node.key" class="external-node">
      <polygon
        v-if="node.shape === 'triangle'"
        :points="`${node.x},${node.y - 10} ${node.x - 11},${node.y + 9} ${node.x + 11},${node.y + 9}`"
        class="external-node-shape"
      />
      <rect
        v-else-if="node.shape === 'square'"
        :x="node.x - 9"
        :y="node.y - 9"
        width="18"
        height="18"
        rx="2"
        class="external-node-shape"
      />
      <circle v-else :cx="node.x" :cy="node.y" r="9" class="external-node-shape" />
      <text
        :x="node.x + 14"
        :y="node.y + 4"
        class="external-node-label"
      >
        {{ node.label }}
      </text>
      <title>{{ node.direction === 'incoming' ? 'Einspeisung' : 'Abgang aus dem Verteiler' }}: {{ node.label }}</title>
    </g>
  </svg>
</template>

<style scoped>
.cabinet-wiring-overlay {
  position: absolute;
  inset: 0;
  z-index: 8;
  overflow: visible;
  pointer-events: none;
}
.wiring-path-halo {
  fill: none;
  stroke: rgba(8, 13, 18, 0.88);
  stroke-width: 4.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.wiring-path {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.95;
}
.wire-l1 { stroke: #e53935; }
.wire-l2 { stroke: #101010; filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.95)); }
.wire-l3 { stroke: #d0d0d0; }
.wire-n { stroke: #1e88e5; }
.wire-pe { stroke: #43a047; stroke-dasharray: 10 4 2 4; }
.wire-unknown { stroke: #ffb300; stroke-dasharray: 5 5; }
.flow-port-marker circle {
  fill: rgb(var(--v-theme-surface));
  stroke: rgb(var(--v-theme-primary));
  stroke-width: 2;
}
.flow-port-marker text {
  fill: rgb(var(--v-theme-on-surface));
  font-size: 9px;
  font-weight: 800;
  paint-order: stroke;
  stroke: rgb(var(--v-theme-surface));
  stroke-width: 3px;
}
.external-node-shape {
  fill: rgb(var(--v-theme-surface));
  stroke: rgb(var(--v-theme-primary));
  stroke-width: 2;
}
.external-node-label {
  fill: rgb(var(--v-theme-on-surface));
  font-size: 11px;
  font-weight: 700;
  paint-order: stroke;
  stroke: rgb(var(--v-theme-surface));
  stroke-width: 3px;
  stroke-linejoin: round;
}
</style>

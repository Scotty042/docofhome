import type {
  ElectricalConnection,
  ElectricalEndpoint,
  ElectricalEndpointKind,
  ElectricalPhase,
  ElectricalTopology,
  ElectricalTopologyNode
} from '../types/electrical'

export interface ElectricalTopologyRow {
  node: ElectricalTopologyNode
  depth: number
  incomingConnection: ElectricalConnection | null
  incomingConnections: ElectricalConnection[]
}

export type PhaseSupplyGroupKey = 'L1' | 'L2' | 'L3' | 'multi' | 'unassigned'

export interface PhaseSupplyPath {
  id: string
  connections: ElectricalConnection[]
  effectivePhases: Array<'L1' | 'L2' | 'L3'>
  phaseMismatch: boolean
  missingPhaseData: boolean
  cycleDetected: boolean
}

export interface PhaseDistributionGroup {
  block: ElectricalTopologyNode
  groups: Array<{
    key: PhaseSupplyGroupKey
    label: string
    paths: PhaseSupplyPath[]
  }>
}

export const endpointKindLabels: Record<ElectricalEndpointKind, string> = {
  grid_connection: 'Netzanschluss',
  asset: 'Asset',
  distribution: 'Verteilung',
  protective_device: 'Schutzgerät',
  cabinet_component: 'Schrankkomponente',
  circuit: 'Stromkreis'
}

export const endpointKindIcons: Record<ElectricalEndpointKind, string> = {
  grid_connection: 'mdi-transmission-tower-import',
  asset: 'mdi-package-variant',
  distribution: 'mdi-electric-switch',
  protective_device: 'mdi-shield-outline',
  cabinet_component: 'mdi-call-split',
  circuit: 'mdi-transmission-tower'
}

export const electricalPhaseColors: Record<ElectricalPhase, string> = {
  L1: 'brown',
  L2: 'grey',
  L3: 'black',
  N: 'blue',
  PE: 'green'
}

export function topologyRows(topology: ElectricalTopology): ElectricalTopologyRow[] {
  const nodes = new Map(topology.nodes.map((node) => [node.endpoint.key, node]))
  const incoming = new Map<string, ElectricalConnection[]>()
  topology.connections.forEach((connection) => {
    const entries = incoming.get(connection.target.key) ?? []
    entries.push(connection)
    entries.sort((left, right) => left.source.name.localeCompare(right.source.name, 'de'))
    incoming.set(connection.target.key, entries)
  })
  const outgoing = new Map<string, ElectricalConnection[]>()
  topology.connections.forEach((connection) => {
    const entries = outgoing.get(connection.source.key) ?? []
    entries.push(connection)
    entries.sort((left, right) => left.target.name.localeCompare(right.target.name, 'de'))
    outgoing.set(connection.source.key, entries)
  })
  const roots = topology.nodes
    .filter((node) => !incoming.has(node.endpoint.key))
    .sort((left, right) => left.endpoint.name.localeCompare(right.endpoint.name, 'de'))
  const result: ElectricalTopologyRow[] = []
  const visited = new Set<string>()
  const visit = (node: ElectricalTopologyNode, depth: number) => {
    if (visited.has(node.endpoint.key)) return
    visited.add(node.endpoint.key)
    result.push({
      node,
      depth,
      incomingConnection: incoming.get(node.endpoint.key)?.[0] ?? null,
      incomingConnections: incoming.get(node.endpoint.key) ?? []
    })
    for (const connection of outgoing.get(node.endpoint.key) ?? []) {
      const child = nodes.get(connection.target.key)
      if (child) visit(child, depth + 1)
    }
  }
  roots.forEach((root) => visit(root, 0))
  topology.nodes
    .filter((node) => !visited.has(node.endpoint.key))
    .forEach((node) => visit(node, 0))
  return result
}

export function phaseConnectionCounts(
  topology: ElectricalTopology
): Record<'L1' | 'L2' | 'L3', number> {
  return Object.fromEntries(
    (['L1', 'L2', 'L3'] as const).map((phase) => [
      phase,
      topology.connections.filter((connection) => connection.effective_phases.includes(phase)).length
    ])
  ) as Record<'L1' | 'L2' | 'L3', number>
}

export function phaseDistributionGroups(
  topology: ElectricalTopology
): PhaseDistributionGroup[] {
  const activeConnections = topology.connections.filter(
    (connection) => connection.deleted_at === null
  )
  const outgoing = new Map<string, ElectricalConnection[]>()
  for (const connection of activeConnections) {
    const entries = outgoing.get(connection.source.key) ?? []
    entries.push(connection)
    outgoing.set(connection.source.key, entries)
  }
  const electricalPhases = (
    connection: ElectricalConnection
  ): Array<'L1' | 'L2' | 'L3'> => connection.effective_phases.filter(
    (phase): phase is 'L1' | 'L2' | 'L3' => phase === 'L1' || phase === 'L2' || phase === 'L3'
  )
  const completePath = (
    connections: ElectricalConnection[],
    cycleDetected: boolean
  ): PhaseSupplyPath => {
    let expectedPhases: Array<'L1' | 'L2' | 'L3'> | null = null
    let phaseMismatch = false
    let missingPhaseData = false
    for (const connection of connections) {
      const phases = electricalPhases(connection)
      if (!phases.length) {
        missingPhaseData = true
        continue
      }
      if (expectedPhases && phases.some((phase) => !expectedPhases?.includes(phase))) {
        phaseMismatch = true
      }
      expectedPhases = phases
    }
    return {
      id: connections.map((connection) => connection.id).join('>'),
      connections,
      effectivePhases: expectedPhases ?? [],
      phaseMismatch,
      missingPhaseData,
      cycleDetected
    }
  }
  const walkPath = (
    connection: ElectricalConnection,
    path: ElectricalConnection[],
    visitedEndpoints: Set<string>
  ): PhaseSupplyPath[] => {
    const nextPath = [...path, connection]
    if (visitedEndpoints.has(connection.target.key)) {
      return [completePath(nextPath, true)]
    }
    const nextVisited = new Set(visitedEndpoints)
    nextVisited.add(connection.target.key)
    const nextConnections = outgoing.get(connection.target.key) ?? []
    if (!nextConnections.length) {
      return [completePath(nextPath, false)]
    }
    return nextConnections.flatMap((nextConnection) => (
      walkPath(nextConnection, nextPath, nextVisited)
    ))
  }
  const groupForPath = (path: PhaseSupplyPath): PhaseSupplyGroupKey => {
    if (path.effectivePhases.length === 1) return path.effectivePhases[0]
    if (path.effectivePhases.length > 1) return 'multi'
    return 'unassigned'
  }
  const definitions: Array<{ key: PhaseSupplyGroupKey; label: string }> = [
    { key: 'L1', label: 'L1' },
    { key: 'L2', label: 'L2' },
    { key: 'L3', label: 'L3' },
    { key: 'multi', label: 'Mehrphasig' },
    { key: 'unassigned', label: 'Nicht zugeordnet' }
  ]
  return topology.nodes
    .filter((node) => node.endpoint.device_type === 'phase_distribution_block')
    .map((block) => {
      const paths = (outgoing.get(block.endpoint.key) ?? []).flatMap((connection) => (
        walkPath(connection, [], new Set([block.endpoint.key]))
      ))
      return {
        block,
        groups: definitions.map((definition) => ({
          ...definition,
          paths: paths.filter((path) => groupForPath(path) === definition.key)
        })).filter((group) => group.paths.length)
      }
    })
    .filter((item) => item.groups.length)
}

export function endpointTitle(endpoint: ElectricalEndpoint): string {
  return [endpoint.name, endpoint.code, endpoint.type_name].filter(Boolean).join(' · ')
}

export function phaseLabel(phases: ElectricalPhase[]): string {
  return phases.length ? phases.join(' · ') : 'Phase unbekannt'
}

export function topologyEndpointKey(
  kind: ElectricalEndpointKind,
  id: string
): string {
  return `${kind}:${id}`
}

export function topologyNode(
  topology: ElectricalTopology,
  kind: ElectricalEndpointKind,
  id: string
): ElectricalTopologyNode | null {
  const key = topologyEndpointKey(kind, id)
  return topology.nodes.find((node) => node.endpoint.key === key) ?? null
}

export function incomingTopologyConnections(
  topology: ElectricalTopology,
  kind: ElectricalEndpointKind,
  id: string
): ElectricalConnection[] {
  const key = topologyEndpointKey(kind, id)
  return topology.connections
    .filter((connection) => connection.target.key === key)
    .sort((left, right) => left.source.name.localeCompare(right.source.name, 'de'))
}

export function incomingTopologyConnection(
  topology: ElectricalTopology,
  kind: ElectricalEndpointKind,
  id: string
): ElectricalConnection | null {
  return incomingTopologyConnections(topology, kind, id)[0] ?? null
}

export function topologyFocusLocation(
  kind: ElectricalEndpointKind,
  id: string,
  connected: boolean
) {
  const key = topologyEndpointKey(kind, id)
  return connected
    ? { path: '/electrical/topology', query: { focus: key } }
    : { path: '/electrical/topology', query: { connect: '1', target: key } }
}

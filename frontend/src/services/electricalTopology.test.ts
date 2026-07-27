import { describe, expect, it } from 'vitest'

import {
  incomingTopologyConnection,
  incomingTopologyConnections,
  phaseDistributionGroups,
  phaseConnectionCounts,
  topologyFocusLocation,
  topologyNode,
  topologyRows
} from './electricalTopology'
import type {
  ElectricalConnection,
  ElectricalEndpoint,
  ElectricalTopology,
  ElectricalTopologyNode
} from '../types/electrical'

function endpoint(key: string, name: string): ElectricalEndpoint {
  const [kind, id] = key.split(':') as ['asset' | 'circuit', string]
  return {
    key,
    kind,
    id,
    name,
    code: null,
    type_name: kind === 'asset' ? 'Asset' : 'Stromkreis',
    location_name: null,
    device_type: null,
    effective_phases: null,
    deleted_at: null
  }
}

function node(item: ElectricalEndpoint): ElectricalTopologyNode {
  return {
    endpoint: item,
    source_names: ['Grid'],
    incoming_phases: [],
    downstream_protective_device_count: 0,
    downstream_circuit_count: 0,
    downstream_asset_count: 0
  }
}

function connection(
  id: string,
  source: ElectricalEndpoint,
  target: ElectricalEndpoint,
  phases: Array<'L1' | 'L2' | 'L3'>
): ElectricalConnection {
  return {
    id,
    source,
    target,
    connection_type: 'wire',
    label: null,
    phases,
    effective_phases: phases,
    phase_warnings: [],
    cable_type: null,
    cores: null,
    cross_section_mm2: null,
    length_m: null,
    route: null,
    notes: null,
    created_at: '',
    updated_at: '',
    deleted_at: null
  }
}

describe('electrical topology presentation', () => {
  it('orders every endpoint below its incoming supply', () => {
    const grid = endpoint('asset:grid', 'Grid')
    const circuit = endpoint('circuit:circuit', 'Kitchen')
    const load = endpoint('asset:load', 'Dishwasher')
    const topology: ElectricalTopology = {
      nodes: [node(load), node(grid), node(circuit)],
      connections: [
        connection('one', grid, circuit, ['L1']),
        connection('two', circuit, load, ['L1'])
      ]
    }

    expect(topologyRows(topology).map((row) => [row.node.endpoint.name, row.depth]))
      .toEqual([['Grid', 0], ['Kitchen', 1], ['Dishwasher', 2]])
    expect(topologyRows(topology)[2]?.incomingConnection?.id).toBe('two')
  })

  it('counts phase-bearing connections independently', () => {
    const source = endpoint('asset:source', 'Source')
    const first = endpoint('asset:first', 'First')
    const second = endpoint('asset:second', 'Second')
    const topology: ElectricalTopology = {
      nodes: [node(source), node(first), node(second)],
      connections: [
        connection('one', source, first, ['L1', 'L2', 'L3']),
        connection('two', first, second, ['L2'])
      ]
    }
    expect(phaseConnectionCounts(topology)).toEqual({ L1: 1, L2: 2, L3: 1 })
    expect(topologyNode(topology, 'asset', 'second')?.endpoint.name).toBe('Second')
    expect(incomingTopologyConnection(topology, 'asset', 'second')?.id).toBe('two')
    expect(topologyFocusLocation('asset', 'second', true)).toEqual({
      path: '/electrical/topology', query: { focus: 'asset:second' }
    })
    expect(topologyFocusLocation('asset', 'new', false)).toEqual({
      path: '/electrical/topology', query: { connect: '1', target: 'asset:new' }
    })
  })
  it('keeps multiple incoming energy sources on one topology target', () => {
    const grid = endpoint('asset:grid', 'Grid')
    const pv = endpoint('asset:pv', 'PV inverter')
    const bus = endpoint('asset:bus', 'House bus')
    const topology: ElectricalTopology = {
      nodes: [node(grid), node(pv), node(bus)],
      connections: [
        connection('grid-bus', grid, bus, ['L1', 'L2', 'L3']),
        connection('pv-bus', pv, bus, ['L1', 'L2', 'L3'])
      ]
    }

    const row = topologyRows(topology).find((item) => item.node.endpoint.key === bus.key)
    expect(row?.incomingConnections.map((item) => item.id)).toEqual(['grid-bus', 'pv-bus'])
    expect(incomingTopologyConnections(topology, 'asset', 'bus').map((item) => item.id))
      .toEqual(['grid-bus', 'pv-bus'])
  })

  it('keeps complete downstream supply paths grouped by their effective phase', () => {
    const block: ElectricalEndpoint = {
      ...endpoint('asset:block', 'Phasenverteiler'),
      kind: 'cabinet_component',
      device_type: 'phase_distribution_block'
    }
    const rcd = endpoint('asset:rcd', 'FI 1')
    const l1Breaker = endpoint('asset:l1-breaker', 'Keller LS')
    const l1Circuit = endpoint('circuit:l1-circuit', 'Keller Stromkreis')
    const l1Asset = endpoint('asset:l1-asset', 'Keller Licht')
    const l2Breaker = endpoint('asset:l2-breaker', 'Küche LS')
    const pump = endpoint('asset:pump', 'Drehstrompumpe')
    const unknown = endpoint('asset:unknown', 'Ohne Phase')
    const topology: ElectricalTopology = {
      nodes: [
        node(block), node(rcd), node(l1Breaker), node(l1Circuit),
        node(l1Asset), node(l2Breaker), node(pump), node(unknown)
      ],
      connections: [
        connection('block-rcd', block, rcd, ['L1', 'L2', 'L3']),
        connection('block-pump', block, pump, ['L1', 'L2', 'L3']),
        connection('block-unknown', block, unknown, []),
        connection('rcd-l1', rcd, l1Breaker, ['L1']),
        connection('rcd-l2', rcd, l2Breaker, ['L2']),
        connection('l1-circuit', l1Breaker, l1Circuit, ['L1']),
        connection('l1-asset', l1Circuit, l1Asset, ['L1'])
      ]
    }

    const result = phaseDistributionGroups(topology)[0]
    expect(result?.groups.map((group) => group.key))
      .toEqual(['L1', 'L2', 'multi', 'unassigned'])
    expect(result?.groups.find((group) => group.key === 'L1')?.paths[0]?.connections
      .map((item) => item.id))
      .toEqual(['block-rcd', 'rcd-l1', 'l1-circuit', 'l1-asset'])
    expect(result?.groups.find((group) => group.key === 'L2')?.paths[0]?.connections
      .map((item) => item.id))
      .toEqual(['block-rcd', 'rcd-l2'])
    expect(result?.groups.find((group) => group.key === 'multi')?.paths[0]?.effectivePhases)
      .toEqual(['L1', 'L2', 'L3'])
    expect(result?.groups.find((group) => group.key === 'unassigned')?.paths[0]?.missingPhaseData)
      .toBe(true)
  })

  it('marks phase expansions and cycles instead of hiding invalid supply paths', () => {
    const block: ElectricalEndpoint = {
      ...endpoint('asset:block', 'Phasenverteiler'),
      kind: 'cabinet_component',
      device_type: 'phase_distribution_block'
    }
    const breaker = endpoint('asset:breaker', 'LS')
    const topology: ElectricalTopology = {
      nodes: [node(block), node(breaker)],
      connections: [
        connection('block-breaker', block, breaker, ['L1']),
        connection('breaker-block', breaker, block, ['L1', 'L2'])
      ]
    }
    const path = phaseDistributionGroups(topology)[0]?.groups[0]?.paths[0]

    expect(path?.connections.map((item) => item.id))
      .toEqual(['block-breaker', 'breaker-block'])
    expect(path?.phaseMismatch).toBe(true)
    expect(path?.cycleDetected).toBe(true)
  })

})

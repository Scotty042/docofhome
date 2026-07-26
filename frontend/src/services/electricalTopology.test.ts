import { describe, expect, it } from 'vitest'

import {
  incomingTopologyConnection,
  incomingTopologyConnections,
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

})

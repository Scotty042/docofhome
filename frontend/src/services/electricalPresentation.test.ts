import { describe, expect, it } from 'vitest'

import {
  busbarPhasePattern,
  eligibleParentDistributions,
  filterDistributionTree,
  flattenDistributionTree,
  groupProtectiveDevices,
  moduleBoardStyle,
  moduleDropConflict
} from './electricalPresentation'
import type {
  DistributionTreeNode,
  ProtectiveDevice,
  ProtectiveDeviceType
} from '../types/electrical'

function distribution(
  id: string,
  children: DistributionTreeNode[] = [],
  parentId: string | null = null
): DistributionTreeNode {
  return {
    id,
    asset_id: `asset-${id}`,
    role: 'distribution',
    created_at: '2026-07-21T12:00:00Z',
    updated_at: '2026-07-21T12:00:00Z',
    deleted_at: null,
    asset: {
      id: `asset-${id}`,
      name: `Asset ${id}`,
      jarvis_code: id.toUpperCase(),
      location_id: 'room',
      location_path: 'House / Electrical room',
      status: 'active',
      effective_module_width: null
    },
    parent_distribution_id: parentId,
    distribution_type: parentId ? 'sub' : 'main',
    layout_mode: 'rows',
    designation: id,
    display_name: id,
    rows: null,
    modules_per_row: null,
    description: null,
    notes: null,
    breadcrumbs: [],
    direct_subdistribution_count: children.length,
    direct_protective_device_count: 0,
    children
  }
}

function device(index: number, positioned = true): ProtectiveDevice {
  return {
    id: `device-${index}`,
    asset_id: `asset-${index}`,
    role: 'protective_device',
    created_at: '2026-07-21T12:00:00Z',
    updated_at: '2026-07-21T12:00:00Z',
    deleted_at: null,
    asset: {
      id: `asset-${index}`,
      name: `Device ${index}`,
      jarvis_code: `DEV-${index}`,
      location_id: 'room',
      location_path: 'House / Electrical room',
      status: 'active',
      effective_module_width: null
    },
    distribution_id: 'main',
    distribution_name: 'Main',
    area_id: null,
    area_name: null,
    device_type: (['fuse', 'rcd', 'mcb', 'rcbo', 'spd'][index % 5]) as ProtectiveDeviceType,
    row_number: positioned ? 1 : null,
    start_position: positioned ? index + 1 : null,
    module_width: positioned ? 1 : null,
    rated_current_a: null,
    residual_current_ma: null,
    characteristic: null,
    poles: null,
    breaking_capacity_ka: null,
    rcd_type: null,
    fuse_type: null,
    spd_type: null,
    assigned_rcd_id: null,
    assigned_rcd_name: null,
    neutral_rail_id: null,
    neutral_rail_name: null,
    effective_rcd_id: null,
    effective_rcd_name: null,
    effective_neutral_rail_id: null,
    effective_neutral_rail_name: null,
    busbar_component_id: null,
    busbar_component_name: null,
    calculated_phases: [],
    group_warnings: [],
    description: null,
    notes: null
  }
}

describe('electrical presentation', () => {

  it('repeats a three-phase busbar pattern from the selected start phase', () => {
    expect(busbarPhasePattern({
      phases: ['L1', 'L2', 'L3'],
      start_phase: 'L2',
      module_width: 7
    })).toEqual(['L2', 'L3', 'L1', 'L2', 'L3', 'L1', 'L2'])
  })

  it('uses only phases enabled on the busbar', () => {
    expect(busbarPhasePattern({
      phases: ['L1', 'L3'],
      start_phase: 'L3',
      module_width: 4
    })).toEqual(['L3', 'L1', 'L3', 'L1'])
  })
  it('flattens hierarchy and excludes the current distribution and all descendants as parents', () => {
    const grandchild = distribution('grandchild', [], 'child')
    const child = distribution('child', [grandchild], 'main')
    const roots = [distribution('main', [child]), distribution('other')]

    expect(flattenDistributionTree(roots).map(({ distribution: item, depth }) => (
      [item.id, depth]
    ))).toEqual([
      ['main', 0], ['child', 1], ['grandchild', 2], ['other', 0]
    ])
    expect(eligibleParentDistributions(roots, 'child').map(({ distribution: item }) => item.id))
      .toEqual(['main', 'other'])
  })

  it('keeps matching descendants with their hierarchy context', () => {
    const roots = [distribution('main', [distribution('workshop', [], 'main')])]
    const filtered = filterDistributionTree(roots, 'workshop', '')
    expect(filtered).toHaveLength(1)
    expect(filtered[0]?.children[0]?.id).toBe('workshop')
  })

  it('groups more than one hundred devices without dropping positioned or unknown entries', () => {
    const devices = Array.from({ length: 101 }, (_, index) => device(index, index < 100))
    const groups = groupProtectiveDevices(devices)
    expect(groups.flatMap((group) => group.devices)).toHaveLength(101)
    expect(groups.find((group) => group.row === 1)?.devices).toHaveLength(100)
    expect(groups.find((group) => group.row === null)?.devices[0]?.id).toBe('device-100')
  })

  it('validates module drops while allowing a device to move across its own position', () => {
    const moving = device(0)
    moving.start_position = 2
    moving.module_width = 2
    const occupied = device(1)
    occupied.start_position = 5
    occupied.module_width = 2

    expect(moduleDropConflict([moving, occupied], moving.id, 3, 2, 12)).toBeNull()
    expect(moduleDropConflict([moving, occupied], moving.id, 4, 2, 12))
      .toContain('Device 1')
    expect(moduleDropConflict([moving, occupied], moving.id, 12, 2, 12))
      .toContain('Modul 13')
  })

  it('keeps a twelve-module rail compact enough for a distribution field', () => {
    expect(moduleBoardStyle(12)).toEqual({
      gridTemplateColumns: 'repeat(12, minmax(34px, 1fr))',
      minWidth: '452px'
    })
  })
})

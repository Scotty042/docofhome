import { describe, expect, it } from 'vitest'

import {
  eligibleParentLocations,
  filterLocationTree,
  flattenLocationTree
} from './locationPresentation'
import type { Location, LocationTreeNode, LocationType } from '../types/locations'

function location(
  id: string,
  name: string,
  type: LocationType,
  path: string,
  breadcrumbs: Array<{ id: string, name: string, location_type: LocationType }>,
  children: LocationTreeNode[] = [],
  deletedAt: string | null = null
): LocationTreeNode {
  return {
    id,
    name,
    location_type: type,
    path,
    breadcrumbs,
    children,
    deleted_at: deletedAt,
    created_at: '2026-07-20T12:00:00Z',
    updated_at: '2026-07-20T12:00:00Z',
    description: null,
    parent_id: breadcrumbs.length > 1 ? breadcrumbs.at(-2)?.id ?? null : null,
    short_name: null,
    sort_order: null,
    notes: null,
    direct_asset_count: 0,
    descendant_asset_count: 0
  }
}

const rootCrumb = { id: 'root', name: 'House', location_type: 'building' as const }
const floorCrumb = { id: 'floor', name: 'Ground floor', location_type: 'floor' as const }
const room = location(
  'room', 'Kitchen', 'room', 'House / Ground floor / Kitchen',
  [rootCrumb, floorCrumb, { id: 'room', name: 'Kitchen', location_type: 'room' }]
)
const floor = location('floor', 'Ground floor', 'floor', 'House / Ground floor',
  [rootCrumb, floorCrumb], [room])
const root = location('root', 'House', 'building', 'House', [rootCrumb], [floor])

describe('location presentation', () => {
  it('keeps ancestors when a nested desktop tree result matches', () => {
    const filtered = filterLocationTree([root], 'Kitchen', 'room')
    expect(filtered).toHaveLength(1)
    expect(filtered[0].children[0].children[0].id).toBe('room')
  })

  it('flattens hierarchy with stable depth for mobile cards', () => {
    expect(flattenLocationTree([root]).map((entry) => [entry.location.id, entry.depth])).toEqual([
      ['root', 0], ['floor', 1], ['room', 2]
    ])
  })

  it('excludes the current node, descendants and archived entries from parents', () => {
    const archived = location('old', 'Old room', 'room', 'House / Old room', [
      rootCrumb, { id: 'old', name: 'Old room', location_type: 'room' }
    ], [], '2026-07-20T12:00:00Z')
    const parents = eligibleParentLocations(
      [root, floor, room, archived] as Location[],
      'floor'
    )
    expect(parents.map((entry) => entry.id)).toEqual(['root'])
  })

  it('keeps valid parents beyond the first 100 tree entries selectable', () => {
    const children = Array.from({ length: 125 }, (_, index) => {
      const id = `area-${index + 1}`
      const name = `Area ${String(index + 1).padStart(3, '0')}`
      return location(id, name, 'area', `House / ${name}`, [
        rootCrumb,
        { id, name, location_type: 'area' }
      ])
    })
    const largeRoot = location('root', 'House', 'building', 'House', [rootCrumb], children)
    const allLocations = flattenLocationTree([largeRoot]).map((entry) => entry.location)

    expect(allLocations).toHaveLength(126)
    expect(eligibleParentLocations(allLocations, 'area-1').map((entry) => entry.id))
      .toContain('area-125')
  })
})

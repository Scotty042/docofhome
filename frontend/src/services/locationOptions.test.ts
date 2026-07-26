import { describe, expect, it } from 'vitest'

import { flattenLocationTree, locationSelectItems } from './locationOptions'
import type { LocationTreeNode } from '../types/locations'

function node(
  id: string,
  name: string,
  sortOrder: number | null,
  children: LocationTreeNode[] = []
): LocationTreeNode {
  return {
    id,
    name,
    sort_order: sortOrder,
    children,
    path: name,
    location_type: children.length ? 'floor' : 'room',
    parent_id: null,
    description: null,
    short_name: null,
    notes: null,
    breadcrumbs: [],
    direct_asset_count: 0,
    descendant_asset_count: 0,
    created_at: '2026-07-23T00:00:00Z',
    updated_at: '2026-07-23T00:00:00Z',
    deleted_at: null
  }
}

describe('hierarchical location options', () => {
  it('keeps every floor together and sorts rooms inside the floor', () => {
    const basement = node('basement', 'Keller', 30, [node('workshop', 'Werkstatt', 1)])
    const ground = node('ground', 'Erdgeschoss', 10, [
      node('living', 'Wohnzimmer', 30),
      node('pantry', 'Speisekammer', 20),
      node('bedroom', 'Schlafzimmer', 10)
    ])
    const upper = node('upper', 'Oben', 20, [node('upper-bedroom', 'Schlafzimmer', 10)])

    expect(flattenLocationTree([basement, upper, ground]).map((item) => item.id)).toEqual([
      'ground', 'bedroom', 'pantry', 'living', 'upper', 'upper-bedroom', 'basement', 'workshop'
    ])
    expect(locationSelectItems([basement, upper, ground]).map((item) => item.depth)).toEqual([
      0, 1, 1, 1, 0, 1, 0, 1
    ])
  })
})

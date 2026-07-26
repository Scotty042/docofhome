import { describe, expect, it } from 'vitest'

import {
  filterSelectionCandidates,
  normalizeSelectedEntityIds,
  selectionDomains,
  toggleSelectedEntity
} from './homeAssistantSelection'
import type { HomeAssistantEntity } from '../types/homeAssistant'

function entity(index: number, domain = 'sensor'): HomeAssistantEntity {
  return {
    entity_id: `${domain}.entity_${index}`,
    name: `Entity ${index}`,
    domain,
    state: String(index),
    unit: null,
    device_class: null,
    icon: null,
    device_id: `device-${index % 3}`,
    device_name: `Device ${index % 3}`,
    area_id: null,
    area_name: index % 2 ? 'Kitchen' : 'Utility',
    platform: 'test',
    entity_category: null,
    last_changed: null,
    last_updated: null,
    available: true,
    disabled: false
  }
}

describe('Home Assistant entity selection presentation', () => {
  it('normalizes, deduplicates and stably sorts selected IDs', () => {
    expect(normalizeSelectedEntityIds([
      ' sensor.z ', 'light.a', 'sensor.z', '', ' light.b '
    ])).toEqual(['light.a', 'light.b', 'sensor.z'])
  })

  it('keeps selections across search and selected-only filters', () => {
    const entities = [entity(1), entity(2), entity(3, 'light')]
    const selectedIds = new Set(['sensor.entity_1', 'light.entity_3'])

    expect(filterSelectionCandidates(entities, {
      search: 'Kitchen', selectedIds
    }).map((item) => item.entity_id)).toEqual(['sensor.entity_1', 'light.entity_3'])
    expect(filterSelectionCandidates(entities, {
      domain: 'sensor', selectedOnly: true, selectedIds
    }).map((item) => item.entity_id)).toEqual(['sensor.entity_1'])
    expect(normalizeSelectedEntityIds(selectedIds)).toEqual([
      'light.entity_3', 'sensor.entity_1'
    ])
  })

  it('handles more than one thousand candidates without dropping entries', () => {
    const entities = Array.from({ length: 1501 }, (_, index) => entity(index))
    const filtered = filterSelectionCandidates(entities, {
      selectedIds: new Set(),
      search: 'Entity'
    })
    expect(filtered).toHaveLength(1501)
    expect(selectionDomains([...entities, entity(2000, 'light')])).toEqual(['light', 'sensor'])
  })

  it('toggles a new set without mutating the previous selection', () => {
    const previous = new Set(['sensor.entity_1'])
    const added = toggleSelectedEntity(previous, 'sensor.entity_2')
    const removed = toggleSelectedEntity(added, 'sensor.entity_1')

    expect([...previous]).toEqual(['sensor.entity_1'])
    expect(normalizeSelectedEntityIds(added)).toEqual([
      'sensor.entity_1', 'sensor.entity_2'
    ])
    expect([...removed]).toEqual(['sensor.entity_2'])
  })
})

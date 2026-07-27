import { describe, expect, it } from 'vitest'

import { buildHomeAssistantAssetDraft, suggestedLocationId } from './homeAssistantAssetDraft'
import type { AssetType } from '../types/assets'
import type { Location } from '../types/locations'
import type { HomeAssistantDevice } from '../types/homeAssistant'

const type = {
  id: 'type-1',
  name: 'Smart Home',
  code_prefix: 'SH',
  description: null,
  icon: null,
  module_width: null,
  breaker_characteristic: null,
  rated_current_a: null,
  coil_voltage_v: null,
  coil_voltage_type: null,
  contact_count: null,
  contact_type: null,
  created_at: '',
  updated_at: '',
  deleted_at: null
} satisfies AssetType
const location = { id: 'loc-1', name: 'Wohnzimmer', path: 'Haus / EG / Wohnzimmer', location_type: 'room', description: null, parent_id: null, short_name: null, sort_order: null, notes: null, breadcrumbs: [], direct_asset_count: 0, descendant_asset_count: 0, created_at: '', updated_at: '', deleted_at: null } satisfies Location
const device = { device_id: 'dev-1', name: 'Thermostat', manufacturer: 'Acme', model: 'T1', model_id: null, sw_version: '1.0', hw_version: null, serial_number: 'ABC', area_id: 'area-1', area_name: 'Wohnzimmer', entity_count: 2, disabled: false } satisfies HomeAssistantDevice

describe('Home Assistant asset draft', () => {
  it('prefills known metadata and location', () => {
    expect(suggestedLocationId('Wohnzimmer', [location])).toBe('loc-1')
    const draft = buildHomeAssistantAssetDraft('device', device, [type], [location])
    expect(draft.name).toBe('Thermostat')
    expect(draft.asset_type_id).toBe('type-1')
    expect(draft.location_id).toBe('loc-1')
    expect(draft.serial_number).toBe('ABC')
    expect(draft.description).toContain('Hersteller: Acme')
  })
})

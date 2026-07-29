import { describe, expect, it } from 'vitest'

import layout from './ElectricalDistributionLayoutPage.vue?raw'
import topology from './ElectricalTopologyPage.vue?raw'
import api from '../services/electricalApi.ts?raw'

describe('release 1.7.4.5 electrical cabinet fixes', () => {
  it('filters unplaced DIN assets and meters globally and by distribution location', () => {
    expect(api).toContain('allAssetPlacements')
    expect(api).toContain('allMeterPlacements')
    expect(api).toContain('loadAllProtectiveDevices')
    expect(layout).toContain('matchesCurrentDistributionLocation')
    expect(layout).toContain('allAssetPlacements.value.map')
    expect(layout).toContain('allMeterPlacements.value.map')
  })

  it('merges every active cabinet component into the topology endpoint selector', () => {
    expect(topology).toContain('loadCabinetComponentFallbackEndpoints')
    expect(topology).toContain('electricalApi.distributionTree()')
    expect(topology).toContain('electricalApi.cabinetComponents(distribution.id)')
    expect(topology).toContain('Phasenschiene / Kammschiene')
    expect(topology).toContain('merged.set(endpoint.key, endpoint)')
  })
})

import { describe, expect, it } from 'vitest'

import page from './ElectricalDistributionLayoutPage.vue?raw'

describe('FI/RCD DIN asset selection', () => {
  it('offers current DIN asset placements and persists a dedicated asset reference', () => {
    expect(page).toContain('placement.is_rcd === true')
    expect(page).toContain('linkedRcdSelection')
    expect(page).toContain('linked_rcd_asset_id')
    expect(page).toContain('item-value="value"')
  })
})

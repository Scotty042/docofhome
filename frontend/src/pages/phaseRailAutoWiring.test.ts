import page from './ElectricalDistributionLayoutPage.vue?raw'
import { describe, expect, it } from 'vitest'

describe('phase rail automatic wiring', () => {
  it('connects every fully covered DIN device and keeps FI assignment optional', () => {
    expect(page).toContain('Zugehöriger FI/RCD (optional)')
    expect(page).toContain('verbindet automatisch jedes vollständig überdeckte DIN-Gerät')
    expect(page).toContain('vierpoligen FI')
    expect(page).toContain('der vierte Pol bleibt für N frei')
    expect(page).toContain('v-if="!automaticEditingConnection"')
    expect(page).toContain('@click="archiveDetailDevice"')
    expect(page).toContain('@click="archiveDetailComponent"')
    expect(page).toContain('Das DIN-Gerät würde nur teilweise von der Phasen-/Kammschiene überdeckt.')
    expect(page).toContain('automatisch mit ${savedComponent.automatic_connection_count} DIN-Gerät(en) verbunden')
    expect(page).toContain('visibleProtectiveDeviceIds()')
    expect(page).toContain('visibleDinAssetIds()')
    expect(page).toContain('visible_asset_ids: visibleDinAssetIds()')
    expect(page).toContain('electricalApi.synchronizePhaseRailContacts')
    expect(page).toContain('(distribution.value?.protective_devices ?? []).map((device) => device.id)')
    expect(page).toContain('assetPlacements.value.map((placement) => placement.asset_id)')
    expect(page).toContain('Automatische Kontakte')
    expect(page).toContain('v-model="cabinetComponentDialog" max-width="720" scrollable')
    expect(page).not.toContain('noch keinem FI/RCD zugeordnet')
  })
})

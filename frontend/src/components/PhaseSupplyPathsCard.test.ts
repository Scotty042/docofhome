import { describe, expect, it } from 'vitest'

import card from './PhaseSupplyPathsCard.vue?raw'
import layout from '../pages/ElectricalDistributionLayoutPage.vue?raw'
import topology from '../pages/ElectricalTopologyPage.vue?raw'

describe('phase supply path presentation', () => {
  it('shows ordered paths, phase conductors and documentation warnings', () => {
    expect(card).toContain('Vollständige Reihenfolge ab Phasenverteilerblock')
    expect(card).toContain('v-for="connection in path.connections"')
    expect(card).toContain('v-for="phase in connection.effective_phases"')
    expect(card).toContain('Phasenwechsel oder Phasenerweiterung')
    expect(card).toContain('Zyklischer Versorgungsweg erkannt')
    expect(card).toContain('<v-expansion-panels multiple')
  })

  it('integrates the phase paths into topology and cabinet views', () => {
    expect(topology).toContain('<PhaseSupplyPathsCard')
    expect(layout).toContain('title="Versorgungswege im Zählerschrank"')
    expect(layout).toContain('Phasenverteiler ohne dokumentierte Abgänge')
    expect(layout).toContain('phaseDistributionGroups(topology.value)')
  })
})

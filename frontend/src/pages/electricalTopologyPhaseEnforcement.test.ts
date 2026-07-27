import topologyPage from './ElectricalTopologyPage.vue?raw'
import { describe, expect, it } from 'vitest'

// This source-contract test deliberately avoids mounting Vuetify. It protects the
// phase-enforcement wiring between the endpoint metadata, dialog and save path.
describe('electrical topology phase enforcement', () => {
  it('locks the line phase to the protective device phase calculated from the rail', () => {
    expect(topologyPage).toContain('forcedLinePhases')
    expect(topologyPage).toContain('endpoint.kind === \'protective_device\'')
    expect(topologyPage).toContain('Durch Sammel-/Phasenschiene fest vorgegeben')
    expect(topologyPage).toContain('updateConnectionPhases')
    expect(topologyPage).toContain('L1/L2/L3 werden aus Position und Startphase der Schiene berechnet')
  })

  it('shows save errors inside the open connection dialog', () => {
    expect(topologyPage).toContain('const dialogError = ref<string | null>(null)')
    expect(topologyPage).toContain('v-if="dialogError"')
    expect(topologyPage).toContain('{{ dialogError }}')
  })
})

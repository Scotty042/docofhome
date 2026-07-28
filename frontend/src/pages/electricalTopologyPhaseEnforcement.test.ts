import topologyPage from './ElectricalTopologyPage.vue?raw'
import distributionLayoutPage from './ElectricalDistributionLayoutPage.vue?raw'
import { describe, expect, it } from 'vitest'

// Source-contract tests deliberately avoid mounting Vuetify. They protect the
// phase-enforcement wiring between endpoint metadata, dialog and save path.
describe('electrical topology phase enforcement', () => {
  it('recognizes direct phase-rail connections and locks the line phase', () => {
    expect(topologyPage).toContain('directPhaseRailConnection')
    expect(topologyPage).toContain("source.device_type === 'phase_rail'")
    expect(topologyPage).toContain("target.kind === 'protective_device'")
    expect(topologyPage).toContain('Fest vorgegebene Außenleiterphase')
    expect(topologyPage).toContain('Berechnet aus Startphase und TE-Position der Phasenschiene')
  })

  it('does not render selectable L1/L2/L3 options for a locked connection', () => {
    expect(topologyPage).toContain('v-if="phaseLockActive"')
    expect(topologyPage).toContain('label="Zusätzliche Leiter"')
    expect(topologyPage).toContain("item.value === 'N' || item.value === 'PE'")
    expect(topologyPage).toContain(':disabled="!forcedLinePhases.length"')
    expect(topologyPage).toContain(':disabled="forcedPhaseConflict"')
  })

  it('uses effective phases when an existing connection is opened', () => {
    expect(topologyPage).toContain('connection.effective_phases.length')
    expect(topologyPage).toContain('editedLockedLinePhases')
    expect(topologyPage).toContain('editedEffectiveLinePhases')
    expect(topologyPage).toContain('editingConnectionMatchesSelection')
  })

  it('shows topology phases only from effective phases', () => {
    expect(topologyPage).toContain('return connection.effective_phases')
  })

  it('distinguishes general busbars from positional phase/comb rails', () => {
    expect(distributionLayoutPage).toContain('Sammelschiene (allgemeiner Verteiler)')
    expect(distributionLayoutPage).toContain('Phasenschiene / Kammschiene (Sicherungsreihe)')
    expect(distributionLayoutPage).toContain('Eine Sammelschiene ist ein allgemeiner Verteilpunkt')
    expect(distributionLayoutPage).toContain("component.component_type === 'phase_rail'")
  })

  it('shows save errors inside the open connection dialog', () => {
    expect(topologyPage).toContain('const dialogError = ref<string | null>(null)')
    expect(topologyPage).toContain('v-if="dialogError"')
    expect(topologyPage).toContain('{{ dialogError }}')
  })

  it('keeps N and PE rail wiring separate from line-phase enforcement', () => {
    expect(topologyPage).toContain('restrictedEndpointConductors')
    expect(topologyPage).toContain("endpoint.device_type === 'neutral_rail'")
    expect(topologyPage).toContain("endpoint.device_type === 'protective_earth_rail'")
    expect(topologyPage).toContain('restrictedConnectionConductors')
    expect(topologyPage).toContain('Der Leiter wird durch die ausgewählte N- oder PE-Schiene festgelegt.')
  })

  it('allows a separate N or PE path to a target with an existing line-phase feed', () => {
    expect(topologyPage).toContain('auxiliaryConductorOnly')
    expect(topologyPage).toContain('linePhaseBindingRequested')
    expect(topologyPage).toContain('requestedLinePhases.length')
    expect(topologyPage).toContain('Außenleiter anderer Einspeisungen werden nicht auf diesen Leiterweg übertragen.')
  })
})

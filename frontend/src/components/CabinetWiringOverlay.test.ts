import { describe, expect, it } from 'vitest'

import overlay from './CabinetWiringOverlay.vue?raw'
import layout from '../pages/ElectricalDistributionLayoutPage.vue?raw'

describe('cabinet visual wiring mode', () => {
  it('draws stored main topology connections on positioned cabinet endpoints', () => {
    expect(overlay).toContain('data-electrical-endpoint-key')
    expect(overlay).toContain('visibleConnections')
    expect(overlay).toContain('orthogonalPath')
    expect(layout).toContain('<CabinetWiringOverlay')
    expect(layout).toContain("viewMode === 'wiring'")
  })

  it('omits only the branch to an individual circuit while keeping manual breaker feeds', () => {
    expect(overlay).toContain('isIndividualCircuitBranch')
    expect(overlay).toContain("connection.source.kind === 'circuit'")
    expect(overlay).toContain("connection.target.kind === 'circuit'")
    expect(overlay).toContain('Eine manuelle Einspeisung zu einem LS/MCB/RCBO')
    expect(overlay).not.toContain('individualCircuitEndpointKeys')
    expect(overlay).not.toContain("new Set(['mcb', 'rcbo'])")
    expect(layout).toContain('Abgänge von LS-/RCBO-Geräten')
  })

  it('routes freely inside the cabinet and separates every conductor', () => {
    expect(overlay).toContain('function connectionPortOffsets(')
    expect(overlay).toContain('function laneAssignments(')
    expect(overlay).toContain('function choosePort(')
    expect(overlay).toContain('function orthogonalPath(')
    expect(overlay).toContain('const conductorOffset = (phaseIndex - center) * 8')
    expect(overlay).toContain('const trackY = baseMidY + lane + conductorOffset')
    expect(overlay).toContain('Die Wege dürfen innerhalb des Schrankbilds verlaufen')
    expect(overlay).not.toContain('crossSectionOrthogonalPath')
    expect(overlay).not.toContain('upper card borders as a shared trunk')
    expect(layout).toContain('innerhalb der Schrankdarstellung')
    expect(layout).toContain('festem Abstand')
  })

  it('bundles duplicate main edges and uses standard external symbols', () => {
    expect(overlay).toContain('Mehrere Datensätze zwischen denselben Hauptkomponenten')
    expect(overlay).toContain('isAutomaticBusbarContact')
    expect(overlay).toContain("endpoint.kind === 'grid_connection'")
    expect(overlay).toContain("if (endpoint.kind === 'distribution') return 'square'")
    expect(overlay).toContain('Hausanschluss')
  })


  it('places the grid connection at the bottom and uses the real meter card anchor', () => {
    expect(overlay).toContain("entry.endpoint.kind === 'grid_connection'")
    expect(overlay).toContain('height.value - verticalPadding')
    expect(layout).toContain('meterPlacementEndpointKey(placement)')
    expect(layout).toContain('meter-placement-card')
  })

  it('shows separate input and output ports for FI/RCD flow-through devices', () => {
    expect(overlay).toContain('flowThrough')
    expect(overlay).toContain("label: 'IN'")
    expect(overlay).toContain("label: 'OUT'")
    expect(overlay).toContain("role === 'target' ? -horizontalOffset : horizontalOffset")
    expect(layout).toContain('data-electrical-flow-through')
  })

  it('keeps N and PE rail cards compact without inline wiring summaries', () => {
    expect(layout).not.toContain('import ElectricalWiringSummary')
    expect(layout).not.toContain('<ElectricalWiringSummary')
    expect(layout).toContain("['neutral_rail', 'protective_earth_rail'].includes(area.area_type)")
  })
})

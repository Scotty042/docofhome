import source from './ElectricalWiringSummary.vue?raw'
import { describe, expect, it } from 'vitest'

describe('electrical wiring summary with multiple feeds', () => {
  it('uses all incoming connections and displays their count', () => {
    expect(source).toContain('incomingTopologyConnections')
    expect(source).toContain('incomingConnections.length > 1')
    expect(source).toContain('dokumentierte Einspeisungen')
    expect(source).toContain('new Set(incomingConnections.value.flatMap')
  })
})

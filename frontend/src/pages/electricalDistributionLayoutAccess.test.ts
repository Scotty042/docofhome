import detail from './ElectricalDistributionDetailPage.vue?raw'
import editor from './ElectricalDistributionEditorPage.vue?raw'
import layout from './ElectricalDistributionLayoutPage.vue?raw'
import { describe, expect, it } from 'vitest'

describe('electrical distribution layout access', () => {
  it('exposes the cabinet layout for every distribution and supports subdistribution sections', () => {
    expect(detail).toContain('Schrankaufteilung')
    expect(detail).toContain('`/electrical/distributions/${distribution.id}/layout`')
    expect(editor).toContain('Felder und Bereiche kann für Haupt- und Unterverteilungen')
    expect(layout).toContain('Einfache Reihenaufteilung')
    expect(layout).toContain('Noch keine Schrankaufteilung angelegt')
  })
})

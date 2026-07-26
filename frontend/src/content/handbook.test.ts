import { describe, expect, it } from 'vitest'

import {
  filterHandbookEntries,
  glossaryLetters,
  handbookEntries,
  handbookSections,
  sortGlossaryEntries
} from './handbook'

describe('static handbook and glossary content', () => {
  it('contains the central private-home terms', () => {
    const terms = new Set(handbookEntries.map((entry) => entry.term))
    for (const term of [
      'Asset',
      'Sammelschiene',
      'Phasenschiene / Kammschiene',
      'FI / RCD',
      'N-Schiene',
      'VLAN',
      'DHCP',
      'Switch-Port',
      'Zählerstand'
    ]) {
      expect(terms.has(term), term).toBe(true)
    }
    expect(handbookSections.map((section) => section.id)).toEqual([
      'einstieg',
      'assets-und-produkte',
      'elektro',
      'netzwerk',
      'verbrauch-und-zaehler',
      'home-assistant',
      'bilder-und-dokumente',
      'backup-und-betrieb'
    ])
  })

  it('searches term, description, alias and category without internet or API data', () => {
    expect(filterHandbookEntries(handbookEntries, 'Sammelschiene', 'all')
      .some((entry) => entry.id === 'sammelschiene')).toBe(true)
    expect(filterHandbookEntries(handbookEntries, 'Kammschiene', 'all')
      .some((entry) => entry.id === 'phasenschiene')).toBe(true)
    expect(filterHandbookEntries(handbookEntries, 'automatische Vergabe', 'network')
      .some((entry) => entry.id === 'dhcp')).toBe(true)
    expect(filterHandbookEntries(handbookEntries, '', 'consumption')
      .every((entry) => entry.category === 'consumption')).toBe(true)
    expect(filterHandbookEntries(handbookEntries, 'VLAN', 'electrical')).toEqual([])
  })

  it('provides a sorted alphabetic glossary with jump letters', () => {
    const sorted = sortGlossaryEntries(handbookEntries)
    expect(sorted[0]?.term).toBe('Abgang')
    expect(glossaryLetters(sorted)).toContain('A')
    expect(glossaryLetters(sorted)).toContain('Z')
  })
})

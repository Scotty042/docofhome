import { describe, expect, it } from 'vitest'

import {
  folderPathChain,
  isEqualOrDescendantPath,
  isInvalidMoveDestination
} from './documentFolderTree'

describe('document folder tree', () => {
  it('builds the root-to-folder chain for lazy tree expansion', () => {
    expect(folderPathChain('')).toEqual([''])
    expect(folderPathChain('Rechnungen/2026/Energie')).toEqual([
      '',
      'Rechnungen',
      'Rechnungen/2026',
      'Rechnungen/2026/Energie'
    ])
  })

  it('detects equal and descendant paths on folder boundaries', () => {
    expect(isEqualOrDescendantPath('Anlagen', 'Anlagen')).toBe(true)
    expect(isEqualOrDescendantPath('Anlagen/PV', 'Anlagen')).toBe(true)
    expect(isEqualOrDescendantPath('Anlagenbau', 'Anlagen')).toBe(false)
    expect(isEqualOrDescendantPath('', 'Anlagen')).toBe(false)
  })

  it('prevents moving folders into themselves or their descendants only', () => {
    expect(isInvalidMoveDestination('Anlagen', 'folder', 'Anlagen')).toBe(true)
    expect(isInvalidMoveDestination('Anlagen', 'folder', 'Anlagen/PV')).toBe(true)
    expect(isInvalidMoveDestination('Anlagen', 'folder', 'Rechnungen')).toBe(false)
    expect(isInvalidMoveDestination('Anlagen/Plan.pdf', 'file', 'Anlagen')).toBe(false)
  })
})

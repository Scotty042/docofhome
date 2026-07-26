import source from './NetworkPage.vue?raw'
import { describe, expect, it } from 'vitest'

describe('network page resilience', () => {
  it('keeps fulfilled endpoint data when another request fails', () => {
    expect(source).toContain('Promise.allSettled')
    expect(source).toContain("if (deviceData.status === 'fulfilled')")
    expect(source).toContain('Ein Teil der Netzwerkdaten konnte nicht geladen werden.')
  })
})

import { describe, expect, it } from 'vitest'

import { resolveSetupNavigation } from './setupNavigation'

describe('setup navigation', () => {
  it('opens an unavailable state instead of setup when the status request fails', () => {
    expect(resolveSetupNavigation('settings', '/settings', 'unavailable')).toEqual({
      name: 'unavailable',
      query: { from: '/settings' }
    })
  })

  it('does not redirect recursively while the unavailable page is open', () => {
    expect(resolveSetupNavigation('unavailable', '/unavailable', 'unavailable')).toBe(true)
  })

  it('opens setup only after a successful incomplete status', () => {
    expect(resolveSetupNavigation('dashboard', '/', false)).toEqual({ name: 'setup' })
  })

  it('keeps completed installations out of setup', () => {
    expect(resolveSetupNavigation('setup', '/setup', true)).toEqual({ name: 'dashboard' })
  })
})

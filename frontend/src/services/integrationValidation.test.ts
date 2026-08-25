import { describe, expect, it } from 'vitest'

import { validateIntegrationUrl } from './integrationValidation'

describe('integration URL validation', () => {
  it('accepts an HTTPS server URL without userinfo', () => {
    expect(validateIntegrationUrl('https://service.example.test', true)).toBe(true)
  })

  it.each([
    'https://user@service.example.test',
    'https://user:password@service.example.test'
  ])('rejects credentials embedded in %s', (url) => {
    expect(validateIntegrationUrl(url, true)).toContain('Zugangsdatenfelder')
  })

  it('allows an empty URL for a disabled integration', () => {
    expect(validateIntegrationUrl(null, false)).toBe(true)
  })
})

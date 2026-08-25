import { describe, expect, it } from 'vitest'

import { APP_NAME, APP_SLOGAN, APP_SUPPORT_LABEL } from './branding'

describe('branding metadata', () => {
  it('uses the final DocOfHome product identity', () => {
    expect(APP_NAME).toBe('DocOfHome')
    expect(APP_SLOGAN).toBe('Know your home.')
    expect(APP_SUPPORT_LABEL).toBe('DocOfHome unterstützen ☕')
  })
})

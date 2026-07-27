import source from './ProductImageField.vue?raw'
import { describe, expect, it } from 'vitest'

describe('product image provider workflow', () => {
  it('enforces provider selection through the backend', () => {
    expect(source).toContain('assetApi.searchProductImages')
    expect(source).toContain('assetApi.importProductImage')
    expect(source).toContain('in den Einstellungen aktivierten Quellen')
    expect(source).not.toContain('searchWikimediaInBrowser')
    expect(source).not.toContain('downloadWikimediaImageInBrowser')
  })
})

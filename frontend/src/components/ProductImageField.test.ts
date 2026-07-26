import source from './ProductImageField.vue?raw'
import { describe, expect, it } from 'vitest'

describe('product image browser fallback workflow', () => {
  it('prefers the backend and locally uploads a browser-downloaded fallback image', () => {
    const backendSearch = source.indexOf('assetApi.searchProductImages')
    const browserSearch = source.indexOf('searchWikimediaInBrowser(query')

    expect(backendSearch).toBeGreaterThan(-1)
    expect(browserSearch).toBeGreaterThan(backendSearch)
    expect(source).toContain('downloadWikimediaImageInBrowser')
    expect(source).toContain('assetApi.uploadProductImage(file, signal)')
    expect(source).toContain('Browser-Suche nicht erreichbar')
  })
})

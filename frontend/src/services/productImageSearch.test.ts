import { afterEach, describe, expect, it, vi } from 'vitest'

import { downloadWikimediaImageInBrowser, searchWikimediaInBrowser } from './productImageSearch'

const item = {
  title: 'Testgerät',
  thumbnail_url: 'https://upload.wikimedia.org/thumb/test.jpg',
  source_url: 'https://commons.wikimedia.org/wiki/File:Test.jpg',
  image_url: 'https://upload.wikimedia.org/test.jpg',
  license_name: 'CC BY-SA 4.0',
  author: 'Autor'
}

afterEach(() => vi.restoreAllMocks())

describe('browser Wikimedia fallback', () => {
  it('uses the official CORS origin parameter and keeps only approved hosts', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      query: {
        pages: [
          { title: 'File:Test.jpg', imageinfo: [{ url: item.image_url, thumburl: item.thumbnail_url, descriptionurl: item.source_url, extmetadata: { LicenseShortName: { value: 'CC BY-SA 4.0' } } }] },
          { title: 'File:Evil.jpg', imageinfo: [{ url: 'https://example.org/evil.jpg', thumburl: 'https://example.org/evil.jpg', descriptionurl: 'https://example.org' }] }
        ]
      }
    }), { status: 200, headers: { 'content-type': 'application/json' } }))

    const result = await searchWikimediaInBrowser('Testgerät')

    expect(result).toHaveLength(1)
    expect(result[0].image_url).toBe(item.image_url)
    const requested = new URL(String(fetchMock.mock.calls[0][0]))
    expect(requested.searchParams.get('origin')).toBe('*')
  })

  it('downloads an approved image for local upload', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(new Blob(['image'], { type: 'image/jpeg' }), {
      status: 200,
      headers: { 'content-type': 'image/jpeg' }
    }))

    const file = await downloadWikimediaImageInBrowser(item)

    expect(file.type).toBe('image/jpeg')
    expect(file.name).toBe('wikimedia-product-image.jpg')
  })

  it('rejects non-Wikimedia image hosts', async () => {
    await expect(downloadWikimediaImageInBrowser({ ...item, image_url: 'https://example.org/test.jpg' }))
      .rejects.toThrow('freigegebenen Wikimedia-Host')
  })

  it('returns an empty list when Wikimedia has no matching pages', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      query: { pages: [] }
    }), { status: 200, headers: { 'content-type': 'application/json' } }))

    await expect(searchWikimediaInBrowser('nicht vorhanden')).resolves.toEqual([])
  })

  it('reports a complete external search outage', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('unavailable', { status: 503 }))

    await expect(searchWikimediaInBrowser('ABB S201'))
      .rejects.toThrow('HTTP 503')
  })
})

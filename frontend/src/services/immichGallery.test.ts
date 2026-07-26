import { describe, expect, it } from 'vitest'

import {
  adjacentImmichImage,
  albumImageQuery,
  formatImmichDimensions,
  formatImmichTimestamp,
  linkedImmichAssetIds,
  prependImmichLink,
  selectedImmichAlbumId
} from './immichGallery'
import type { ImmichAssetLink, ImmichImage } from '../types/immich'

function link(id: string, externalId: string): ImmichAssetLink {
  return {
    id,
    asset_id: 'asset-id',
    immich_asset_id: externalId,
    original_file_name: `${externalId}.jpg`,
    file_created_at: '2026-07-20T10:30:00Z',
    width: 1600,
    height: 1200,
    is_favorite: false,
    thumbnail_url: `/api/v1/immich/assets/${externalId}/thumbnail`,
    created_at: '2026-07-21T10:00:00Z',
    updated_at: '2026-07-21T10:00:00Z'
  }
}

function image(id: string, width: number | null = 1600, height: number | null = 1200): ImmichImage {
  return {
    immich_asset_id: id,
    original_file_name: `${id}.jpg`,
    file_created_at: '2026-07-20T10:30:00Z',
    width,
    height,
    is_favorite: false,
    thumbnail_url: `/api/v1/immich/assets/${id}/thumbnail`
  }
}

describe('Immich gallery presentation', () => {
  it('uses the persisted Immich album and exposes every page to asset pickers', () => {
    const configuration = {
      installation_name: 'Home',
      language: 'de' as const,
      timezone: 'Europe/Berlin',
      theme: 'dark' as const,
      online_product_image_search_enabled: false,
      setup_completed_at: '2026-07-22T10:00:00Z',
      integrations: [{
        kind: 'immich' as const,
        enabled: true,
        base_url: 'https://immich.example.test',
        account: null,
        secret_configured: true,
        selected_album_id: '00000000-0000-4000-8000-000000000001',
        document_root: null
      }]
    }

    const albumId = selectedImmichAlbumId(configuration)

    expect(albumId).toBe('00000000-0000-4000-8000-000000000001')
    expect(albumImageQuery(albumId!, 3, ' panel ')).toEqual({
      page: 3,
      page_size: 48,
      album_id: albumId,
      search: 'panel'
    })
  })

  it('keeps linked IDs independently of replacing remote candidate pages', () => {
    const links = [link('one', 'image-1'), link('two', 'image-2')]
    let remotePage = ['image-1', 'image-3']
    const linkedIds = linkedImmichAssetIds(links)

    remotePage = ['image-4', 'image-2']

    expect(linkedIds.has(remotePage[0])).toBe(false)
    expect(linkedIds.has(remotePage[1])).toBe(true)
  })

  it('prepends a created link without duplicating its local identity', () => {
    const created = link('two', 'image-2')
    expect(prependImmichLink([link('one', 'image-1'), created], created)).toEqual([
      created,
      link('one', 'image-1')
    ])
  })

  it('provides understandable metadata fallbacks', () => {
    expect(formatImmichTimestamp(null)).toBe('Aufnahmedatum unbekannt')
    expect(formatImmichTimestamp('2026-07-20T10:30:00Z')).toContain('2026')
    expect(formatImmichDimensions(image('known'))).toBe('1600 × 1200 px')
    expect(formatImmichDimensions(image('unknown', null, null))).toBe('Abmessungen unbekannt')
  })

  it('navigates only inside the currently loaded page', () => {
    const images = [image('one'), image('two'), image('three')]

    expect(adjacentImmichImage(images, 'two', -1)?.immich_asset_id).toBe('one')
    expect(adjacentImmichImage(images, 'two', 1)?.immich_asset_id).toBe('three')
    expect(adjacentImmichImage(images, 'one', -1)).toBeNull()
    expect(adjacentImmichImage(images, 'three', 1)).toBeNull()
    expect(adjacentImmichImage(images, 'missing', 1)).toBeNull()
  })
})

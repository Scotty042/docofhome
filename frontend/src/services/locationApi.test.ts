import { afterEach, describe, expect, it, vi } from 'vitest'

import { locationApi, LocationApiError } from './locationApi'
import { createEmptyLocation } from '../types/locations'

afterEach(() => vi.unstubAllGlobals())

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('location API', () => {
  it('serializes path search, type filters, sorting and pagination', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      items: [], total: 0, page: 2, page_size: 10, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await locationApi.list({
      page: 2,
      page_size: 10,
      search: 'House / Kitchen',
      location_type: 'room',
      sort_by: 'path',
      sort_order: 'desc',
      include_deleted: true
    })

    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain('/api/v1/locations?')
    expect(url).toContain('search=House+%2F+Kitchen')
    expect(url).toContain('location_type=room')
    expect(url).toContain('sort_by=path')
    expect(url).toContain('include_deleted=true')
  })

  it('loads the tree and sends complete create and move payloads', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({ id: 'room-id' }, 201))
      .mockResolvedValueOnce(jsonResponse({ id: 'room-id', parent_id: 'floor-id' }))
    vi.stubGlobal('fetch', fetchMock)
    const payload = createEmptyLocation('root-id')
    payload.name = 'Kitchen'
    payload.location_type = 'room'

    await locationApi.tree()
    await locationApi.create(payload)
    await locationApi.move('room-id', 'floor-id')

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/locations/tree')
    expect(JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)).toEqual(payload)
    expect(JSON.parse((fetchMock.mock.calls[2][1] as RequestInit).body as string)).toEqual({
      parent_id: 'floor-id'
    })
  })

  it('surfaces domain conflicts from the backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(
      { detail: 'Location has active child locations' }, 409
    )))

    await expect(locationApi.remove('floor-id')).rejects.toEqual(
      new LocationApiError('Location has active child locations', 409)
    )
  })
})

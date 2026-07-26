import { afterEach, describe, expect, it, vi } from 'vitest'

import { isSafeLocalRoute, sanitizeSearchResponse, searchApi, SearchApiError } from './searchApi'
import type { SearchResponse } from '../types/search'

const response: SearchResponse = {
  query: 'test',
  total: 2,
  groups: [
    {
      result_type: 'asset',
      label: 'Assets',
      total: 2,
      results: [
        {
          result_type: 'asset',
          id: '1',
          title: 'Sicher',
          subtitle: 'A-001',
          description: null,
          route: '/assets/1',
          archived: false,
          matched_fields: ['Name']
        },
        {
          result_type: 'asset',
          id: '2',
          title: 'Unsicher',
          subtitle: 'A-002',
          description: null,
          route: 'https://example.invalid/assets/2',
          archived: false,
          matched_fields: ['Name']
        }
      ]
    }
  ]
}

afterEach(() => vi.unstubAllGlobals())

describe('search route safety', () => {
  it('accepts only local absolute app paths', () => {
    expect(isSafeLocalRoute('/assets/123')).toBe(true)
    expect(isSafeLocalRoute('/assets/123?archived=1')).toBe(true)
    expect(isSafeLocalRoute('https://example.invalid')).toBe(false)
    expect(isSafeLocalRoute('//example.invalid/assets/1')).toBe(false)
    expect(isSafeLocalRoute('/\\example.invalid')).toBe(false)
    expect(isSafeLocalRoute('/http:example.invalid')).toBe(false)
  })

  it('removes unsafe results and recalculates counts', () => {
    const sanitized = sanitizeSearchResponse(response)
    expect(sanitized.total).toBe(1)
    expect(sanitized.groups[0]?.total).toBe(1)
    expect(sanitized.groups[0]?.results[0]?.route).toBe('/assets/1')
  })
})

describe('search API', () => {
  it('serializes the bounded local search request', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await searchApi.search('  Keller  ', {
      limitPerType: 7,
      includeArchived: true
    })

    expect(result.total).toBe(1)
    const url = String(fetchMock.mock.calls[0]?.[0])
    expect(url).toContain('/api/v1/search?')
    expect(url).toContain('q=++Keller++')
    expect(url).toContain('limit_per_type=7')
    expect(url).toContain('include_archived=true')
  })

  it('returns a readable API error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: 'Suchtext ist zu kurz' }),
      { status: 422, headers: { 'Content-Type': 'application/json' } }
    )))

    await expect(searchApi.search('x')).rejects.toEqual(
      new SearchApiError('Suchtext ist zu kurz', 422)
    )
  })
})

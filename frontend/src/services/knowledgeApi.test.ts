import { afterEach, describe, expect, it, vi } from 'vitest'

import { knowledgeApi } from './knowledgeApi'

const wikiPage = {
  id: '00000000-0000-4000-8000-000000000001',
  parent_id: null,
  title: 'Heizung',
  slug: 'heizung',
  content: 'Grundlagen',
  path: 'Heizung',
  depth: 0,
  sort_order: 0,
  archived: false,
  created_at: '2026-07-22T12:00:00Z',
  updated_at: '2026-07-22T12:00:00Z'
}

afterEach(() => vi.unstubAllGlobals())

describe('knowledge API', () => {
  it('encodes Wiki searches and keeps requests on the local API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([wikiPage]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await knowledgeApi.wikiPages(' Wärmepumpe & Filter ')

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      '/api/v1/wiki/pages?search=W%C3%A4rmepumpe+%26+Filter'
    )
  })

  it('sends stable local target identifiers for notes', async () => {
    const response = {
      id: '00000000-0000-4000-8000-000000000002',
      target_type: 'asset',
      target_id: '00000000-0000-4000-8000-000000000003',
      content: 'Filter liegt im Keller.',
      created_at: '2026-07-22T12:00:00Z',
      updated_at: '2026-07-22T12:00:00Z'
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), {
      status: 201,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await knowledgeApi.createNote('asset', response.target_id, response.content)

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe('/api/v1/notes')
    expect(JSON.parse(String(init.body))).toEqual({
      target_type: 'asset',
      target_id: response.target_id,
      content: response.content
    })
  })
  it('requests archived Wiki pages explicitly for the archive view', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { ...wikiPage, archived: true }
    ]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await knowledgeApi.wikiPages(undefined, true)

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      '/api/v1/wiki/pages?include_archived=true'
    )
  })

})

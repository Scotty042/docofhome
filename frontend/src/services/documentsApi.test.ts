import { afterEach, describe, expect, it, vi } from 'vitest'

import { documentsApi, DocumentsApiError } from './documentsApi'

const listResponse = {
  path: 'Invoices',
  root_path: 'docofhome/Documents',
  root_exists: true,
  items: []
}

afterEach(() => vi.unstubAllGlobals())

describe('documents API', () => {
  it('encodes relative paths without exposing Nextcloud configuration', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(listResponse), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    await documentsApi.list('Invoices/Änderungen & Pläne')

    const url = String(fetchMock.mock.calls[0]?.[0])
    expect(url).toContain('/api/v1/documents?')
    expect(url).toContain('path=Invoices%2F%C3%84nderungen+%26+Pl%C3%A4ne')
    expect(url).not.toContain('nextcloud')
    expect(url).not.toContain('remote.php')
  })

  it('uploads the File body and only sets overwrite after explicit confirmation', async () => {
    const response = {
      item: {
        name: 'Manual.pdf',
        path: 'Manual.pdf',
        entry_type: 'file',
        size_bytes: 6,
        modified_at: null,
        content_type: 'application/pdf',
        etag: null
      },
      created: true,
      overwritten: false
    }
    const fetchMock = vi.fn().mockImplementation(async () => new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }))
    vi.stubGlobal('fetch', fetchMock)
    const file = new File([new Uint8Array([1, 2, 3])], 'Manual.pdf', {
      type: 'application/pdf'
    })

    await documentsApi.upload('', file, false)
    await documentsApi.upload('', file, true)

    const firstUrl = String(fetchMock.mock.calls[0]?.[0])
    const firstInit = fetchMock.mock.calls[0]?.[1] as RequestInit
    const secondUrl = String(fetchMock.mock.calls[1]?.[0])
    expect(firstUrl).toContain('filename=Manual.pdf')
    expect(firstUrl).not.toContain('overwrite=true')
    expect(firstInit.body).toBe(file)
    expect(firstInit.headers).toEqual(expect.objectContaining({ 'Content-Type': 'application/pdf' }))
    expect(secondUrl).toContain('overwrite=true')
  })

  it('downloads only through the local API and preserves bytes', async () => {
    const payload = new Blob(['manual'], { type: 'application/pdf' })
    const fetchMock = vi.fn().mockResolvedValue(new Response(payload, {
      status: 200,
      headers: { 'Content-Type': 'application/pdf' }
    }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await documentsApi.download('Invoices/Manual.pdf')

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      '/api/v1/documents/download?path=Invoices%2FManual.pdf'
    )
    expect(await result.text()).toBe('manual')
  })

  it('creates local download URLs and readable conflict errors', async () => {
    expect(documentsApi.downloadUrl('Invoices/Manual.pdf')).toBe(
      '/api/v1/documents/download?path=Invoices%2FManual.pdf'
    )
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: 'A document with this name already exists' }),
      { status: 409, headers: { 'Content-Type': 'application/json' } }
    )))

    await expect(documentsApi.createFolder('', 'Invoices')).rejects.toEqual(
      new DocumentsApiError('A document with this name already exists', 409)
    )
  })

  it('uses overwrite-safe MOVE and DELETE contracts', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        item: {
          name: 'Renamed.pdf',
          path: 'Renamed.pdf',
          entry_type: 'file',
          size_bytes: 1,
          modified_at: null,
          content_type: null,
          etag: null
        },
        created: false,
        overwritten: false
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await documentsApi.move({
      source_path: 'Manual.pdf',
      target_parent_path: '',
      name: 'Renamed.pdf'
    })
    await documentsApi.remove('Renamed.pdf')

    const move = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(move.method).toBe('POST')
    expect(JSON.parse(String(move.body))).toEqual({
      source_path: 'Manual.pdf',
      target_parent_path: '',
      name: 'Renamed.pdf'
    })
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('path=Renamed.pdf')
    expect((fetchMock.mock.calls[1]?.[1] as RequestInit).method).toBe('DELETE')
  })
})

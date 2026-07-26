import { afterEach, describe, expect, it, vi } from 'vitest'

import { aboutApi } from './aboutApi'

afterEach(() => vi.unstubAllGlobals())

describe('about API', () => {
  it('loads project information and sends only explicit feedback metadata', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        name: 'DocOfHome', slogan: 'Know your home.', version: '1.4.2',
        project_summary: 'Lokal', data_sovereignty: 'Privat',
        license_notice: 'AGPL-3.0', links: [], releases: [],
        feedback_available: true, feedback_unavailable_reason: null
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        accepted: true, message: 'Gesendet', reference: 'ref-1'
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    expect((await aboutApi.read()).version).toBe('1.4.2')
    await aboutApi.sendFeedback({
      category: 'error', subject: 'Ein Fehler', description: 'Ausführliche Beschreibung',
      current_page: '/about', include_technical_info: false, technical_info: null
    })

    const payload = JSON.parse(String((fetchMock.mock.calls[1]?.[1] as RequestInit).body))
    expect(payload.technical_info).toBeNull()
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('/about/feedback')
  })
})

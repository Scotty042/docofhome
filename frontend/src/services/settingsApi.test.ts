import { afterEach, describe, expect, it, vi } from 'vitest'

import { settingsApi } from './settingsApi'
import { createDefaultConfiguration } from '../types/settings'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('first-run defaults', () => {
  it('starts in dark mode with every integration disabled', () => {
    const configuration = createDefaultConfiguration()

    expect(configuration.theme).toBe('dark')
    expect(configuration.integrations).toHaveLength(4)
    expect(configuration.integrations.map((integration) => integration.kind)).toContain('fritzbox')
    expect(configuration.integrations.every((integration) => !integration.enabled)).toBe(true)
    expect(configuration.enabled_modules).toEqual(expect.arrayContaining(['images', 'documents', 'workloads']))
    expect(configuration.main_menu_modules).toEqual(expect.arrayContaining(['images', 'documents', 'workloads']))
  })
})

describe('settings API', () => {
  it('does not send an empty secret when preserving stored credentials', async () => {
    const configuration = createDefaultConfiguration()
    configuration.installation_name = 'Test House'
    configuration.integrations[0].enabled = true
    configuration.integrations[0].base_url = 'https://home-assistant.example.test'
    configuration.integrations[0].secret = ''

    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      ...configuration,
      setup_completed_at: '2026-07-20T12:00:00Z',
      integrations: configuration.integrations.map((integration) => ({
        kind: integration.kind,
        enabled: integration.enabled,
        base_url: integration.base_url,
        secret_configured: integration.kind === 'home_assistant'
      }))
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    await settingsApi.update(configuration)

    const request = fetchMock.mock.calls[0][1] as RequestInit
    const body = JSON.parse(request.body as string) as { integrations: Array<Record<string, unknown>> }
    expect(body.integrations[0]).not.toHaveProperty('secret')
  })

  it('uses the stored-credential connection test endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      kind: 'immich',
      success: true,
      message: 'Immich ist erreichbar.',
      service_version: '2.1.0',
      response_time_ms: 42
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await settingsApi.testIntegration('immich')

    expect(result.success).toBe(true)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/settings/integrations/immich/test',
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('persists an Immich album selection without applying it to other integrations', async () => {
    const configuration = createDefaultConfiguration()
    configuration.installation_name = 'Test House'
    configuration.integrations[1].selected_album_id = '00000000-0000-4000-8000-000000000001'
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      ...configuration,
      setup_completed_at: '2026-07-22T12:00:00Z'
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    await settingsApi.update(configuration)

    const request = fetchMock.mock.calls[0][1] as RequestInit
    const body = JSON.parse(request.body as string) as {
      integrations: Array<{ kind: string, selected_album_id: string | null }>
    }
    expect(body.integrations.find((item) => item.kind === 'immich')?.selected_album_id)
      .toBe('00000000-0000-4000-8000-000000000001')
    expect(body.integrations.find((item) => item.kind === 'home_assistant')?.selected_album_id)
      .toBeNull()
  })

  it('persists the Nextcloud document root only for Nextcloud', async () => {
    const configuration = createDefaultConfiguration()
    configuration.installation_name = 'Test House'
    configuration.integrations[2].document_root = ' Haus/Dokumente '
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      ...configuration,
      setup_completed_at: '2026-07-22T12:00:00Z'
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    await settingsApi.update(configuration)

    const request = fetchMock.mock.calls[0][1] as RequestInit
    const body = JSON.parse(request.body as string) as {
      integrations: Array<{ kind: string, document_root: string | null }>
    }
    expect(body.integrations.find((item) => item.kind === 'nextcloud')?.document_root)
      .toBe('Haus/Dokumente')
    expect(body.integrations.find((item) => item.kind === 'immich')?.document_root).toBeNull()
  })


  it('reads and rotates the MCP configuration through dedicated endpoints', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        enabled: false,
        permission: 'read',
        public_url: null,
        token_configured: false
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        token: 'doh_mcp_test-token',
        settings: {
          enabled: false,
          permission: 'read',
          public_url: null,
          token_configured: true
        }
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    const current = await settingsApi.readMcp()
    const rotated = await settingsApi.rotateMcpToken()

    expect(current.enabled).toBe(false)
    expect(rotated.token).toBe('doh_mcp_test-token')
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/v1/settings/mcp', expect.anything())
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/v1/settings/mcp/token', expect.objectContaining({ method: 'POST' }))
  })

  it('surfaces a readable API error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: 'Setup has already been completed' }),
      { status: 409, headers: { 'Content-Type': 'application/json' } }
    )))

    await expect(settingsApi.complete(createDefaultConfiguration()))
      .rejects.toThrow('Setup has already been completed')
  })
})

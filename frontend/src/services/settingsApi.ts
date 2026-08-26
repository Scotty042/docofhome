import type {
  ConfigurationRead,
  ConfigurationWrite,
  HealthRead,
  IntegrationKind,
  IntegrationTestResult,
  IntegrationWrite,
  McpSettingsRead,
  McpSettingsWrite,
  McpTokenCreated,
  SetupStatus
} from '../types/settings'
import { moduleKeys } from '../types/settings'

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    }
  })

  if (!response.ok) {
    let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg).filter(Boolean).join(', ') || message
      }
    } catch {
      // The fallback message remains useful when the server did not return JSON.
    }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

function serializable(configuration: ConfigurationWrite): ConfigurationWrite {
  return {
    ...configuration,
    enabled_modules: configuration.enabled_modules ?? [...moduleKeys],
    integrations: configuration.integrations.map((integration) => ({
      kind: integration.kind,
      enabled: integration.enabled,
      base_url: integration.base_url || null,
      account: integration.account?.trim() || null,
      selected_album_id: integration.kind === 'immich'
        ? integration.selected_album_id || null
        : null,
      document_root: integration.kind === 'nextcloud'
        ? integration.document_root?.trim() || 'docofhome/Documents'
        : null,
      ...(integration.secret?.trim() ? { secret: integration.secret.trim() } : {})
    }))
  }
}

export const settingsApi = {
  health: () => request<HealthRead>('/health'),
  setupStatus: () => request<SetupStatus>('/setup/status'),
  read: () => request<ConfigurationRead>('/settings'),
  complete: (configuration: ConfigurationWrite) => request<ConfigurationRead>(
    '/setup/complete',
    { method: 'POST', body: JSON.stringify(serializable(configuration)) }
  ),
  update: (configuration: ConfigurationWrite) => request<ConfigurationRead>(
    '/settings',
    { method: 'PUT', body: JSON.stringify(serializable(configuration)) }
  ),
  testIntegration: (kind: IntegrationKind) => request<IntegrationTestResult>(
    `/settings/integrations/${kind}/test`,
    { method: 'POST' }
  ),
  testIntegrationDraft: (integration: IntegrationWrite) => request<IntegrationTestResult>(
    '/settings/integrations/test',
    { method: 'POST', body: JSON.stringify(integration) }
  ),
  readMcp: () => request<McpSettingsRead>('/settings/mcp'),
  updateMcp: (configuration: McpSettingsWrite) => request<McpSettingsRead>(
    '/settings/mcp',
    { method: 'PUT', body: JSON.stringify(configuration) }
  ),
  rotateMcpToken: () => request<McpTokenCreated>(
    '/settings/mcp/token',
    { method: 'POST' }
  )
}

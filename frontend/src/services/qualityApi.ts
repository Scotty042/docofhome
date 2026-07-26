import type { QualityReport } from '../types/quality'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string }
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // Keep the HTTP fallback for non-JSON responses.
  }
  return `Anfrage fehlgeschlagen (HTTP ${response.status})`
}

async function request(path: string, init?: RequestInit): Promise<QualityReport> {
  const response = await fetch(`/api/v1/quality${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json() as Promise<QualityReport>
}

export const qualityApi = {
  latest: () => request('/latest'),
  run: () => request('/run', { method: 'POST' })
}

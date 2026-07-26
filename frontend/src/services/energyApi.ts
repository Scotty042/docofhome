import type {
  EnergyBalance,
  EnergyComponent,
  EnergyComponentWrite,
  EnergyConfiguration,
  EnergyConfigurationWrite
} from '../types/energy'

export class EnergyApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/energy${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    let message = `Energieanfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
      if (typeof body.detail === 'string') message = body.detail
      if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg).filter(Boolean).join(', ') || message
      }
    } catch {
      // Keep HTTP fallback.
    }
    throw new EnergyApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const energyApi = {
  configuration: () => request<EnergyConfiguration>('/configuration'),
  updateConfiguration: (payload: EnergyConfigurationWrite) => request<EnergyConfiguration>(
    '/configuration', { method: 'PUT', body: JSON.stringify(payload) }
  ),
  components: () => request<EnergyComponent[]>('/components'),
  createComponent: (payload: EnergyComponentWrite) => request<EnergyComponent>('/components', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateComponent: (id: string, payload: EnergyComponentWrite) => request<EnergyComponent>(
    `/components/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeComponent: (id: string) => request<void>(`/components/${id}`, { method: 'DELETE' }),
  balance: (months = 12) => request<EnergyBalance>(`/balance?months=${months}`)
}

import { afterEach, describe, expect, it, vi } from 'vitest'

import { electricalApi } from './electricalApi'
import {
  createEmptyElectricalCircuit,
  editableElectricalCircuit
} from '../types/electrical'
import type { ElectricalCircuit } from '../types/electrical'

function response(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

afterEach(() => vi.unstubAllGlobals())

describe('electrical circuit API', () => {
  it('serializes distribution, protective-device, search and pagination filters', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      items: [], total: 0, page: 2, page_size: 25, pages: 0
    }))
    vi.stubGlobal('fetch', fetchMock)

    await electricalApi.listCircuits({
      distribution_id: 'distribution-1',
      protective_device_id: 'device-1',
      search: 'Kitchen sockets',
      page: 2,
      page_size: 25
    })

    const url = String(fetchMock.mock.calls[0]?.[0])
    expect(url).toContain('/api/v1/electrical/circuits?')
    expect(url).toContain('distribution_id=distribution-1')
    expect(url).toContain('protective_device_id=device-1')
    expect(url).toContain('search=Kitchen+sockets')
    expect(url).toContain('page=2')
  })

  it('sends only explicit circuit documentation values', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ id: 'circuit-1' }, 201))
    vi.stubGlobal('fetch', fetchMock)
    const payload = createEmptyElectricalCircuit('distribution-1')
    payload.name = 'Kitchen'
    payload.circuit_number = 'F1'

    await electricalApi.createCircuit(payload)

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(JSON.parse(String(init.body))).toEqual({
      distribution_id: 'distribution-1',
      protective_device_id: null,
      name: 'Kitchen',
      circuit_number: 'F1',
      description: null,
      notes: null
    })
  })

  it('creates an editable copy without changing historical response metadata', () => {
    const circuit: ElectricalCircuit = {
      id: 'circuit-1',
      distribution_id: 'distribution-1',
      distribution_name: 'HV',
      protective_device_id: 'device-1',
      protective_device_name: 'Breaker',
      protective_device_code: 'MCB-001',
      name: 'Kitchen',
      circuit_number: 'F1',
      description: null,
      notes: 'Documented',
      created_at: '2026-07-22T08:00:00Z',
      updated_at: '2026-07-22T08:00:00Z',
      deleted_at: null
    }

    expect(editableElectricalCircuit(circuit)).toEqual({
      distribution_id: 'distribution-1',
      protective_device_id: 'device-1',
      name: 'Kitchen',
      circuit_number: 'F1',
      description: null,
      notes: 'Documented'
    })
  })
})

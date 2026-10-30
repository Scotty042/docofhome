import { describe, expect, it } from 'vitest'
import { inventoryReturnTo, readInventoryQuery, writeInventoryQuery } from './inventoryNavigation'

describe('inventory navigation state', () => {
  it('restores all filters, pagination and sorting after a detail visit', () => {
    const query = { q: 'Backofen', status: 'active', type: '11111111-1111-4111-8111-111111111111', location: '22222222-2222-4222-8222-222222222222', label: '33333333-3333-4333-8333-333333333333', sort: 'updated_at:desc', page: '3', size: '25', archived: '1' }
    expect(writeInventoryQuery(readInventoryQuery(query))).toEqual(query)
  })
  it('rejects malformed query values before they reach UUID and pagination endpoints', () => {
    expect(readInventoryQuery({ q: ['bad'], type: 'not-a-uuid', status: 'deleted', page: '-2', size: '100000', sort: 'sql:desc' }))
      .toMatchObject({ search: '', assetTypeId: '', status: '', page: 1, pageSize: 10, sort: 'name:asc' })
    expect(readInventoryQuery({ page: 'Infinity' }).page).toBe(1)
    expect(writeInventoryQuery(readInventoryQuery({}))).toEqual({})
  })
  it('accepts only a local inventory return path, even for a tampered detail link', () => {
    expect(inventoryReturnTo('/assets?q=Backofen&page=3')).toBe('/assets?q=Backofen&page=3')
    for (const bad of ['https://example.com', '//example.com', '/settings', '/assets-other', '/assets?x=\\evil', '/assets?x=\n']) expect(inventoryReturnTo(bad)).toBe('/assets')
  })
})

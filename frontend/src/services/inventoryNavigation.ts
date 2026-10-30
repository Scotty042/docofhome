import type { AssetStatus } from '../types/assets'

export interface InventoryState {
  search: string; status: AssetStatus | ''; assetTypeId: string; locationId: string; labelId: string
  sort: string; page: number; pageSize: number; showArchived: boolean
}
const sorts = ['name:asc', 'name:desc', 'created_at:desc', 'updated_at:desc']
const statuses = ['active', 'inactive', 'maintenance', 'retired']
const text = (value: unknown) => typeof value === 'string' ? value : ''
const uuid = (value: unknown) => /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(text(value)) ? text(value) : ''
export function readInventoryQuery(query: Record<string, unknown>): InventoryState {
  const page = Number(text(query.page))
  const size = Number(text(query.size))
  return {
    search: text(query.q).slice(0, 200),
    status: statuses.includes(text(query.status)) ? text(query.status) as AssetStatus : '',
    assetTypeId: uuid(query.type), locationId: uuid(query.location), labelId: uuid(query.label),
    sort: sorts.includes(text(query.sort)) ? text(query.sort) : 'name:asc',
    page: Number.isSafeInteger(page) && page >= 1 && page <= 1000000 ? page : 1,
    pageSize: [10, 25, 50].includes(size) ? size : 10,
    showArchived: query.archived === '1'
  }
}
export function writeInventoryQuery(state: InventoryState): Record<string, string> {
  const result: Record<string, string> = {}
  const search = state.search?.trim() || ''
  if (search) result.q = search
  if (state.status) result.status = state.status
  if (state.assetTypeId) result.type = state.assetTypeId
  if (state.locationId) result.location = state.locationId
  if (state.labelId) result.label = state.labelId
  if (state.sort !== 'name:asc') result.sort = state.sort
  if (state.page !== 1) result.page = String(state.page)
  if (state.pageSize !== 10) result.size = String(state.pageSize)
  if (state.showArchived) result.archived = '1'
  return result
}
export function inventoryReturnTo(value: unknown): string {
  if (typeof value !== 'string' || /[\\\u0000-\u001f\u007f]/u.test(value)) return '/assets'
  return value === '/assets' || value.startsWith('/assets?') ? value : '/assets'
}

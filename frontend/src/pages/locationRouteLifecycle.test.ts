import { nextTick, ref, watch } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import { useLocationDetailData } from '../composables/useLocationDetailData'
import { useLocationEditorData } from '../composables/useLocationEditorData'
import type { Asset, Page } from '../types/assets'
import type { Location, LocationTreeNode } from '../types/locations'

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((accept) => { resolve = accept })
  return { promise, resolve }
}

function location(id: string, name: string): Location {
  return {
    id,
    name,
    location_type: 'room',
    path: `House / ${name}`,
    breadcrumbs: [
      { id: 'root', name: 'House', location_type: 'building' },
      { id, name, location_type: 'room' }
    ],
    parent_id: 'root',
    short_name: null,
    sort_order: null,
    description: null,
    notes: null,
    direct_asset_count: 1,
    descendant_asset_count: 0,
    deleted_at: null,
    created_at: '2026-07-20T12:00:00Z',
    updated_at: '2026-07-20T12:00:00Z'
  }
}

function asset(id: string, name: string, locationId: string): Asset {
  return {
    id,
    name,
    jarvis_code: id.toUpperCase(),
    description: null,
    asset_type_id: 'type-id',
    product_id: null,
    location_id: locationId,
    serial_number: null,
    inventory_number: null,
    module_width: null,
    effective_module_width: null,
    breaker_characteristic: null,
    effective_breaker_characteristic: null,
    rated_current_a: null,
    effective_rated_current_a: null,
    coil_voltage_v: null,
    effective_coil_voltage_v: null,
    coil_voltage_type: null,
    effective_coil_voltage_type: null,
    contact_count: null,
    effective_contact_count: null,
    contact_type: null,
    effective_contact_type: null,
    status: 'active',
    asset_type: { id: 'type-id', name: 'Device' },
    product: null,
    location: { id: locationId, name: `Location ${locationId}` },
    labels: [],
    deleted_at: null,
    created_at: '2026-07-20T12:00:00Z',
    updated_at: '2026-07-20T12:00:00Z'
  }
}

function assetPage(items: Asset[], page: number, total = items.length): Page<Asset> {
  return { items, total, page, page_size: 25, pages: Math.ceil(total / 25) }
}

function tree(): LocationTreeNode[] {
  return [{
    ...location('root', 'House'),
    location_type: 'building',
    parent_id: null,
    path: 'House',
    breadcrumbs: [{ id: 'root', name: 'House', location_type: 'building' }],
    children: []
  }]
}

describe('location route lifecycle', () => {
  it('shows location B and page-one assets after navigating from A in the same detail instance', async () => {
    const routeId = ref('A')
    const delayedAThirdPage = deferred<Page<Asset>>()
    const delayedLocationB = deferred<Location>()
    const getLocation = vi.fn((id: string) => (
      id === 'A' ? Promise.resolve(location('A', 'Location A')) : delayedLocationB.promise
    ))
    const getAssets = vi.fn((id: string, page: number) => {
      if (id === 'A' && page === 1) {
        return Promise.resolve(assetPage([asset('asset-a', 'Asset A', 'A')], 1, 75))
      }
      if (id === 'A' && page === 3) return delayedAThirdPage.promise
      return Promise.resolve(assetPage([asset('asset-b', 'Asset B', 'B')], 1))
    })
    const state = useLocationDetailData({ getLocation, getAssets })
    const stop = watch(routeId, (id) => void state.loadLocation(id), { immediate: true })

    await vi.waitFor(() => expect(state.assets.value[0]?.name).toBe('Asset A'))
    state.assetPage.value = 3
    state.error.value = 'Old location error'
    state.assetError.value = 'Old asset error'
    void state.loadAssets()
    await vi.waitFor(() => expect(getAssets).toHaveBeenCalledWith('A', 3, 25))

    routeId.value = 'B'
    await nextTick()
    expect(state.location.value).toBeNull()
    expect(state.assets.value).toEqual([])
    expect(state.assetPage.value).toBe(1)
    expect(state.error.value).toBeNull()
    expect(state.assetError.value).toBeNull()

    delayedLocationB.resolve(location('B', 'Location B'))
    await vi.waitFor(() => expect(state.assets.value[0]?.name).toBe('Asset B'))
    delayedAThirdPage.resolve(assetPage([asset('stale-a', 'Stale Asset A', 'A')], 3, 75))
    await nextTick()
    await Promise.resolve()

    expect(state.location.value?.name).toBe('Location B')
    expect(state.assets.value.map((entry) => entry.name)).toEqual(['Asset B'])
    expect(state.assetPage.value).toBe(1)
    expect(getAssets).toHaveBeenCalledWith('B', 1, 25)
    stop()
  })

  it('keeps location B in the editor when edit route A completes late', async () => {
    const routeId = ref<string | null>('A')
    const requestedParent = ref<string | null>(null)
    const delayedLocationA = deferred<Location>()
    const delayedLocationB = deferred<Location>()
    const getLocation = vi.fn((id: string) => (
      id === 'A' ? delayedLocationA.promise : delayedLocationB.promise
    ))
    const state = useLocationEditorData({
      getTree: () => Promise.resolve(tree()),
      getLocation
    })
    const stop = watch(
      [routeId, requestedParent],
      ([id, parent]) => void state.loadEditor(id, parent),
      { immediate: true }
    )

    await vi.waitFor(() => expect(getLocation).toHaveBeenCalledWith('A'))
    routeId.value = 'B'
    await nextTick()
    expect(state.form.value.name).toBe('')
    expect(state.locations.value).toEqual([])
    expect(state.error.value).toBeNull()

    delayedLocationB.resolve(location('B', 'Location B'))
    await vi.waitFor(() => expect(state.form.value.name).toBe('Location B'))
    delayedLocationA.resolve(location('A', 'Location A'))
    await nextTick()
    await Promise.resolve()

    expect(state.form.value.name).toBe('Location B')
    expect(state.loading.value).toBe(false)
    stop()
  })
})

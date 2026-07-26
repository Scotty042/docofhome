import { nextTick, ref, watch } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import {
  useElectricalDistributionDetail,
  useElectricalDistributionEditor,
  useElectricalProtectiveDeviceEditor
} from '../composables/useElectricalData'
import type {
  DistributionDetail,
  DistributionTreeNode,
  ProtectiveDevice
} from '../types/electrical'

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((accept) => { resolve = accept })
  return { promise, resolve }
}

function distribution(id: string): DistributionDetail {
  return {
    id,
    asset_id: `asset-${id}`,
    role: 'distribution',
    created_at: '2026-07-21T12:00:00Z',
    updated_at: '2026-07-21T12:00:00Z',
    deleted_at: null,
    asset: {
      id: `asset-${id}`,
      name: `Asset ${id}`,
      jarvis_code: id.toUpperCase(),
      location_id: 'room',
      location_path: 'House / Electrical room',
      status: 'active',
      effective_module_width: null
    },
    parent_distribution_id: null,
    distribution_type: 'main',
    layout_mode: 'rows',
    designation: `Distribution ${id}`,
    display_name: `Distribution ${id}`,
    rows: null,
    modules_per_row: null,
    description: null,
    notes: null,
    breadcrumbs: [],
    direct_subdistribution_count: 0,
    direct_protective_device_count: 0,
    protective_devices: []
  }
}

function tree(): DistributionTreeNode[] {
  const root = distribution('root')
  return [{ ...root, children: [] }]
}

function device(id: string): ProtectiveDevice {
  return {
    id,
    asset_id: `asset-${id}`,
    role: 'protective_device',
    created_at: '2026-07-21T12:00:00Z',
    updated_at: '2026-07-21T12:00:00Z',
    deleted_at: null,
    asset: {
      id: `asset-${id}`,
      name: `Device ${id}`,
      jarvis_code: id.toUpperCase(),
      location_id: 'room',
      location_path: 'House / Electrical room',
      status: 'active',
      effective_module_width: null
    },
    distribution_id: 'root',
    distribution_name: 'Distribution root',
    area_id: null,
    area_name: null,
    device_type: 'mcb',
    row_number: null,
    start_position: null,
    module_width: null,
    rated_current_a: null,
    residual_current_ma: null,
    characteristic: null,
    poles: null,
    breaking_capacity_ka: null,
    rcd_type: null,
    fuse_type: null,
    spd_type: null,
    assigned_rcd_id: null,
    assigned_rcd_name: null,
    neutral_rail_id: null,
    neutral_rail_name: null,
    effective_rcd_id: null,
    effective_rcd_name: null,
    effective_neutral_rail_id: null,
    effective_neutral_rail_name: null,
    busbar_component_id: null,
    busbar_component_name: null,
    calculated_phases: [],
    group_warnings: [],
    description: null,
    notes: null
  }
}

const editorBase = {
  getTree: () => Promise.resolve(tree()),
  getAssets: () => Promise.resolve([])
}

describe('electrical route lifecycle', () => {
  it('keeps distribution B when delayed detail A resolves in the same component instance', async () => {
    const routeId = ref('A')
    const delayedA = deferred<DistributionDetail>()
    const delayedB = deferred<DistributionDetail>()
    const state = useElectricalDistributionDetail({
      getDistribution: (id) => id === 'A' ? delayedA.promise : delayedB.promise
    })
    const stop = watch(routeId, (id) => void state.loadDistribution(id), { immediate: true })

    await nextTick()
    routeId.value = 'B'
    await nextTick()
    expect(state.distribution.value).toBeNull()
    expect(state.error.value).toBeNull()

    delayedB.resolve(distribution('B'))
    await vi.waitFor(() => expect(state.distribution.value?.id).toBe('B'))
    delayedA.resolve(distribution('A'))
    await nextTick()
    await Promise.resolve()

    expect(state.distribution.value?.id).toBe('B')
    expect(state.loading.value).toBe(false)
    stop()
  })

  it('keeps distribution B when edit route A completes late', async () => {
    const routeId = ref<string | null>('A')
    const delayedA = deferred<DistributionDetail>()
    const delayedB = deferred<DistributionDetail>()
    const state = useElectricalDistributionEditor({
      ...editorBase,
      getDistribution: (id) => id === 'A' ? delayedA.promise : delayedB.promise,
      getDevice: (id) => Promise.resolve(device(id))
    })
    const stop = watch(routeId, (id) => void state.loadEditor(id, null), { immediate: true })

    await nextTick()
    routeId.value = 'B'
    await nextTick()
    expect(state.form.value.asset_id).toBe('')
    expect(state.tree.value).toEqual([])

    delayedB.resolve(distribution('B'))
    await vi.waitFor(() => expect(state.form.value.asset_id).toBe('asset-B'))
    delayedA.resolve(distribution('A'))
    await nextTick()
    await Promise.resolve()

    expect(state.form.value.asset_id).toBe('asset-B')
    expect(state.form.value.designation).toBe('Distribution B')
    stop()
  })

  it('keeps protective device B when edit route A completes late', async () => {
    const routeId = ref<string | null>('A')
    const delayedA = deferred<ProtectiveDevice>()
    const delayedB = deferred<ProtectiveDevice>()
    const state = useElectricalProtectiveDeviceEditor({
      ...editorBase,
      getDistribution: (id) => Promise.resolve(distribution(id)),
      getDevice: (id) => id === 'A' ? delayedA.promise : delayedB.promise
    })
    const stop = watch(routeId, (id) => void state.loadEditor(id, null), { immediate: true })

    await nextTick()
    routeId.value = 'B'
    await nextTick()
    expect(state.form.value.asset_id).toBe('')
    expect(state.error.value).toBeNull()

    delayedB.resolve(device('B'))
    await vi.waitFor(() => expect(state.form.value.asset_id).toBe('asset-B'))
    delayedA.resolve(device('A'))
    await nextTick()
    await Promise.resolve()

    expect(state.form.value.asset_id).toBe('asset-B')
    expect(state.loading.value).toBe(false)
    stop()
  })
})

import { ref } from 'vue'

import {
  ElectricalApiError,
  electricalApi,
  loadAllAvailableAssets
} from '../services/electricalApi'
import {
  createEmptyDistribution,
  createEmptyProtectiveDevice,
  editableDistribution,
  editableProtectiveDevice,
  type AvailableElectricalAsset,
  type DistributionDetail,
  type DistributionTreeNode,
  type ElectricalRole,
  type ProtectiveDevice
} from '../types/electrical'

interface DetailDependencies {
  getDistribution: (id: string) => Promise<DistributionDetail>
}

export function useElectricalDistributionDetail(
  dependencies: DetailDependencies = {
    getDistribution: (id) => electricalApi.getDistribution(id, true)
  }
) {
  const distribution = ref<DistributionDetail | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)
  const errorStatus = ref<number | null>(null)
  let requestId = 0

  async function loadDistribution(id: string) {
    const currentRequest = ++requestId
    distribution.value = null
    error.value = null
    errorStatus.value = null
    loading.value = true
    try {
      const result = await dependencies.getDistribution(id)
      if (currentRequest !== requestId) return
      distribution.value = result
    } catch (reason) {
      if (currentRequest !== requestId) return
      error.value = reason instanceof Error
        ? reason.message
        : 'Verteilung konnte nicht geladen werden.'
      errorStatus.value = reason instanceof ElectricalApiError ? reason.status : 0
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  return { distribution, loading, error, errorStatus, loadDistribution }
}

interface EditorDependencies {
  getTree: () => Promise<DistributionTreeNode[]>
  getDistribution: (id: string) => Promise<DistributionDetail>
  getDevice: (id: string) => Promise<ProtectiveDevice>
  getAssets: (
    role: ElectricalRole,
    currentComponentId?: string,
    search?: string
  ) => Promise<AvailableElectricalAsset[]>
}

const editorDependencies: EditorDependencies = {
  getTree: () => electricalApi.distributionTree(),
  getDistribution: (id) => electricalApi.getDistribution(id, true),
  getDevice: (id) => electricalApi.getProtectiveDevice(id, true),
  getAssets: loadAllAvailableAssets
}

function currentAssetOption(
  current: DistributionDetail | ProtectiveDevice
): AvailableElectricalAsset {
  return {
    id: current.asset.id,
    name: current.asset.name,
    jarvis_code: current.asset.jarvis_code,
    location_id: current.asset.location_id,
    location_path: current.asset.location_path,
    effective_module_width: current.asset.effective_module_width
  }
}

export function useElectricalDistributionEditor(
  dependencies: EditorDependencies = editorDependencies
) {
  const form = ref(createEmptyDistribution())
  const tree = ref<DistributionTreeNode[]>([])
  const assets = ref<AvailableElectricalAsset[]>([])
  const loading = ref(true)
  const assetsLoading = ref(false)
  const error = ref<string | null>(null)
  let loadRequestId = 0
  let assetRequestId = 0
  let currentId: string | null = null

  async function loadEditor(id: string | null, parentId: string | null) {
    const requestId = ++loadRequestId
    assetRequestId += 1
    currentId = id
    form.value = createEmptyDistribution(parentId)
    tree.value = []
    assets.value = []
    loading.value = true
    assetsLoading.value = false
    error.value = null
    try {
      const [loadedTree, current, available] = await Promise.all([
        dependencies.getTree(),
        id ? dependencies.getDistribution(id) : Promise.resolve(null),
        id ? Promise.resolve([]) : dependencies.getAssets('distribution')
      ])
      if (requestId !== loadRequestId) return
      if (current?.deleted_at) throw new Error('Archivierte Verteilungen können nicht bearbeitet werden.')
      tree.value = loadedTree
      assets.value = current ? [currentAssetOption(current)] : available
      form.value = current ? editableDistribution(current) : createEmptyDistribution(parentId)
    } catch (reason) {
      if (requestId !== loadRequestId) return
      error.value = reason instanceof Error
        ? reason.message
        : 'Verteilungseditor konnte nicht geladen werden.'
    } finally {
      if (requestId === loadRequestId) loading.value = false
    }
  }

  async function searchAssets(search: string) {
    if (currentId) return
    const requestId = ++assetRequestId
    assetsLoading.value = true
    try {
      const available = await dependencies.getAssets('distribution', undefined, search)
      if (requestId !== assetRequestId) return
      assets.value = available
    } catch (reason) {
      if (requestId !== assetRequestId) return
      error.value = reason instanceof Error ? reason.message : 'Assets konnten nicht geladen werden.'
    } finally {
      if (requestId === assetRequestId) assetsLoading.value = false
    }
  }

  return { form, tree, assets, loading, assetsLoading, error, loadEditor, searchAssets }
}

export function useElectricalProtectiveDeviceEditor(
  dependencies: EditorDependencies = editorDependencies
) {
  const form = ref(createEmptyProtectiveDevice())
  const tree = ref<DistributionTreeNode[]>([])
  const assets = ref<AvailableElectricalAsset[]>([])
  const loading = ref(true)
  const assetsLoading = ref(false)
  const error = ref<string | null>(null)
  let loadRequestId = 0
  let assetRequestId = 0
  let currentId: string | null = null

  async function loadEditor(id: string | null, distributionId: string | null) {
    const requestId = ++loadRequestId
    assetRequestId += 1
    currentId = id
    form.value = createEmptyProtectiveDevice(distributionId ?? '')
    tree.value = []
    assets.value = []
    loading.value = true
    assetsLoading.value = false
    error.value = null
    try {
      const [loadedTree, current, available] = await Promise.all([
        dependencies.getTree(),
        id ? dependencies.getDevice(id) : Promise.resolve(null),
        id ? Promise.resolve([]) : dependencies.getAssets('protective_device')
      ])
      if (requestId !== loadRequestId) return
      if (current?.deleted_at) throw new Error('Archivierte Schutzgeräte können nicht bearbeitet werden.')
      tree.value = loadedTree
      assets.value = current ? [currentAssetOption(current)] : available
      form.value = current
        ? editableProtectiveDevice(current)
        : createEmptyProtectiveDevice(distributionId ?? '')
    } catch (reason) {
      if (requestId !== loadRequestId) return
      error.value = reason instanceof Error
        ? reason.message
        : 'Schutzgeräteeditor konnte nicht geladen werden.'
    } finally {
      if (requestId === loadRequestId) loading.value = false
    }
  }

  async function searchAssets(search: string) {
    if (currentId) return
    const requestId = ++assetRequestId
    assetsLoading.value = true
    try {
      const available = await dependencies.getAssets('protective_device', undefined, search)
      if (requestId !== assetRequestId) return
      assets.value = available
    } catch (reason) {
      if (requestId !== assetRequestId) return
      error.value = reason instanceof Error ? reason.message : 'Assets konnten nicht geladen werden.'
    } finally {
      if (requestId === assetRequestId) assetsLoading.value = false
    }
  }

  return { form, tree, assets, loading, assetsLoading, error, loadEditor, searchAssets }
}

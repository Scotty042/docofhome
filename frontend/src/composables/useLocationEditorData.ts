import { ref } from 'vue'

import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationPresentation'
import {
  createEmptyLocation,
  editableLocation,
  type Location,
  type LocationTreeNode
} from '../types/locations'

interface LocationEditorDependencies {
  getTree: () => Promise<LocationTreeNode[]>
  getLocation: (id: string) => Promise<Location>
}

const defaultDependencies: LocationEditorDependencies = {
  getTree: () => locationApi.tree(),
  getLocation: (id) => locationApi.get(id, true)
}

export function useLocationEditorData(
  dependencies: LocationEditorDependencies = defaultDependencies
) {
  const form = ref(createEmptyLocation())
  const locations = ref<Location[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  let loadRequestId = 0

  async function loadEditor(id: string | null, requestedParent: string | null) {
    const requestId = ++loadRequestId
    loading.value = true
    error.value = null
    locations.value = []
    form.value = createEmptyLocation()
    try {
      const [tree, current] = await Promise.all([
        dependencies.getTree(),
        id ? dependencies.getLocation(id) : Promise.resolve(null)
      ])
      if (requestId !== loadRequestId) return
      const loadedLocations = flattenLocationTree(tree).map((entry) => entry.location)
      locations.value = loadedLocations
      if (current) {
        if (current.deleted_at) throw new Error('Archivierte Standorte können nicht bearbeitet werden.')
        form.value = editableLocation(current)
      } else {
        const root = loadedLocations.find((location) => location.location_type === 'building')
        form.value = createEmptyLocation(requestedParent ?? root?.id ?? null)
      }
    } catch (reason) {
      if (requestId !== loadRequestId) return
      error.value = reason instanceof Error ? reason.message : 'Standorteditor konnte nicht geladen werden.'
    } finally {
      if (requestId === loadRequestId) loading.value = false
    }
  }

  return { form, locations, loading, error, loadEditor }
}

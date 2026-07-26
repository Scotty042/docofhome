import type { Location, LocationTreeNode, LocationType } from '../types/locations'
import { flattenLocationTree as flattenSortedLocationTree } from './locationOptions'

export const locationTypeItems: Array<{ title: string, value: LocationType }> = [
  { title: 'Gebäude', value: 'building' },
  { title: 'Etage', value: 'floor' },
  { title: 'Raum', value: 'room' },
  { title: 'Bereich', value: 'area' },
  { title: 'Schrank', value: 'cabinet' },
  { title: 'Installationspunkt', value: 'installation_point' },
  { title: 'Außenbereich', value: 'outdoor' }
]

const labels = Object.fromEntries(locationTypeItems.map((item) => [item.value, item.title])) as (
  Record<LocationType, string>
)

const icons: Record<LocationType, string> = {
  building: 'mdi-home',
  floor: 'mdi-layers-triple',
  room: 'mdi-door',
  area: 'mdi-shape-outline',
  cabinet: 'mdi-cupboard-outline',
  installation_point: 'mdi-map-marker-radius-outline',
  outdoor: 'mdi-tree-outline'
}

export function locationTypeLabel(type: LocationType): string {
  return labels[type]
}

export function locationTypeIcon(type: LocationType): string {
  return icons[type]
}

export function filterLocationTree(
  nodes: LocationTreeNode[],
  search: string,
  type: LocationType | ''
): LocationTreeNode[] {
  const normalized = search.trim().toLocaleLowerCase()
  return nodes.flatMap((node) => {
    const children = filterLocationTree(node.children, search, type)
    const matchesSearch = !normalized || node.name.toLocaleLowerCase().includes(normalized)
      || node.path.toLocaleLowerCase().includes(normalized)
    const matchesType = !type || node.location_type === type
    if ((matchesSearch && matchesType) || children.length > 0) return [{ ...node, children }]
    return []
  })
}

export interface FlatLocation {
  location: LocationTreeNode
  depth: number
}

export function flattenLocationTree(nodes: LocationTreeNode[], depth = 0): FlatLocation[] {
  return nodes.flatMap((node) => [
    { location: node, depth },
    ...flattenLocationTree(node.children, depth + 1)
  ])
}

export function eligibleParentLocations(
  locations: Location[],
  currentId: string | null
): Location[] {
  const byId = new Map(locations.map((location) => [location.id, location]))
  const children = new Map<string | null, LocationTreeNode[]>()
  for (const location of locations) {
    const node = { ...location, children: [] } as LocationTreeNode
    const key = location.parent_id && byId.has(location.parent_id) ? location.parent_id : null
    children.set(key, [...(children.get(key) ?? []), node])
  }
  const attach = (node: LocationTreeNode): LocationTreeNode => ({
    ...node,
    children: (children.get(node.id) ?? []).map(attach)
  })
  return flattenSortedLocationTree((children.get(null) ?? []).map(attach))
    .filter((location) => (
      location.deleted_at === null
      && location.id !== currentId
      && (!currentId || !location.breadcrumbs.some((entry) => entry.id === currentId))
    ))
}
